import json
import os
from datetime import datetime

# File-based storage for persistence when MongoDB is not available
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)

def load_data(filename):
    """Load data from JSON file"""
    filepath = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(filename, data):
    """Save data to JSON file"""
    filepath = os.path.join(STORAGE_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# Load initial data
users_data = load_data('users.json')
emails_data = load_data('emails.json')
preferences_data = load_data('preferences.json')
notifications_data = load_data('notifications.json')
calendar_data = load_data('calendar.json')

def get_users():
    return users_data

def get_emails():
    return emails_data

def get_preferences():
    return preferences_data

def get_notifications():
    return notifications_data

def get_calendar():
    return calendar_data

def save_users():
    save_data('users.json', users_data)

def save_emails():
    save_data('emails.json', emails_data)

def save_preferences():
    save_data('preferences.json', preferences_data)

def save_notifications():
    save_data('notifications.json', notifications_data)

def save_calendar():
    save_data('calendar.json', calendar_data)