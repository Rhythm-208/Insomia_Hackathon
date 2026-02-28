# emails/models.py — FIXED + EXTENDED + FALLBACK
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import os

# Import persistent storage
from .storage import (get_users, get_emails, get_preferences, get_notifications, get_calendar,
                      save_users, save_emails, save_preferences, save_notifications, save_calendar)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
try:
    client    = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000, connectTimeoutMS=1000)
    # Test the connection
    client.admin.command('ping')
    db        = client['mailmind']
    users_col          = db['users']
    emails_col         = db['emails']
    preferences_col    = db['preferences']
    notifications_col  = db['notifications']
    calendar_col       = db['calendar_events']   # NEW
    MONGO_AVAILABLE = True
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    print("Using fallback persistent file storage for testing")
    MONGO_AVAILABLE = False
    # Fallback persistent storage
    users_col = get_users()
    emails_col = get_emails()
    preferences_col = get_preferences()
    notifications_col = get_notifications()
    calendar_col = get_calendar()


# ── USERS ─────────────────────────────────────────────
def create_user(google_id, email, name, roll_no, picture, token_dict):
    if MONGO_AVAILABLE:
        existing = users_col.find_one({"google_id": google_id})
        if existing:
            users_col.update_one(
                {"google_id": google_id},
                {"$set": {"token": token_dict, "last_login": datetime.utcnow().isoformat()}}
            )
            return str(existing['_id'])
        result = users_col.insert_one({
            "google_id":  google_id, "email": email, "name": name,
            "roll_no":    roll_no,   "picture": picture, "token": token_dict,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
        })
        return str(result.inserted_id)
    else:
        # Fallback: simple in-memory storage
        user = {
            "google_id": google_id, "email": email, "name": name,
            "roll_no": roll_no, "picture": picture, "token": token_dict,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
        }
        users_col.append(user)
        save_users()
        return str(len(users_col) - 1)


def get_user(google_id):
    if MONGO_AVAILABLE:
        return users_col.find_one({"google_id": google_id})
    else:
        for user in users_col:
            if user.get("google_id") == google_id:
                return user
        return None


