# emails/calendar_service.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Maps quadrant colours to Google Calendar colour IDs
COLOUR_MAP = {
    'red':    '11',   # Tomato
    'yellow': '5',    # Banana
    'blue':   '9',    # Blueberry
    'grey':   '8',    # Graphite
}


def get_calendar_service(token_dict):
    creds = Credentials(
        token=token_dict.get('token', token_dict.get('access_token')),
        refresh_token=token_dict.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=token_dict['client_id'],
        client_secret=token_dict['client_secret'],
    )
    return build('calendar', 'v3', credentials=creds)


def create_calendar_event(token_dict, subject, summary, event_date, colour='yellow'):
    """
    Create a Google Calendar event from a classified email.
    event_date: "YYYY-MM-DD" string or None
    """
    service = get_calendar_service(token_dict)

    # Parse date — fallback to tomorrow if not found
    if event_date:
        try:
            start_date = datetime.strptime(event_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = (datetime.utcnow() + timedelta(days=1)).date()
    else:
        start_date = (datetime.utcnow() + timedelta(days=1)).date()

    end_date = start_date + timedelta(days=1)

    event = {
        'summary':     subject,
        'description': summary,
        'start': {
            'date':     start_date.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'date':     end_date.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'colorId': COLOUR_MAP.get(colour, '5'),
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 60},   # 1 hour before
            ],
        },
    }

    try:
        created = service.events().insert(
            calendarId='primary', body=event
        ).execute()
        return {'success': True, 'event_id': created.get('id'), 'link': created.get('htmlLink')}
    except Exception as e:
        print(f"Calendar error: {e}")
        return {'success': False, 'error': str(e)}
