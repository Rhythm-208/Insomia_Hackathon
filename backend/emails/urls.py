# emails/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('fetch/',              views.fetch_and_classify,      name='fetch'),
    path('',                    views.get_user_emails,         name='get_emails'),
    path('search/',             views.search_user_emails,      name='search'),
    path('preferences/',        views.save_user_preferences,   name='save_prefs'),
    path('preferences/get/',    views.get_user_preferences,    name='get_prefs'),
    path('notifications/',      views.get_notifications,       name='notifications'),
    path('notifications/seen/', views.mark_seen,               name='mark_seen'),
    path('calendar/',           views.get_user_calendar_events, name='calendar_events'),  # NEW
    path('calendar/add/',       views.add_manual_event,        name='add_event'),         # NEW
]
