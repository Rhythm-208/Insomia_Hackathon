# emails/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .gmail_service import fetch_emails
from .gemini_service import interpret_preferences, classify_all_emails
from .calendar_service import create_calendar_event
from .models import (
    get_user, save_email, update_email_classification,
    get_emails, search_emails, save_preferences, get_preferences,
    create_notification, get_unseen_notifications, mark_notifications_seen
)


def auth_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('google_id'):
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


# ════════════════════════════════════════════════════════
# PREFERENCES
# POST /api/emails/preferences/
# ════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def save_user_preferences(request):
    """
    User submits: { "text": "I like AI and fests", "informals": true }
    Gemini maps it to priority profile → saved to MongoDB
    """
    google_id = request.session.get('google_id')
    try:
        data             = json.loads(request.body)
        raw_text         = data.get('text', '').strip()
        informals        = data.get('informals', True)
        informal_cats    = data.get('informal_categories', ['food', 'deals'])

        if not raw_text:
            return JsonResponse({'error': 'Preference text is required'}, status=400)

        # Run Model 1 — interpret preferences
        priority_profile = interpret_preferences(raw_text)

        save_preferences(
            google_id=google_id,
            raw_text=raw_text,
            priority_profile=priority_profile,
            informals_enabled=informals,
            informal_categories=informal_cats
        )

        return JsonResponse({
            'success':          True,
            'priority_profile': priority_profile,
            'message':          'Preferences saved. Fetching your emails now...'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@auth_required
def get_user_preferences(request):
    google_id = request.session.get('google_id')
    prefs = get_preferences(google_id)
    if not prefs:
        return JsonResponse({'has_preferences': False})
    prefs['_id'] = str(prefs['_id'])
    return JsonResponse({'has_preferences': True, 'preferences': prefs})


# ════════════════════════════════════════════════════════
# FETCH + CLASSIFY EMAILS
# POST /api/emails/fetch/
# ════════════════════════════════════════════════════════
@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def fetch_and_classify(request):
    """
    1. Fetch emails from Gmail
    2. Save raw emails to MongoDB
    3. Run Model 2 on each email
    4. Create calendar events for Q1/Q2
    5. Create notifications for Q1 critical
    """
    google_id = request.session.get('google_id')
    user      = get_user(google_id)
    prefs     = get_preferences(google_id)

    if not user:
        return JsonResponse({'error': 'User not found'}, status=404)
    if not prefs:
        return JsonResponse({'error': 'Set preferences first'}, status=400)

    try:
        # Step 1 — fetch from Gmail
        emails = fetch_emails(user['token'], max_results=50)

        # Step 2 — save raw emails
        for email in emails:
            save_email(google_id, email)

        # Step 3 — classify all with Gemini
        priority_profile   = prefs['priority_profile']
        classifications    = classify_all_emails(emails, priority_profile)

        calendar_count = 0
        notify_count   = 0

        for gmail_id, classification in classifications:
            # Save classification to MongoDB
            update_email_classification(google_id, gmail_id, classification)

            # Step 4 — Calendar for Q1 and Q2
            if classification['action'] == 'add_to_calendar':
                email_data = next((e for e in emails if e['gmail_id'] == gmail_id), None)
                if email_data:
                    create_calendar_event(
                        token_dict  = user['token'],
                        subject     = email_data['subject'],
                        summary     = classification['summary'],
                        event_date  = classification['event_date'],
                        colour      = classification['colour']
                    )
                    calendar_count += 1

            # Step 5 — Notifications for Q1 notify
            if classification['action'] == 'notify':
                email_data = next((e for e in emails if e['gmail_id'] == gmail_id), None)
                if email_data:
                    create_notification(
                        google_id  = google_id,
                        gmail_id   = gmail_id,
                        message    = classification['summary'],
                        importance = classification['importance']
                    )
                    notify_count += 1

        return JsonResponse({
            'success':        True,
            'fetched':        len(emails),
            'classified':     len(classifications),
            'calendar_added': calendar_count,
            'notifications':  notify_count,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ════════════════════════════════════════════════════════
# GET EMAILS — dashboard
# GET /api/emails/
# ════════════════════════════════════════════════════════
@require_http_methods(["GET"])
@auth_required
def get_user_emails(request):
    google_id    = request.session.get('google_id')
    quadrant     = request.GET.get('quadrant')
    class_filter = request.GET.get('class')
    is_informal  = request.GET.get('informal', 'false').lower() == 'true'
    limit        = int(request.GET.get('limit', 50))

    emails = get_emails(google_id, quadrant=quadrant,
                        class_filter=class_filter,
                        is_informal=is_informal, limit=limit)

    grouped = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': [], 'informal': []}
    for e in emails:
        if e.get('is_informal'):
            grouped['informal'].append(e)
        else:
            grouped[e.get('quadrant', 'Q4')].append(e)

    return JsonResponse({
        'success': True,
        'emails':  emails,
        'grouped': grouped,
        'counts':  {k: len(v) for k, v in grouped.items()}
    })


# ════════════════════════════════════════════════════════
# SEARCH
# GET /api/emails/search/?q=RAID
# ════════════════════════════════════════════════════════
@require_http_methods(["GET"])
@auth_required
def search_user_emails(request):
    google_id  = request.session.get('google_id')
    query_text = request.GET.get('q', '').strip()
    if not query_text:
        return JsonResponse({'error': 'q param required'}, status=400)
    results = search_emails(google_id, query_text)
    return JsonResponse({'success': True, 'query': query_text,
                         'count': len(results), 'results': results})


# ════════════════════════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════════════════════════
@require_http_methods(["GET"])
@auth_required
def get_notifications(request):
    google_id = request.session.get('google_id')
    notifs    = get_unseen_notifications(google_id)
    return JsonResponse({'success': True, 'notifications': notifs, 'count': len(notifs)})


@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def mark_seen(request):
    mark_notifications_seen(request.session.get('google_id'))
    return JsonResponse({'success': True})
