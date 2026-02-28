# emails/views.py — FIXED
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
    create_notification, get_unseen_notifications, mark_notifications_seen,
    get_calendar_events, save_calendar_event, create_indexes  # FIX: added calendar event storage and indexes
)


def auth_required(view_func):
    """FIX: Added functools.wraps to preserve function metadata"""
    import functools
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('google_id'):
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def save_user_preferences(request):
    google_id = request.session.get('google_id')
    try:
        data          = json.loads(request.body)
        raw_text      = data.get('text', '').strip()
        informals     = data.get('informals', True)
        informal_cats = data.get('informal_categories', ['food', 'deals'])

        if not raw_text:
            return JsonResponse({'error': 'Preference text is required'}, status=400)

        priority_profile = interpret_preferences(raw_text)

        save_preferences(
            google_id=google_id, raw_text=raw_text,
            priority_profile=priority_profile,
            informals_enabled=informals, informal_categories=informal_cats
        )
        return JsonResponse({
            'success': True, 'priority_profile': priority_profile,
            'message': 'Preferences saved. Fetching your emails now...'
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
    if '_id' in prefs:
        prefs['_id'] = str(prefs['_id'])
    return JsonResponse({'has_preferences': True, 'preferences': prefs})


@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def fetch_and_classify(request):
    google_id = request.session.get('google_id')
    user  = get_user(google_id)
    prefs = get_preferences(google_id)

    if not user:
        return JsonResponse({'error': 'User not found'}, status=404)
    if not prefs:
        return JsonResponse({'error': 'Set preferences first'}, status=400)

    try:
        emails = fetch_emails(user['token'], max_results=50)
        for email in emails:
            save_email(google_id, email)

        priority_profile = prefs['priority_profile']
        classifications  = classify_all_emails(emails, priority_profile)

        calendar_count = 0
        notify_count   = 0

        for gmail_id, classification in classifications:
            update_email_classification(google_id, gmail_id, classification)

            if classification['action'] == 'add_to_calendar':
                email_data = next((e for e in emails if e['gmail_id'] == gmail_id), None)
                if email_data:
                    result = create_calendar_event(
                        token_dict=user['token'],
                        subject=email_data['subject'],
                        summary=classification['summary'],
                        event_date=classification['event_date'],
                        colour=classification['colour']
                    )
                    # FIX: Also store calendar event in MongoDB for dashboard display
                    save_calendar_event(google_id, {
                        'gmail_id': gmail_id,
                        'title': email_data['subject'],
                        'summary': classification['summary'],
                        'event_date': classification['event_date'],
                        'colour': classification['colour'],
                        'quadrant': classification['quadrant'],
                        'class': classification['class'],
                        'google_event_id': result.get('event_id'),
                    })
                    calendar_count += 1

            if classification['action'] == 'notify':
                email_data = next((e for e in emails if e['gmail_id'] == gmail_id), None)
                if email_data:
                    create_notification(
                        google_id=google_id, gmail_id=gmail_id,
                        message=classification['summary'],
                        importance=classification['importance']
                    )
                    notify_count += 1

        return JsonResponse({
            'success': True, 'fetched': len(emails),
            'classified': len(classifications),
            'calendar_added': calendar_count, 'notifications': notify_count,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@auth_required
def get_user_emails(request):
    google_id    = request.session.get('google_id')
    quadrant     = request.GET.get('quadrant')
    class_filter = request.GET.get('class')
    is_informal  = request.GET.get('informal', 'false').lower() == 'true'
    limit        = int(request.GET.get('limit', 50))

    emails = get_emails(google_id, quadrant=quadrant, class_filter=class_filter,
                        is_informal=is_informal, limit=limit)

    grouped = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': [], 'informal': []}
    for e in emails:
        if e.get('is_informal'):
            grouped['informal'].append(e)
        else:
            grouped[e.get('quadrant', 'Q4')].append(e)

    return JsonResponse({
        'success': True, 'emails': emails, 'grouped': grouped,
        'counts': {k: len(v) for k, v in grouped.items()}
    })


@require_http_methods(["GET"])
@auth_required
def get_user_calendar_events(request):
    """NEW endpoint: get all calendar events for the dashboard calendar"""
    google_id = request.session.get('google_id')
    events = get_calendar_events(google_id)
    return JsonResponse({'success': True, 'events': events, 'count': len(events)})


@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def add_manual_event(request):
    """NEW endpoint: manually add a calendar event from the frontend"""
    google_id = request.session.get('google_id')
    try:
        data = json.loads(request.body)
        required = ['title', 'event_date', 'event_type']
        for field in required:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)

        # Map event type to colour and quadrant
        type_map = {
            'exam':     {'colour': 'red',    'quadrant': 'Q1'},
            'assignment': {'colour': 'yellow', 'quadrant': 'Q2'},
            'lecture':  {'colour': 'blue',   'quadrant': 'Q2'},
            'lab':      {'colour': 'blue',   'quadrant': 'Q2'},
            'club':     {'colour': 'purple', 'quadrant': 'Q3'},
            'study':    {'colour': 'green',  'quadrant': 'Q2'},
        }
        meta = type_map.get(data['event_type'], {'colour': 'grey', 'quadrant': 'Q4'})

        event = {
            'gmail_id':   None,
            'title':      data['title'],
            'summary':    data.get('description', ''),
            'event_date': data['event_date'],
            'event_time': data.get('event_time', ''),
            'colour':     meta['colour'],
            'quadrant':   meta['quadrant'],
            'class':      data['event_type'].upper(),
            'manual':     True,
        }
        save_calendar_event(google_id, event)
        return JsonResponse({'success': True, 'event': event})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
