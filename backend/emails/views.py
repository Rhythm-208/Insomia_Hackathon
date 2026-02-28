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
        informal_cats    = data.get('informal_categories', ['food', 'deals'])
        manual_absences  = data.get('manual_absences', {})

        if not raw_text and not manual_absences:
            return JsonResponse({'error': 'Preference text or manual absences required'}, status=400)
        
        # Only re-interpret preferences if text is provided
        priority_profile = None
        if raw_text:
            try:
                priority_profile = interpret_preferences(raw_text)
            except Exception as ge:
                print(f'Gemini preference error (using fallback): {ge}')
                from college_data import CLUBS, FESTS
                all_codes = list(CLUBS.keys()) + list(FESTS.keys())
                priority_profile = {code: 'medium' for code in all_codes}
        else:
            # If only adjusting absences, keep existing profile
            from .models import get_preferences
            existing = get_preferences(google_id)
            priority_profile = existing.get('priority_profile') if existing else {}

        save_preferences(
            google_id=google_id, raw_text=raw_text,
            priority_profile=priority_profile,
            informals_enabled=informals, informal_categories=informal_cats,
            manual_absences=manual_absences
        )
        return JsonResponse({
            'success': True, 'priority_profile': priority_profile,
            'message': 'Preferences saved!'
        })
    except Exception as e:
        import traceback; traceback.print_exc()
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
        print(f"Fetch Error: User with google_id {google_id} not found in database.")
        return JsonResponse({'error': f'User {google_id} not found in database. Please log in again.'}, status=404)
    if not prefs:
        print(f"Fetch Error: Preferences for user {google_id} not found.")
        return JsonResponse({'error': 'Set preferences first'}, status=400)

    try:
        # 1. Fetch emails from Gmail
        try:
            emails = fetch_emails(user['token'], max_results=30)
        except Exception as ge:
            import traceback; traceback.print_exc()
            return JsonResponse({'error': f'Gmail fetch failed: {ge}'}, status=500)

        for email in emails:
            save_email(google_id, email)

        # 2. Classify with Gemini (graceful fallback per email)
        priority_profile = prefs.get('priority_profile', {})
        try:
            classifications = classify_all_emails(emails, priority_profile)
        except Exception as ce:
            print(f'Gemini classify error: {ce}')
            classifications = []

        calendar_count = 0
        notify_count   = 0

        for gmail_id, classification in classifications:
            update_email_classification(google_id, gmail_id, classification)

            # FIX: Upload EVERYTHING to calendar if it has a date, regardless of priority action
            if classification['action'] == 'add_to_calendar' or classification.get('event_date'):
                email_data = next((e for e in emails if e['gmail_id'] == gmail_id), None)
                if email_data:
                    # Try creating Google Calendar event — non-blocking
                    try:
                        result = create_calendar_event(
                            token_dict=user['token'],
                            subject=email_data['subject'],
                            summary=classification['summary'],
                            event_date=classification['event_date'],
                            colour=classification['colour']
                        )
                    except Exception:
                        result = {}
                    save_calendar_event(google_id, {
                        'gmail_id':          gmail_id,
                        'title':             email_data['subject'],
                        'summary':           classification['summary'],
                        'event_date':        classification['event_date'],
                        'event_time':        classification.get('event_time'),
                        'event_venue':       classification.get('event_venue'),
                        'registration_link': classification.get('registration_link'),
                        'organizer':         classification.get('organizer'),
                        'colour':            classification['colour'],
                        'quadrant':          classification['quadrant'],
                        'class':             classification['class'],
                        'google_event_id':   result.get('event_id'),
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
@csrf_exempt
@require_http_methods(["POST"])
@auth_required
def toggle_attendance(request):
    """Update attendance status for an event"""
    try:
        data = json.loads(request.body)
        event_id = data.get('event_id')
        attended = data.get('attended', False)
        
        if not event_id:
            return JsonResponse({'error': 'Event ID required'}, status=400)
            
        from .models import update_event_attendance
        success = update_event_attendance(request.session['google_id'], event_id, attended)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Could not update attendance'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
