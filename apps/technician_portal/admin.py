from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from .models import Technician, Customer, Repair

class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'expertise']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register/', self.admin_site.admin_view(self.register_technician_view),
                 name='register_technician'),
        ]
        return custom_urls + urls
    
    def register_technician_view(self, request):
        return redirect('register_technician')

admin.site.register(Technician, TechnicianAdmin)
admin.site.register(Customer)
admin.site.register(Repair)
