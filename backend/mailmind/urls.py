# mailmind/urls.py — FIXED + added debug endpoint + frontend
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from emails.views_frontend import index, health_check
import json

# Debug login — ONLY for development with seeded data
@csrf_exempt
def debug_login(request):
    """DEV ONLY: sets session to seeded test user so you can test without OAuth"""
    import os
    if os.getenv('DEBUG', 'True') != 'True':
        return JsonResponse({'error': 'Only available in DEBUG mode'}, status=403)
    request.session['google_id'] = 'test_user_001'
    request.session['email']     = 'testuser@iitj.ac.in'
    request.session['name']      = 'Shreshth Dhimole'
    return JsonResponse({'success': True, 'message': 'Logged in as test user'})

urlpatterns = [
    path('login/',       index),            # Login page
    path('auth/',        include('users.urls')),
    path('api/emails/',  include('emails.urls')),
    path('api/debug/login/', debug_login),  # DEV ONLY
    path('api/health/',  health_check),     # Health check
    path('',             index),            # Serve frontend
]
