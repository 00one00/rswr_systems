"""
Simplified URL configuration for testing
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def simple_home(request):
    return HttpResponse("Hello from RS Systems on AWS!")

urlpatterns = [
    path('', simple_home, name='home'),
    path('admin/', admin.site.urls),
] 