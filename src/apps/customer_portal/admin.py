from django.contrib import admin
from .models import CustomerUser, CustomerPreference, RepairApproval

# Custom admin class for CustomerUser model
class CustomerUserAdmin(admin.ModelAdmin):
    # Define the fields to display in the list view
    list_display = ['user', 'customer', 'get_email', 'get_full_name', 'is_primary_contact']
    # Define the fields to filter by in the list view
    list_filter = ['is_primary_contact', 'customer']
    # Define the fields to search by in the list view
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'customer__name']
    # Select related fields to improve performance
    list_select_related = ['user', 'customer']
    
    # Method to display the user's email in the list view
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'  # Column header in the list view
    get_email.admin_order_field = 'user__email'  # Field to order by
    
    # Method to display the user's full name in the list view
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'  # Column header in the list view
    get_full_name.admin_order_field = 'user__first_name'  # Field to order by
    
    # Define the layout of the form in the detail view
    fieldsets = (
        (None, {
            'fields': ('user', 'customer', 'is_primary_contact')
        }),
    )

# Custom admin class for CustomerPreference model
class CustomerPreferenceAdmin(admin.ModelAdmin):
    # Define the fields to display in the list view
    list_display = ['customer', 'receive_email_notifications', 'receive_sms_notifications', 'default_view']
    # Define the fields to filter by in the list view
    list_filter = ['receive_email_notifications', 'receive_sms_notifications', 'default_view']
    # Define the fields to search by in the list view
    search_fields = ['customer__name']

# Custom admin class for RepairApproval model
class RepairApprovalAdmin(admin.ModelAdmin):
    # Define the fields to display in the list view
    list_display = ['repair', 'approved', 'approved_by', 'approval_date']
    # Define the fields to filter by in the list view
    list_filter = ['approved', 'approval_date']
    # Define the fields to search by in the list view
    search_fields = ['repair__id', 'repair__customer__name', 'approved_by__user__username']
    # Make the approval_date field read-only
    readonly_fields = ['approval_date']

# Register the models with their custom admin classes
admin.site.register(CustomerUser, CustomerUserAdmin)
admin.site.register(CustomerPreference, CustomerPreferenceAdmin)
admin.site.register(RepairApproval, RepairApprovalAdmin) 