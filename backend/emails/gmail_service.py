# emails/gmail_service.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import base64
import re


def get_gmail_service(token_dict):
    creds = Credentials(
        token=token_dict['access_token'],
        refresh_token=token_dict.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=token_dict['client_id'],
        client_secret=token_dict['client_secret'],
    )
    return build('gmail', 'v1', credentials=creds)


def fetch_emails(token_dict, max_results=50):
    service  = get_gmail_service(token_dict)
    result   = service.users().messages().list(
        userId='me', maxResults=max_results, labelIds=['INBOX']
    ).execute()
    messages = result.get('messages', [])

    emails_list = []
    for msg in messages:
        try:
            full_msg = service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()
            parsed = parse_email(full_msg)
            if parsed:
                emails_list.append(parsed)
        except Exception as e:
            print(f"Error fetching {msg['id']}: {e}")
            continue

    return emails_list


def parse_email(msg):
    headers      = {h['name']: h['value'] for h in msg['payload']['headers']}
    subject      = headers.get('Subject', '(no subject)')
    sender       = headers.get('From', '')
    date         = headers.get('Date', '')
    sender_email = sender.split('<')[1].replace('>', '').strip() if '<' in sender else sender
    body         = extract_body(msg['payload'])

    return {
        'gmail_id':    msg['id'],
        'subject':     subject,
        'body':        body[:2000],
        'sender':      sender_email,
        'sender_full': sender,
        'date':        date,
        'snippet':     msg.get('snippet', ''),
        'classified':  False,
        'fetched_at':  datetime.utcnow().isoformat(),
    }


def extract_body(payload):
    body = ''
    if 'body' in payload and payload['body'].get('data'):
        body = decode_base64(payload['body']['data'])
    elif 'parts' in payload:
        for part in payload['parts']:
            mime = part.get('mimeType', '')
            if mime == 'text/plain' and part['body'].get('data'):
                body = decode_base64(part['body']['data'])
                break
            elif mime == 'text/html' and not body and part['body'].get('data'):
                body = strip_html(decode_base64(part['body']['data']))
            elif mime.startswith('multipart'):
                body = extract_body(part)
                if body:
                    break
    return body.strip()


def decode_base64(data):
    try:
        return base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
    except Exception:
        return ''


def strip_html(html):
    clean = re.sub(r'<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', clean).strip()
