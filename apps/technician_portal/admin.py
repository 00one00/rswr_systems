from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.utils.html import format_html
from django import forms
from .models import Technician, Repair, UnitRepairCount, Customer

class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_email', 'get_full_name', 'phone_number', 'expertise', 'is_manager', 'is_active', 'repairs_completed']
    list_filter = ['expertise', 'is_manager', 'is_active', 'can_assign_work', 'can_override_pricing']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number']
    list_select_related = ['user']
    filter_horizontal = ['managed_technicians']

    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on manager status"""
        form = super().get_form(request, obj, **kwargs)

        # If editing an existing non-manager, hide managed_technicians field
        if obj and not obj.is_manager:
            if 'managed_technicians' in form.base_fields:
                form.base_fields['managed_technicians'].widget = forms.HiddenInput()

        # For managers, show only active technicians (exclude self)
        if 'managed_technicians' in form.base_fields:
            queryset = Technician.objects.filter(is_active=True).order_by('user__first_name')
            if obj:
                # Exclude self from managed_technicians options
                queryset = queryset.exclude(id=obj.id)
            form.base_fields['managed_technicians'].queryset = queryset
            # Use FilteredSelectMultiple for better UX with many technicians
            form.base_fields['managed_technicians'].widget = forms.widgets.FilteredSelectMultiple('Managed Technicians', False)

        return form

    def save_model(self, request, obj, form, change):
        """Validate and save technician, clearing managed_technicians for non-managers"""
        # If not a manager, clear managed technicians
        if not obj.is_manager:
            obj.managed_technicians.clear()

        super().save_model(request, obj, form, change)

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'phone_number', 'expertise', 'is_active')
        }),
        ('Manager Capabilities', {
            'fields': ('is_manager', 'approval_limit', 'can_assign_work', 'can_override_pricing', 'managed_technicians'),
            'description': 'Configure manager-level permissions and responsibilities.'
        }),
        ('Performance Metrics', {
            'fields': ('repairs_completed', 'average_repair_time', 'customer_rating'),
            'classes': ('collapse',),
            'description': 'Performance tracking data (automatically updated).'
        }),
        ('Schedule & Availability', {
            'fields': ('working_hours',),
            'classes': ('collapse',),
            'description': 'Working hours in JSON format: {"monday": ["9:00", "17:00"], ...}'
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
    list_display = ['id', 'customer', 'unit_number', 'technician', 'get_status_badge', 'get_price_display', 'repair_date']
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

    def get_price_display(self, obj):
        if obj.has_price_override():
            return format_html(
                '<span style="color: #ff6b6b;" title="Manual override: {}">${} ⚠️</span>',
                obj.override_reason or "No reason provided",
                f"{obj.cost:.2f}"
            )
        return f"${obj.cost:.2f}"
    get_price_display.short_description = 'Price'
    get_price_display.admin_order_field = 'cost'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('technician', 'customer', 'unit_number', 'repair_date')
        }),
        ('Repair Details', {
            'fields': ('damage_type', 'description', 'queue_status')
        }),
        ('Pricing', {
            'fields': ('cost', 'cost_override', 'override_reason'),
            'description': 'Cost is normally calculated automatically based on repair count. Admins can manually adjust the cost field directly, or use override fields to document custom pricing with a reason.'
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