# ── PREFERENCES ───────────────────────────────────────
def save_preferences(google_id, raw_text, priority_profile,
                     informals_enabled=True, informal_categories=None, **kwargs):
    if MONGO_AVAILABLE:
        preferences_col.update_one(
            {"google_id": google_id},
            {"$set": {
                "google_id":           google_id,
                "raw_text":            raw_text,
                "priority_profile":    priority_profile,
                "informals_enabled":   informals_enabled,
                "informal_categories": informal_categories or ["food", "deals"],
                "manual_absences":     kwargs.get("manual_absences", {}),
                "updated_at":          datetime.utcnow().isoformat(),
            }},
            upsert=True
        )
    else:
        # Fallback: in-memory storage
        for pref in preferences_col:
            if pref.get("google_id") == google_id:
                pref.update({
                    "raw_text": raw_text,
                    "priority_profile": priority_profile,
                    "informals_enabled": informals_enabled,
                    "informal_categories": informal_categories or ["food", "deals"],
                    "manual_absences": kwargs.get("manual_absences", pref.get("manual_absences", {})),
                    "updated_at": datetime.utcnow().isoformat(),
                })
                save_preferences()
                return
        preferences_col.append({
            "google_id": google_id,
            "raw_text": raw_text,
            "priority_profile": priority_profile,
            "informals_enabled": informals_enabled,
            "informal_categories": informal_categories or ["food", "deals"],
            "manual_absences": kwargs.get("manual_absences", {}),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_preferences()


def get_preferences(google_id):
    if MONGO_AVAILABLE:
        return preferences_col.find_one({"google_id": google_id})
    else:
        for pref in preferences_col:
            if pref.get("google_id") == google_id:
                return pref
        return None


# ── EMAILS ────────────────────────────────────────────
def save_email(google_id, email_data):
    if MONGO_AVAILABLE:
        email_data['google_id'] = google_id
        existing = emails_col.find_one({
            "google_id": google_id, "gmail_id": email_data['gmail_id']
        })
        if existing:
            return str(existing['_id'])
        result = emails_col.insert_one(email_data)
        return str(result.inserted_id)
    else:
        # Fallback: in-memory storage
        email_data['google_id'] = google_id
        for email in emails_col:
            if email.get('gmail_id') == email_data.get('gmail_id'):
                return str(emails_col.index(email))
        emails_col.append(email_data)
        save_emails()
        return str(len(emails_col) - 1)


def update_email_classification(google_id, gmail_id, classification):
    if MONGO_AVAILABLE:
        classification['classified']    = True
        classification['classified_at'] = datetime.utcnow().isoformat()
        emails_col.update_one(
            {"google_id": google_id, "gmail_id": gmail_id},
            {"$set": classification}
        )
    else:
        # Fallback: in-memory storage
        for email in emails_col:
            if email.get('google_id') == google_id and email.get('gmail_id') == gmail_id:
                email.update(classification)
                email['classified'] = True
                email['classified_at'] = datetime.utcnow().isoformat()
                save_emails()
                break


def get_emails(google_id, quadrant=None, class_filter=None,
               is_informal=False, limit=50):
    if MONGO_AVAILABLE:
        query = {"google_id": google_id, "classified": True}
        if quadrant:    query["quadrant"]    = quadrant
        if class_filter: query["class"]     = class_filter
        if is_informal: query["is_informal"] = True
        emails = list(emails_col.find(query).sort("date", DESCENDING).limit(limit))
        for e in emails:
            e['_id'] = str(e['_id'])
        return emails
    else:
        # Fallback: in-memory storage
        emails = [e for e in emails_col if e.get('google_id') == google_id and e.get('classified')]
        if quadrant:
            emails = [e for e in emails if e.get('quadrant') == quadrant]
        if class_filter:
            emails = [e for e in emails if e.get('class') == class_filter]
        if is_informal:
            emails = [e for e in emails if e.get('is_informal')]
        emails.sort(key=lambda x: x.get('date', ''), reverse=True)
        return emails[:limit]


def search_emails(google_id, query_text, limit=20):
    if MONGO_AVAILABLE:
        import re
        pattern = re.compile(query_text, re.IGNORECASE)
        results = list(emails_col.find({
            "google_id": google_id, "classified": True,
            "$or": [
                {"subject": {"$regex": pattern}}, {"summary": {"$regex": pattern}},
                {"class":   {"$regex": pattern}}, {"sender":  {"$regex": pattern}},
            ]
        }).sort("date", DESCENDING).limit(limit))
        for r in results:
            r['_id'] = str(r['_id'])
        return results
    else:
        # Fallback: in-memory storage
        import re
        pattern = re.compile(query_text, re.IGNORECASE)
        results = []
        for email in emails_col:
            if email.get('google_id') != google_id or not email.get('classified'):
                continue
            if (pattern.search(email.get('subject', '')) or
                pattern.search(email.get('summary', '')) or
                pattern.search(email.get('class', '')) or
                pattern.search(email.get('sender', ''))):
                results.append(email)
        results.sort(key=lambda x: x.get('date', ''), reverse=True)
        return results[:limit]


# ── CALENDAR EVENTS (NEW) ─────────────────────────────
def save_calendar_event(google_id, event_data):
    if MONGO_AVAILABLE:
        event_data['google_id']  = google_id
        event_data['created_at'] = datetime.utcnow().isoformat()
        # FIX: Upsert by gmail_id if it exists, else insert fresh
        if event_data.get('gmail_id'):
            result = calendar_col.update_one(
                {"google_id": google_id, "gmail_id": event_data['gmail_id']},
                {"$set": event_data},
                upsert=True
            )
        else:
            result = calendar_col.insert_one(event_data)
        return True
    else:
        # Fallback: in-memory storage with persistence
        event_data['google_id']  = google_id
        event_data['created_at'] = datetime.utcnow().isoformat()
        
        # Default attended to False if not present
        if 'attended' not in event_data:
            event_data['attended'] = False
        
        # Determine unique key for matching (prefer google_event_id, then gmail_id)
        match_key = None
        match_val = None
        if event_data.get('google_event_id'):
            match_key = 'google_event_id'
            match_val = event_data['google_event_id']
        elif event_data.get('gmail_id'):
            match_key = 'gmail_id'
            match_val = event_data['gmail_id']

        if match_key:
            for i, event in enumerate(calendar_col):
                if event.get(match_key) == match_val and event.get('google_id') == google_id:
                    # PRESERVE ATTENDED STATUS IF IT EXISTS
                    event_data['attended'] = event.get('attended', False)
                    calendar_col[i] = event_data
                    save_calendar()  # Persist changes
                    return True

        calendar_col.append(event_data)
        save_calendar()  # Persist changes
        return True


def update_event_attendance(google_id, event_id, attended):
    """Toggle attendance for a specific event"""
    if calendar_table is not None:
        try:
            from bson import ObjectId
            calendar_table.update_one(
                {"google_id": google_id, "_id": ObjectId(event_id)},
                {"$set": {"attended": attended}}
            )
            return True
        except Exception:
            return False
    else:
        try:
            # For fallback, id is the index
            idx = int(event_id)
            if 0 <= idx < len(calendar_col):
                if calendar_col[idx].get('google_id') == google_id:
                    calendar_col[idx]['attended'] = attended
                    save_calendar()
                    return True
            # Search by google_event_id or gmail_id if not index
            for event in calendar_col:
                if (event.get('google_event_id') == event_id or event.get('gmail_id') == event_id) and event.get('google_id') == google_id:
                    event['attended'] = attended
                    save_calendar()
                    return True
            return False
        except Exception:
            return False


def get_calendar_events(google_id, month=None, year=None):
    if MONGO_AVAILABLE:
        query = {"google_id": google_id}
        if month and year:
            # Filter by month/year string prefix: "2026-03"
            prefix = f"{year}-{str(month).zfill(2)}"
            query["event_date"] = {"$regex": f"^{prefix}"}
        events = list(calendar_col.find(query).sort("event_date", ASCENDING))
        for e in events:
            e['_id'] = str(e['_id'])
        return events
    else:
        # Fallback: in-memory storage
        events = [e for e in calendar_col if e.get('google_id') == google_id]
        if month and year:
            prefix = f"{year}-{str(month).zfill(2)}"
            events = [e for e in events if e.get('event_date', '').startswith(prefix)]
        events.sort(key=lambda x: x.get('event_date', ''))
        return events


# ── NOTIFICATIONS ─────────────────────────────────────
def create_notification(google_id, gmail_id, message, importance):
    if MONGO_AVAILABLE:
        notifications_col.insert_one({
            "google_id":  google_id, "gmail_id":   gmail_id,
            "message":    message,   "importance": importance,
            "seen": False, "created_at": datetime.utcnow().isoformat(),
        })
    else:
        # Fallback: in-memory storage
        notifications_col.append({
            "google_id": google_id, "gmail_id": gmail_id,
            "message": message, "importance": importance,
            "seen": False, "created_at": datetime.utcnow().isoformat(),
        })
        save_notifications()


def get_unseen_notifications(google_id):
    if MONGO_AVAILABLE:
        notifs = list(notifications_col.find(
            {"google_id": google_id, "seen": False}
        ).sort("created_at", DESCENDING))
        for n in notifs:
            n['_id'] = str(n['_id'])
        return notifs
    else:
        # Fallback: in-memory storage
        notifs = [n for n in notifications_col if n.get('google_id') == google_id and not n.get('seen')]
        notifs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return notifs


def mark_notifications_seen(google_id):
    if MONGO_AVAILABLE:
        notifications_col.update_many(
            {"google_id": google_id, "seen": False},
            {"$set": {"seen": True}}
        )
    else:
        # Fallback: in-memory storage
        for notif in notifications_col:
            if notif.get('google_id') == google_id and not notif.get('seen'):
                notif['seen'] = True
                save_notifications()


# ── SEED SAMPLE DATA (for testing without real Gmail) ─
def seed_sample_data(google_id):
    """Call this to populate MongoDB with demo events — for testing only"""
    from datetime import date, timedelta
    today = date.today()
    sample_events = [
        {"title": "Data Structures Exam", "event_date": str(today),
         "event_time": "10:00", "colour": "red", "quadrant": "Q1",
         "class": "EXAM", "summary": "Mid-term exam on Trees and Graphs", "manual": True},
        {"title": "OS Assignment Due", "event_date": str(today + timedelta(days=1)),
         "event_time": "23:59", "colour": "yellow", "quadrant": "Q2",
         "class": "ASSIGNMENT", "summary": "Submit OS process scheduling assignment", "manual": True},
        {"title": "Algorithms Lecture", "event_date": str(today + timedelta(days=2)),
         "event_time": "09:00", "colour": "blue", "quadrant": "Q2",
         "class": "LECTURE", "summary": "Dynamic programming lecture — bring notes", "manual": True},
        {"title": "Coding Club", "event_date": str(today + timedelta(days=3)),
         "event_time": "17:00", "colour": "purple", "quadrant": "Q3",
         "class": "CLUB", "summary": "Weekly coding club meetup", "manual": True},
        {"title": "ML Project Submission", "event_date": str(today + timedelta(days=4)),
         "event_time": "14:00", "colour": "yellow", "quadrant": "Q1",
         "class": "ASSIGNMENT", "summary": "Final ML project — neural network implementation", "manual": True},
        {"title": "Quiz 3 - DBMS", "event_date": str(today + timedelta(days=10)),
         "event_time": "11:00", "colour": "red", "quadrant": "Q1",
         "class": "EXAM", "summary": "Quiz covers SQL joins, normalization", "manual": True},
        {"title": "RAID Workshop", "event_date": str(today + timedelta(days=7)),
         "event_time": "15:00", "colour": "purple", "quadrant": "Q3",
         "class": "CLUB", "summary": "AI/ML workshop by RAID club", "manual": True},
        {"title": "Physics Lab", "event_date": str(today + timedelta(days=5)),
         "event_time": "14:00", "colour": "blue", "quadrant": "Q2",
         "class": "LAB", "summary": "Optics experiment — bring lab manual", "manual": True},
    ]
    for event in sample_events:
        event['google_id']   = google_id
        event['created_at']  = datetime.utcnow().isoformat()
        event['gmail_id']    = None
        if MONGO_AVAILABLE:
            calendar_col.insert_one(event)
        else:
            calendar_col.append(event)
    if not MONGO_AVAILABLE:
        save_calendar()
    return len(sample_events)


# ── INDEXES ───────────────────────────────────────────
def create_indexes():
    if MONGO_AVAILABLE:
        users_col.create_index("google_id", unique=True)
        emails_col.create_index(
            [("google_id", ASCENDING), ("gmail_id", ASCENDING)], unique=True)
        emails_col.create_index([("google_id", ASCENDING), ("quadrant", ASCENDING)])
        preferences_col.create_index("google_id", unique=True)
        notifications_col.create_index([("google_id", ASCENDING), ("seen", ASCENDING)])
        calendar_col.create_index([("google_id", ASCENDING), ("event_date", ASCENDING)])
        print("Indexes created.")
    else:
        print("Using in-memory storage - no indexes needed")

# Initialize indexes on import
create_indexes()
