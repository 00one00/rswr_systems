"""
URL configuration for Railway deployment.
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def health_check(request):
    """Simple health check view to verify the application is running."""
    return HttpResponse("OK", content_type="text/plain")

def home(request):
    """Simple home view."""
    return HttpResponse("<h1>RSWR Systems</h1><p>Application is running on Railway.</p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', home, name='home'),
] 