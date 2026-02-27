# emails/models.py
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import os

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client    = MongoClient(MONGO_URI)
db        = client['mailmind']

users_col         = db['users']
emails_col        = db['emails']
preferences_col   = db['preferences']
notifications_col = db['notifications']


# ── USERS ─────────────────────────────────────────────
def create_user(google_id, email, name, roll_no, picture, token_dict):
    existing = users_col.find_one({"google_id": google_id})
    if existing:
        users_col.update_one(
            {"google_id": google_id},
            {"$set": {"token": token_dict, "last_login": datetime.utcnow().isoformat()}}
        )
        return str(existing['_id'])
    result = users_col.insert_one({
        "google_id":  google_id,
        "email":      email,
        "name":       name,
        "roll_no":    roll_no,
        "picture":    picture,
        "token":      token_dict,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": datetime.utcnow().isoformat(),
    })
    return str(result.inserted_id)


def get_user(google_id):
    return users_col.find_one({"google_id": google_id})


# ── PREFERENCES ───────────────────────────────────────
def save_preferences(google_id, raw_text, priority_profile,
                     informals_enabled=True, informal_categories=None):
    preferences_col.update_one(
        {"google_id": google_id},
        {"$set": {
            "google_id":           google_id,
            "raw_text":            raw_text,
            "priority_profile":    priority_profile,
            "informals_enabled":   informals_enabled,
            "informal_categories": informal_categories or ["food", "deals"],
            "updated_at":          datetime.utcnow().isoformat(),
        }},
        upsert=True
    )


def get_preferences(google_id):
    return preferences_col.find_one({"google_id": google_id})


# ── EMAILS ────────────────────────────────────────────
def save_email(google_id, email_data):
    email_data['google_id'] = google_id
    existing = emails_col.find_one({
        "google_id": google_id,
        "gmail_id":  email_data['gmail_id']
    })
    if existing:
        return str(existing['_id'])
    result = emails_col.insert_one(email_data)
    return str(result.inserted_id)


def update_email_classification(google_id, gmail_id, classification):
    classification['classified']    = True
    classification['classified_at'] = datetime.utcnow().isoformat()
    emails_col.update_one(
        {"google_id": google_id, "gmail_id": gmail_id},
        {"$set": classification}
    )


def get_emails(google_id, quadrant=None, class_filter=None,
               is_informal=False, limit=50):
    query = {"google_id": google_id, "classified": True}
    if quadrant:
        query["quadrant"] = quadrant
    if class_filter:
        query["class"] = class_filter
    if is_informal:
        query["is_informal"] = True

    emails = list(emails_col.find(query).sort("date", DESCENDING).limit(limit))
    for e in emails:
        e['_id'] = str(e['_id'])
    return emails


def search_emails(google_id, query_text, limit=20):
    import re
    pattern = re.compile(query_text, re.IGNORECASE)
    results = list(emails_col.find({
        "google_id":  google_id,
        "classified": True,
        "$or": [
            {"subject": {"$regex": pattern}},
            {"summary": {"$regex": pattern}},
            {"class":   {"$regex": pattern}},
            {"sender":  {"$regex": pattern}},
        ]
    }).sort("date", DESCENDING).limit(limit))
    for r in results:
        r['_id'] = str(r['_id'])
    return results


# ── NOTIFICATIONS ─────────────────────────────────────
def create_notification(google_id, gmail_id, message, importance):
    notifications_col.insert_one({
        "google_id":  google_id,
        "gmail_id":   gmail_id,
        "message":    message,
        "importance": importance,
        "seen":       False,
        "created_at": datetime.utcnow().isoformat(),
    })


def get_unseen_notifications(google_id):
    notifs = list(notifications_col.find(
        {"google_id": google_id, "seen": False}
    ).sort("created_at", DESCENDING))
    for n in notifs:
        n['_id'] = str(n['_id'])
    return notifs


def mark_notifications_seen(google_id):
    notifications_col.update_many(
        {"google_id": google_id, "seen": False},
        {"$set": {"seen": True}}
    )


# ── INDEXES ───────────────────────────────────────────
def create_indexes():
    users_col.create_index("google_id", unique=True)
    emails_col.create_index(
        [("google_id", ASCENDING), ("gmail_id", ASCENDING)], unique=True)
    emails_col.create_index(
        [("google_id", ASCENDING), ("quadrant", ASCENDING)])
    preferences_col.create_index("google_id", unique=True)
    notifications_col.create_index(
        [("google_id", ASCENDING), ("seen", ASCENDING)])
    print("Indexes created.")
