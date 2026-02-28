# emails/gemini_service.py
# Model 1 — Preference Interpreter
# Model 2 — Email Classifier + Summariser

import google.generativeai as genai
from django.conf import settings
import json
import re
import sys
import os

sys.path.insert(0, os.path.join(settings.BASE_DIR))
from college_data import CLUBS, FESTS, ACADEMIC, INTEREST_MAP, TRUSTED_SENDERS

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

ALL_CLASSES = list(CLUBS.keys()) + list(FESTS.keys()) + [
    "ACADEMIC", "INFORMAL_FOOD", "INFORMAL_DEALS", "SPAM", "OTHER"
]


# ════════════════════════════════════════════════════════
# MODEL 1 — PREFERENCE INTERPRETER
# Input:  "I like AI, interested in tech fests"
# Output: { "RAID": "high", "PROMETEO": "high", ... }
# ════════════════════════════════════════════════════════
def build_college_context():
    clubs_text = ""
    for code, info in CLUBS.items():
        clubs_text += f"- {code} ({info['full_name']}): keywords: {', '.join(info['keywords'][:5])}\n"

    fests_text = ""
    for name, info in FESTS.items():
        fests_text += f"- {name} ({info['full_name']}): keywords: {', '.join(info['keywords'][:4])}\n"

    academic_text = ", ".join([f"{k}={v}" for k, v in ACADEMIC.items()])

    return f"""
You are an AI assistant for IIT Jodhpur (IITJ) email management.

IITJ CLUBS:
{clubs_text}

IITJ FESTS:
{fests_text}

ACADEMIC TERMS: {academic_text}

IMPORTANT RULES:
- "AI" or "machine learning" or "data" → maps to RAID
- "robotics" or "embedded" → maps to ROBOTICS_CLUB
- "web" or "google" or "android" → maps to DSC
- "cars" or "automotive" → maps to BOLTHEADS
- "dance" → maps to GROOVE_THEORY
- "drama" or "theatre" → maps to DRAMATICS
- "music" or "singing" → maps to SANGAM
- "chess" → maps to CHESS_SOCIETY
- "quant" or "finance" or "trading" → maps to QUANT_CLUB
- "sports" (general) → maps to SPORTS_COUNCIL
- individual sports (football/cricket etc.) only if explicitly mentioned
"""


def interpret_preferences(user_text: str) -> dict:
    """
    Model 1 — maps user's interest text to IITJ club priority weights
    Returns: { "RAID": "high", "IGNUS": "medium", "DRAMATICS": "ignore", ... }
    """
    context = build_college_context()
    all_codes = list(CLUBS.keys()) + list(FESTS.keys())

    prompt = f"""
{context}

The user described their interests:
"{user_text}"

Map their interests to ALL clubs and fests listed above.
Return ONLY a valid JSON object. Include every single club and fest code.
Use exactly these values: "high", "medium", "low", "ignore"

Rules:
- "high"   = user clearly cares about this
- "medium" = might be relevant
- "low"    = include but deprioritise
- "ignore" = skip entirely — don't show emails from this

All codes to include: {json.dumps(all_codes)}

Return ONLY JSON, no explanation, no markdown backticks.
"""

    try:
        response = model.generate_content(prompt)
        text     = response.text.strip()
        text     = re.sub(r'```json|```', '', text).strip()
        profile  = json.loads(text)

        # Make sure all clubs are present — default missing ones to "low"
        for code in all_codes:
            if code not in profile:
                club = CLUBS.get(code, {})
                if club.get('default_priority') == 'ignore':
                    profile[code] = 'ignore'
                else:
                    profile[code] = 'low'

        return profile

    except Exception as e:
        print(f"Gemini preference error: {e}")
        # Fallback — return all as low
        return {code: 'low' for code in all_codes}


