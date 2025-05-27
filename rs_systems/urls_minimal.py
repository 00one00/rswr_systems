"""
Minimal URL configuration for testing deployment.
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("RS Systems - Django Application is Running!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
] 