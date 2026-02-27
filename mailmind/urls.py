# mailmind/urls.py

from django.urls import path, include

urlpatterns = [
    path('auth/',       include('users.urls')),
    path('api/emails/', include('emails.urls')),
]