# ════════════════════════════════════════════════════════
# MODEL 2 — EMAIL CLASSIFIER + SUMMARISER
# Input:  email subject + body + user priority profile
# Output: class, importance, urgency, quadrant, colour,
#         action, summary, event_date, is_informal
# ════════════════════════════════════════════════════════
def classify_email(email_data: dict, priority_profile: dict, sender: str = '') -> dict:
    """
    Classify a single email using Gemini.
    Returns structured classification dict.
    """
    subject = email_data.get('subject', '')
    body    = email_data.get('body', '')[:1000]   # cap body for token efficiency

    # Check if from trusted sender — boost importance
    is_trusted = any(trusted in sender for trusted in TRUSTED_SENDERS)

    # Build priority context string for Gemini
    high_priority   = [k for k, v in priority_profile.items() if v == 'high']
    medium_priority = [k for k, v in priority_profile.items() if v == 'medium']
    ignore_list     = [k for k, v in priority_profile.items() if v == 'ignore']

    prompt = f"""
You are classifying an email for an IIT Jodhpur (IITJ) student.

USER'S PRIORITY PREFERENCES:
- HIGH priority clubs/fests: {', '.join(high_priority) or 'none'}
- MEDIUM priority: {', '.join(medium_priority) or 'none'}
- IGNORE these completely: {', '.join(ignore_list) or 'none'}
- Trusted sender (official IITJ): {'YES — boost importance' if is_trusted else 'no'}

EMAIL TO CLASSIFY:
Subject: {subject}
Body: {body}

CLASSIFICATION RULES:
1. importance = how much THIS USER cares based on their preferences
2. urgency    = how time-sensitive (deadline, exam, event date soon)
3. quadrant   = Q1 (high importance + high urgency)
                Q2 (high importance + low urgency)
                Q3 (low importance + high urgency)
                Q4 (low importance + low urgency)
4. is_informal = true if food deals, canteen, discounts, campus offers
5. action:
   - "notify"          → Q1 critical (exam, deadline, HOD email, urgent)
   - "add_to_calendar" → has a date/event worth tracking (hackathons, talks, fests, workshops, TEDx, seminars)
   - "ignore"          → Q4, spam, promotional

EVENT EXTRACTION RULES — extract ONLY if the email mentions a specific event:
- event_date: Extract the event date as "YYYY-MM-DD". Use 2026 as the year if not specified. If no date found, return null.
- event_time: Extract the exact start time as "HH:MM" in 24-hour format (e.g., "17:00" for 5 PM). If no time found, return null.
- event_venue: Extract the venue/location name (e.g., "LT-3", "MNIT Jaipur", "SAC Ground", "Online - Zoom"). Return null if not found.
- registration_link: Extract any registration/signup URL mentioned. Return null if none.
- organizer: Name of the club, fest, or person organising (e.g., "RAID Club", "DevClub", "TEDx IITJ"). Return null if not found.

VALID CLASSES: {', '.join(ALL_CLASSES)}

Return ONLY this JSON (no markdown, no explanation):
{{
  "class":             "RAID",
  "importance":        "high",
  "urgency":           "high",
  "quadrant":          "Q1",
  "colour":            "red",
  "action":            "add_to_calendar",
  "summary":           "2-line summary of the email here",
  "event_date":        "2026-03-15",
  "event_time":        "17:00",
  "event_venue":       "LT-3, Academic Block",
  "registration_link": "https://...",
  "organizer":         "RAID Club IITJ",
  "is_informal":       false
}}

colour must be: "red" for Q1, "yellow" for Q2, "blue" for Q3, "grey" for Q4
"""

    try:
        response = model.generate_content(prompt)
        text     = response.text.strip()
        text     = re.sub(r'```json|```', '', text).strip()
        result   = json.loads(text)

        # Validate required fields
        required = ['class', 'importance', 'urgency', 'quadrant',
                    'colour', 'action', 'summary', 'event_date', 'is_informal']
        for field in required:
            if field not in result:
                result[field] = get_default(field)
        # Optional rich fields — default to None if missing
        for field in ['event_time', 'event_venue', 'registration_link', 'organizer']:
            result.setdefault(field, None)

        return result

    except Exception as e:
        print(f"Gemini classify error: {e}")
        return get_fallback_classification()


def classify_all_emails(emails: list, priority_profile: dict) -> list:
    """
    Classify a batch of emails.
    Returns list of (gmail_id, classification) tuples.
    """
    results = []
    for email in emails:
        if email.get('classified'):
            continue    # skip already classified

        classification = classify_email(
            email_data=email,
            priority_profile=priority_profile,
            sender=email.get('sender', '')
        )
        results.append((email['gmail_id'], classification))

        # Small delay to avoid Gemini rate limits on free tier
        import time
        time.sleep(0.5)

    return results


# ── HELPERS ───────────────────────────────────────────
def get_default(field):
    defaults = {
        'class':             'OTHER',
        'importance':        'low',
        'urgency':           'low',
        'quadrant':          'Q4',
        'colour':            'grey',
        'action':            'ignore',
        'summary':           'No summary available',
        'event_date':        None,
        'event_time':        None,
        'event_venue':       None,
        'registration_link': None,
        'organizer':         None,
        'is_informal':       False,
    }
    return defaults.get(field)


def get_fallback_classification():
    return {
        'class':             'OTHER',
        'importance':        'low',
        'urgency':           'low',
        'quadrant':          'Q4',
        'colour':            'grey',
        'action':            'ignore',
        'summary':           'Could not classify this email',
        'event_date':        None,
        'event_time':        None,
        'event_venue':       None,
        'registration_link': None,
        'organizer':         None,
        'is_informal':       False,
    }
