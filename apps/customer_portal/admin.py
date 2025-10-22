from django.contrib import admin
from .models import CustomerUser, CustomerPreference, RepairApproval, CustomerRepairPreference
from .pricing_models import CustomerPricing

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

# Custom admin class for CustomerPricing model
class CustomerPricingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'use_custom_pricing', 'created_at', 'created_by']
    list_filter = ['use_custom_pricing', 'created_at']
    search_fields = ['customer__name', 'notes']
    list_select_related = ['customer', 'created_by']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Customer & Settings', {
            'fields': ('customer', 'use_custom_pricing', 'notes')
        }),
        ('Custom Repair Pricing', {
            'fields': ('repair_1_price', 'repair_2_price', 'repair_3_price',
                      'repair_4_price', 'repair_5_plus_price'),
            'description': 'Set custom prices for each repair tier. Leave blank to use default pricing.'
        }),
        ('Volume Discounts', {
            'fields': ('volume_discount_threshold', 'volume_discount_percentage'),
            'description': 'Configure volume discounts for high-volume customers.'
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Custom admin class for CustomerRepairPreference model
class CustomerRepairPreferenceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'field_repair_approval_mode', 'units_per_visit_threshold', 'updated_at']
    list_filter = ['field_repair_approval_mode', 'updated_at']
    search_fields = ['customer__name']
    list_select_related = ['customer']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Field Repair Approval Settings', {
            'fields': ('field_repair_approval_mode', 'units_per_visit_threshold'),
            'description': 'Configure how field-discovered repairs should be handled for this customer.'
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register the models with their custom admin classes
admin.site.register(CustomerUser, CustomerUserAdmin)
admin.site.register(CustomerPreference, CustomerPreferenceAdmin)
admin.site.register(RepairApproval, RepairApprovalAdmin)
admin.site.register(CustomerPricing, CustomerPricingAdmin)
admin.site.register(CustomerRepairPreference, CustomerRepairPreferenceAdmin) 