"""
seed_db.py — Run this to populate MongoDB with sample data for testing.
Usage: python seed_db.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from datetime import datetime, date, timedelta

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['mailmind']

# Sample Google ID for testing (bypass real OAuth)
TEST_GOOGLE_ID = "test_user_001"
TEST_EMAIL     = "testuser@iitj.ac.in"

def seed():
    print("🌱 Seeding MailMind database...")

    # Clear old test data
    for col in ['users', 'preferences', 'calendar_events', 'notifications']:
        db[col].delete_many({"google_id": TEST_GOOGLE_ID})

    # Create test user
    db['users'].update_one(
        {"google_id": TEST_GOOGLE_ID},
        {"$set": {
            "google_id":  TEST_GOOGLE_ID,
            "email":      TEST_EMAIL,
            "name":       "Shreshth Dhimole",
            "roll_no":    "B22CS090",
            "picture":    "https://api.dicebear.com/7.x/initials/svg?seed=SD",
            "token":      {},  # Empty for demo — real token comes from OAuth
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
        }},
        upsert=True
    )
    print("✅ Test user created")

    # Create preferences
    db['preferences'].update_one(
        {"google_id": TEST_GOOGLE_ID},
        {"$set": {
            "google_id":   TEST_GOOGLE_ID,
            "raw_text":    "I love AI, machine learning, coding competitions, and RAID club",
            "priority_profile": {
                "RAID": "high", "DSC": "high", "ROBOTICS_CLUB": "medium",
                "IGNUS": "medium", "PROMETEO": "low", "CHESS_SOCIETY": "low",
                "DRAMATICS": "ignore", "SANGAM": "ignore",
            },
            "informals_enabled": True,
            "informal_categories": ["food", "deals"],
            "updated_at": datetime.utcnow().isoformat(),
        }},
        upsert=True
    )
    print("✅ Preferences saved")

    # Create calendar events
    today = date.today()
    events = [
        {"title": "Data Structures Exam",    "event_date": str(today),                       "event_time": "10:00", "colour": "red",    "quadrant": "Q1", "class": "EXAM",       "summary": "Mid-term exam on Trees, Graphs, Heaps"},
        {"title": "OS Assignment Due",        "event_date": str(today + timedelta(days=1)),   "event_time": "23:59", "colour": "yellow", "quadrant": "Q2", "class": "ASSIGNMENT", "summary": "Submit OS process scheduling assignment"},
        {"title": "Algorithms Lecture",       "event_date": str(today + timedelta(days=2)),   "event_time": "09:00", "colour": "blue",   "quadrant": "Q2", "class": "LECTURE",    "summary": "Dynamic programming — bring notes"},
        {"title": "Coding Club",              "event_date": str(today + timedelta(days=3)),   "event_time": "17:00", "colour": "purple", "quadrant": "Q3", "class": "CLUB",       "summary": "Weekly coding club — LeetCode session"},
        {"title": "ML Project Submission",    "event_date": str(today + timedelta(days=4)),   "event_time": "14:00", "colour": "yellow", "quadrant": "Q1", "class": "ASSIGNMENT", "summary": "Neural network implementation due"},
        {"title": "Physics Lab",              "event_date": str(today + timedelta(days=5)),   "event_time": "14:00", "colour": "blue",   "quadrant": "Q2", "class": "LAB",        "summary": "Optics experiment — bring lab manual"},
        {"title": "RAID Workshop",            "event_date": str(today + timedelta(days=7)),   "event_time": "15:00", "colour": "purple", "quadrant": "Q3", "class": "CLUB",       "summary": "Intro to LLMs and RAG systems"},
        {"title": "CN Assignment",            "event_date": str(today + timedelta(days=8)),   "event_time": "23:59", "colour": "yellow", "quadrant": "Q2", "class": "ASSIGNMENT", "summary": "Computer Networks socket programming lab"},
        {"title": "Quiz 3 - DBMS",            "event_date": str(today + timedelta(days=10)),  "event_time": "11:00", "colour": "red",    "quadrant": "Q1", "class": "EXAM",       "summary": "SQL joins, normalization, indexing"},
        {"title": "PROMETEO Hackathon",       "event_date": str(today + timedelta(days=14)),  "event_time": "09:00", "colour": "purple", "quadrant": "Q2", "class": "FEST",       "summary": "24-hr hackathon — team registration open"},
        {"title": "Study Session — Algo",     "event_date": str(today + timedelta(days=6)),   "event_time": "20:00", "colour": "green",  "quadrant": "Q2", "class": "STUDY",      "summary": "Group study for algorithms mid-sem"},
        {"title": "End Sem — DSA",            "event_date": str(today + timedelta(days=21)),  "event_time": "09:00", "colour": "red",    "quadrant": "Q1", "class": "EXAM",       "summary": "End semester exam for Data Structures"},
    ]
    for event in events:
        event['google_id']  = TEST_GOOGLE_ID
        event['gmail_id']   = None
        event['manual']     = True
        event['created_at'] = datetime.utcnow().isoformat()
        db['calendar_events'].insert_one(event)
    print(f"✅ {len(events)} calendar events created")

    # Create notifications
    notifications = [
        {"message": "Data Structures Exam is TODAY at 10:00 AM!", "importance": "high", "seen": False},
        {"message": "OS Assignment due TOMORROW at 11:59 PM",    "importance": "high", "seen": False},
        {"message": "RAID workshop registration closes today",   "importance": "medium","seen": False},
    ]
    for n in notifications:
        n['google_id']  = TEST_GOOGLE_ID
        n['gmail_id']   = None
        n['created_at'] = datetime.utcnow().isoformat()
        db['notifications'].insert_one(n)
    print(f"✅ {len(notifications)} notifications created")

    print(f"\n🎉 Done! Test user: {TEST_EMAIL} | google_id: {TEST_GOOGLE_ID}")
    print("   Set session manually or use /api/debug/login/ in development mode")


if __name__ == '__main__':
    seed()
