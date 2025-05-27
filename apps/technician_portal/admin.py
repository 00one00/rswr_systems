from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Technician, Repair, UnitRepairCount, Customer

class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_email', 'get_full_name', 'phone_number', 'expertise']
    list_filter = ['expertise']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number']
    list_select_related = ['user']
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'phone_number', 'expertise')
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register-technician/', self.register_technician_view, name='register-technician'),
        ]
        return custom_urls + urls
    
    def register_technician_view(self, request):
        # This is a placeholder for your registration view
        return render(request, 'admin/register_technician.html', {})

class RepairAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'unit_number', 'technician', 'get_status_badge', 'repair_date']
    list_filter = ['queue_status', 'repair_date', 'technician']
    search_fields = ['customer__name', 'unit_number', 'damage_type', 'technician__user__username']
    readonly_fields = ['repair_date']
    date_hierarchy = 'repair_date'
    list_select_related = ['customer', 'technician', 'technician__user']
    
    def get_status_badge(self, obj):
        status_colors = {
            'REQUESTED': 'bg-secondary',
            'PENDING': 'bg-warning',
            'APPROVED': 'bg-info',
            'IN_PROGRESS': 'bg-primary',
            'COMPLETED': 'bg-success',
            'DENIED': 'bg-danger'
        }
        color = status_colors.get(obj.queue_status, 'bg-secondary')
        return format_html('<span class="badge {}">{}</span>', color, obj.get_queue_status_display())
    get_status_badge.short_description = 'Status'
    get_status_badge.admin_order_field = 'queue_status'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('technician', 'customer', 'unit_number', 'repair_date')
        }),
        ('Repair Details', {
            'fields': ('damage_type', 'description', 'queue_status')
        }),
        ('Technical Data', {
            'fields': ('drilled_before_repair', 'windshield_temperature', 'resin_viscosity'),
            'classes': ('collapse',),
        }),
    )

class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'address', 'get_primary_contact']
    search_fields = ['name', 'email', 'phone']
    
    def get_primary_contact(self, obj):
        from apps.customer_portal.models import CustomerUser
        try:
            primary = CustomerUser.objects.filter(customer=obj, is_primary_contact=True).first()
            if primary:
                return f"{primary.user.get_full_name()} ({primary.user.email})"
            return "No primary contact"
        except:
            return "Error retrieving contact"
    get_primary_contact.short_description = 'Primary Contact'

class UnitRepairCountAdmin(admin.ModelAdmin):
    list_display = ['customer', 'unit_number', 'repair_count']
    list_filter = ['customer']
    search_fields = ['customer__name', 'unit_number']

# Register the models
admin.site.register(Technician, TechnicianAdmin)
admin.site.register(Repair, RepairAdmin)
admin.site.register(UnitRepairCount, UnitRepairCountAdmin)
admin.site.register(Customer, CustomerAdmin)
