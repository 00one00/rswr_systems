from django.contrib import admin
from .models import CustomerUser, CustomerPreference, RepairApproval

class CustomerUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'customer', 'get_email', 'get_full_name', 'is_primary_contact']
    list_filter = ['is_primary_contact', 'customer']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'customer__name']
    list_select_related = ['user', 'customer']
    
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
            'fields': ('user', 'customer', 'is_primary_contact')
        }),
    )

class CustomerPreferenceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'receive_email_notifications', 'receive_sms_notifications', 'default_view']
    list_filter = ['receive_email_notifications', 'receive_sms_notifications', 'default_view']
    search_fields = ['customer__name']

class RepairApprovalAdmin(admin.ModelAdmin):
    list_display = ['repair', 'approved', 'approved_by', 'approval_date']
    list_filter = ['approved', 'approval_date']
    search_fields = ['repair__id', 'repair__customer__name', 'approved_by__user__username']
    readonly_fields = ['approval_date']

# Register the models with their admin classes
admin.site.register(CustomerUser, CustomerUserAdmin)
admin.site.register(CustomerPreference, CustomerPreferenceAdmin)
admin.site.register(RepairApproval, RepairApprovalAdmin) 