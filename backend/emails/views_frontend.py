from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import os

def index(request):
    """Serve the main frontend application"""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
    try:
        with open(frontend_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("Frontend not found. Please ensure index.html exists in the frontend directory.", status=500)

@csrf_exempt
def health_check(request):
    """Simple health check endpoint"""
    return HttpResponse("MailMind Backend is running", status=200)