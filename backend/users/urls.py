from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login_page'),
    path('auth/google/', views.initiate_google_auth, name='google_auth'),
    path('auth/callback/', views.oauth_callback, name='oauth_callback'),
    path('logout/', views.logout_user, name='logout'),
    path('auth/check/', views.check_auth, name='check_auth'),
    path('sync/calendar/', views.sync_google_calendar, name='sync_calendar'),
]
