# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/',    views.login,        name='login'),
    path('callback/', views.callback,     name='callback'),
    path('profile/',  views.save_profile, name='save_profile'),
    path('me/',       views.me,           name='me'),
    path('logout/',   views.logout,       name='logout'),
]
