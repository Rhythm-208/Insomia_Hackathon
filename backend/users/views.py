from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
import os

def login_page(request):
    """Render the login page"""
    return render(request, 'login.html')
        
def initiate_google_auth(request):
    """Initiate Google OAuth flow"""
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.readonly'],
        redirect_uri=settings.REDIRECT_URI
    )
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    request.session['oauth_state'] = state
    return redirect(auth_url)

def oauth_callback(request):
    """Handle OAuth callback"""
    state = request.session.get('oauth_state')
    if not state:
        return JsonResponse({'error': 'No OAuth state found'}, status=400)
    
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.readonly'],
        state=state,
        redirect_uri=settings.REDIRECT_URI
    )
    
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    
    # Get user info
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    
    # Save user to database
    from emails.models import create_user
    google_id = user_info['id']
    email = user_info['email']
    name = user_info.get('name', '')
    picture = user_info.get('picture', '')
    
    create_user(google_id, email, name, '', picture, credentials_to_dict(credentials))
    
    # Store session info
    request.session['google_id'] = google_id
    request.session['email'] = email
    request.session['name'] = name
    
    return redirect('/')

def credentials_to_dict(credentials):
    """Convert credentials to dictionary"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    """Logout user and clear session"""
    request.session.flush()
    return JsonResponse({'success': True})

def check_auth(request):
    """Check if user is authenticated"""
    google_id = request.session.get('google_id')
    if google_id:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'google_id': google_id,
                'email': request.session.get('email'),
                'name': request.session.get('name')
            }
        })
    return JsonResponse({'authenticated': False})

def sync_google_calendar(request):
    """Sync Google Calendar events"""
    if not request.session.get('google_id'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    credentials_dict = request.session.get('credentials')
    if not credentials_dict:
        return JsonResponse({'error': 'No credentials found'}, status=401)
    
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    credentials = Credentials(**credentials_dict)
    service = build('calendar', 'v3', credentials=credentials)
    
    # Get events from Google Calendar
    events_result = service.events().list(
        calendarId='primary',
        timeMin='2026-01-01T00:00:00Z',
        maxResults=200,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # Save events to database
    from emails.models import save_calendar_event
    google_id = request.session['google_id']
    
    synced_count = 0
    for event in events:
        if 'dateTime' in event['start']:
            event_data = {
                'title': event['summary'],
                'event_date': event['start']['dateTime'][:10],
                'event_time': event['start']['dateTime'][11:16] if 'dateTime' in event['start'] else '',
                'summary': event.get('description', ''),
                'google_event_id': event['id'],
                'manual': False
            }
            
            # Determine event type and quadrant
            summary_lower = event.get('summary', '').lower()
            if any(word in summary_lower for word in ['exam', 'test', 'quiz']):
                event_data.update({'event_type': 'exam', 'class': 'EXAM', 'quadrant': 'Q1'})
            elif any(word in summary_lower for word in ['assignment', 'due', 'submission']):
                event_data.update({'event_type': 'assignment', 'class': 'ASSIGNMENT', 'quadrant': 'Q2'})
            elif any(word in summary_lower for word in ['lecture', 'class', 'session']):
                event_data.update({'event_type': 'lecture', 'class': 'LECTURE', 'quadrant': 'Q2'})
            elif any(word in summary_lower for word in ['lab', 'practical']):
                event_data.update({'event_type': 'lab', 'class': 'LAB', 'quadrant': 'Q2'})
            elif any(word in summary_lower for word in ['club', 'meeting', 'workshop']):
                event_data.update({'event_type': 'club', 'class': 'CLUB', 'quadrant': 'Q3'})
            else:
                event_data.update({'event_type': 'study', 'class': 'STUDY', 'quadrant': 'Q2'})
            
            save_calendar_event(google_id, event_data)
            synced_count += 1
    
    return JsonResponse({
        'success': True,
        'synced': synced_count,
        'total': len(events)
    })