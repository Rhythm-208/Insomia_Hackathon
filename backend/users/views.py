# users/views.py
# Google OAuth 2.0 Login Flow

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import os
import json
import requests
from google_auth_oauthlib.flow import Flow

from emails.models import create_user, get_user, users_col

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
]

CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')
REDIRECT_URI     = os.getenv('REDIRECT_URI', 'http://localhost:8000/auth/callback/')


def get_flow():
    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )


# ── STEP 1: /auth/login/ ───────────────────────────────
def login(request):
    """Returns Google OAuth URL for React to redirect to"""
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    request.session['oauth_state'] = state
    return JsonResponse({'success': True, 'auth_url': auth_url})


# ── STEP 2: /auth/callback/ ───────────────────────────
def callback(request):
    """Google redirects here after user approves"""
    state = request.GET.get('state')
    if state != request.session.get('oauth_state'):
        return JsonResponse({'error': 'Invalid state'}, status=400)

    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'No code from Google'}, status=400)

    try:
        flow = get_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_dict = {
            'access_token':  creds.token,
            'refresh_token': creds.refresh_token,
            'client_id':     creds.client_id,
            'client_secret': creds.client_secret,
            'token_uri':     creds.token_uri,
        }

        user_info = get_google_user_info(creds.token)
        google_id = user_info['id']

        create_user(
            google_id=google_id,
            email=user_info['email'],
            name=user_info.get('name', ''),
            roll_no='',
            picture=user_info.get('picture', ''),
            token_dict=token_dict
        )

        request.session['google_id'] = google_id
        request.session['email']     = user_info['email']
        request.session['name']      = user_info.get('name', '')

        user = get_user(google_id)
        if not user.get('roll_no'):
            return HttpResponseRedirect('http://127.0.0.1:5500/InboxIQ.html')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── STEP 3: /auth/profile/ ────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def save_profile(request):
    """Save Name + Roll No for new users"""
    google_id = request.session.get('google_id')
    if not google_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    try:
        data    = json.loads(request.body)
        name    = data.get('name', '').strip()
        roll_no = data.get('roll_no', '').strip().upper()

        if not name or not roll_no:
            return JsonResponse({'error': 'Name and Roll No required'}, status=400)

        users_col.update_one(
            {'google_id': google_id},
            {'$set': {'name': name, 'roll_no': roll_no}}
        )
        request.session['name']    = name
        request.session['roll_no'] = roll_no

        return JsonResponse({'success': True, 'next': 'preferences'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── STEP 4: /auth/me/ ─────────────────────────────────
def me(request):
    """Check login status — React calls this on every page load"""
    google_id = request.session.get('google_id')
    if not google_id:
        return JsonResponse({'logged_in': False}, status=401)

    user = get_user(google_id)
    if not user:
        return JsonResponse({'logged_in': False}, status=401)

    return JsonResponse({
        'logged_in': True,
        'google_id': google_id,
        'email':     user['email'],
        'name':      user['name'],
        'roll_no':   user.get('roll_no', ''),
        'picture':   user.get('picture', ''),
    })


# ── STEP 5: /auth/logout/ ─────────────────────────────
def logout(request):
    request.session.flush()
    return JsonResponse({'success': True})


# ── HELPER ────────────────────────────────────────────
def get_google_user_info(access_token):
    r = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    return r.json()
