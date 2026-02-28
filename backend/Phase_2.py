# gmail_service.py
# Drop this into your mailmind/emails/ folder
# ══════════════════════════════════════════════════════

import os
import base64
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pymongo import MongoClient

# ── MongoDB ────────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017/")
db = client["mailmind"]
emails_collection = db["emails"]



# ══════════════════════════════════════════════════════
# STEP 1 — Build Gmail service from user token
# ══════════════════════════════════════════════════════
def get_gmail_service(user_token: dict):
    """
    user_token = OAuth token dict saved in MongoDB at login
    Returns a ready-to-use Gmail API service
    """
    creds = Credentials(
        token=user_token["access_token"],
        refresh_token=user_token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    )
    return build("gmail", "v1", credentials=creds)


# ══════════════════════════════════════════════════════
# STEP 2 — Fetch last 50 emails from inbox
# ══════════════════════════════════════════════════════
def fetch_emails(user_token: dict, max_results: int = 50) -> list:
    """
    Fetches last N emails from Gmail inbox.
    Returns a list of cleaned email dicts.
    """
    service = get_gmail_service(user_token)
    emails  = []

    try:
        # Get list of message IDs from inbox only
        result = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            labelIds=["INBOX"]
        ).execute()

        messages = result.get("messages", [])
        print(f"[Gmail] Found {len(messages)} emails")

        for msg in messages:
            email_data = fetch_single_email(service, msg["id"])
            if email_data:
                emails.append(email_data)

    except HttpError as e:
        print(f"[Gmail Error] {e}")

    return emails


# ══════════════════════════════════════════════════════
# STEP 3 — Parse a single email
# ══════════════════════════════════════════════════════
def fetch_single_email(service, message_id: str) -> dict:
    """
    Fetches one email by ID.
    Extracts: subject, sender, date, plain text body.
    """
    try:
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        headers = msg["payload"].get("headers", [])
        subject = sender = date = ""

        for h in headers:
            name = h["name"].lower()
            if name == "subject":
                subject = h["value"]
            elif name == "from":
                sender = h["value"]
            elif name == "date":
                date = h["value"]

        body = extract_body(msg["payload"])

        return {
            "gmail_id":   message_id,
            "subject":    subject,
            "sender":     sender,
            "date":       date,
            "body":       body[:2000],      # cap at 2000 chars — enough for classifier
            "snippet":    msg.get("snippet", ""),
            "fetched_at": datetime.utcnow().isoformat(),
        }

    except HttpError as e:
        print(f"[Gmail Error] {message_id}: {e}")
        return None


# ══════════════════════════════════════════════════════
# HELPER — Extract plain text from email payload
# ══════════════════════════════════════════════════════
def extract_body(payload: dict) -> str:
    """
    Gmail emails can be simple or multipart.
    Always tries to get plain text first, falls back to HTML.
    """
    body = ""

    # Simple email — body directly in payload
    if "body" in payload and payload["body"].get("data"):
        body = _decode(payload["body"]["data"])

    # Multipart — body split into parts
    elif "parts" in payload:
        for part in payload["parts"]:
            mime = part.get("mimeType", "")

            if mime == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = _decode(data)
                    break

            elif mime == "text/html" and not body:
                data = part.get("body", {}).get("data", "")
                if data:
                    body = _decode(data)

            # Nested multipart
            elif "parts" in part:
                for sub in part["parts"]:
                    if sub.get("mimeType") == "text/plain":
                        data = sub.get("body", {}).get("data", "")
                        if data:
                            body = _decode(data)
                            break

    return body.strip()


def _decode(data: str) -> str:
    """Gmail uses base64url encoding — decode it to readable text"""
    try:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
    except Exception:
        return ""


# ══════════════════════════════════════════════════════
# STEP 4 — Store emails in MongoDB
# ══════════════════════════════════════════════════════
def store_emails(user_id: str, emails: list) -> int:
    """
    Saves fetched emails to MongoDB.
    Skips duplicates using gmail_id — safe to call on every refresh.
    Returns count of newly saved emails.
    """
    saved = 0
    for email in emails:

        # Skip if already stored
        existing = emails_collection.find_one({
            "user_id":  user_id,
            "gmail_id": email["gmail_id"]
        })

        if not existing:
            emails_collection.insert_one({
                "user_id": user_id,
                **email,

                # Classifier fills these in Phase 4
                "classified": False,
                "class":      None,
                "importance": None,
                "urgency":    None,
                "quadrant":   None,
                "colour":     None,
                "action":     None,
                "summary":    None,
                "event_date": None,
            })
            saved += 1

    print(f"[MongoDB] {saved} new emails saved for {user_id}")
    return saved


# ══════════════════════════════════════════════════════
# MAIN PIPELINE — call this after user logs in
# ══════════════════════════════════════════════════════
def run_email_pipeline(user_id: str, user_token: dict) -> int:
    """
    Full Phase 2 in one call:
    1. Fetch 50 emails from Gmail
    2. Store unclassified in MongoDB
    3. Return count of new emails saved

    How to use in views.py:
        from emails.gmail_service import run_email_pipeline
        count = run_email_pipeline(user_id, user_token)
    """
    print(f"[Pipeline] Fetching emails for {user_id}")
    emails = fetch_emails(user_token, max_results=50)
    saved  = store_emails(user_id, emails)
    print(f"[Pipeline] Done — {saved} new emails stored")
    return saved


# ══════════════════════════════════════════════════════
# QUERIES — used by Phase 4 classifier + dashboard
# ══════════════════════════════════════════════════════
def get_unclassified_emails(user_id: str) -> list:
    """Returns emails not yet classified — fed into gemini_service.py"""
    return list(emails_collection.find({
        "user_id":    user_id,
        "classified": False
    }))


def get_all_emails(user_id: str) -> list:
    """Returns all emails for dashboard — newest first"""
    return list(emails_collection.find(
        {"user_id": user_id},
        {"_id": 0}          # hide MongoDB internal _id
    ).sort("date", -1))


def get_emails_by_quadrant(user_id: str, quadrant: str) -> list:
    """
    Returns emails filtered by quadrant.
    quadrant = "Q1" / "Q2" / "Q3" / "Q4"
    Used by the Priority Matrix view on frontend.
    """
    return list(emails_collection.find(
        {"user_id": user_id, "quadrant": quadrant},
        {"_id": 0}
    ).sort("date", -1))


def get_emails_by_class(user_id: str, club_class: str) -> list:
    """
    Returns emails for a specific club/class.
    e.g. get_emails_by_class(user_id, "RAID")
    Used by the search layer.
    """
    return list(emails_collection.find(
        {"user_id": user_id, "class": club_class},
        {"_id": 0}
    ).sort("date", -1))


def search_emails(user_id: str, query: str) -> list:
    """
    Simple keyword search across subject + summary.
    Used by the search bar on the For You Page.
    """
    return list(emails_collection.find(
        {
            "user_id": user_id,
            "$or": [
                {"subject": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"class":   {"$regex": query, "$options": "i"}},
            ]
        },
        {"_id": 0}
    ).sort("date", -1))