from django.contrib import admin
from django.utils import timezone
from .models import ReferralCode, Referral, Reward, RewardOption, RewardRedemption, RewardType

@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'get_customer_email', 
        'reward_option', 
        'status', 
        'assigned_technician',
        'get_applied_to_repair',
        'created_at', 
        'processed_at'
    ]
    list_filter = ['status', 'assigned_technician', 'created_at']
    search_fields = [
        'reward__customer_user__user__email',
        'reward_option__name',
        'notes'
    ]
    raw_id_fields = ['reward', 'reward_option', 'processed_by', 'assigned_technician', 'applied_to_repair']
    
    def get_customer_email(self, obj):
        return obj.reward.customer_user.user.email
    get_customer_email.short_description = 'Customer'
    get_customer_email.admin_order_field = 'reward__customer_user__user__email'
    
    def get_applied_to_repair(self, obj):
        if obj.applied_to_repair:
            return f"Unit #{obj.applied_to_repair.unit_number} - {obj.applied_to_repair.damage_type}"
        return "Not applied"
    get_applied_to_repair.short_description = 'Applied To Repair'
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # If status is being changed, record who processed it
            if obj.status in ['COMPLETED', 'CANCELLED']:
                obj.processed_by = request.user
                obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(RewardOption)
class RewardOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_required', 'get_reward_type', 'is_active']
    list_filter = ['is_active', 'reward_type__category']
    search_fields = ['name', 'description']
    list_editable = ['points_required', 'is_active']
    
    def get_reward_type(self, obj):
        return obj.reward_type.name if obj.reward_type else "No Type"
    get_reward_type.short_description = 'Reward Type'
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'points_required', 'is_active']
        }),
        ('Reward Type', {
            'fields': ['reward_type']
        }),
    ]

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'points']
    search_fields = ['customer_user__user__email']
    
    def customer_email(self, obj):
        return obj.customer_user.user.email
    customer_email.short_description = 'Customer'

@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_email', 'created_at']
    search_fields = ['code', 'customer_user__user__email']
    readonly_fields = ['created_at']
    
    def customer_email(self, obj):
        return obj.customer_user.user.email
    customer_email.short_description = 'Customer'

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer_email', 'referred_email', 'created_at']
    search_fields = ['referral_code__customer_user__user__email', 'customer_user__user__email']
    readonly_fields = ['created_at']
    
    def referrer_email(self, obj):
        return obj.referral_code.customer_user.user.email
    referrer_email.short_description = 'Referrer'
    
    def referred_email(self, obj):
        return obj.customer_user.user.email
    referred_email.short_description = 'Referred User'

@admin.register(RewardType)
class RewardTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'discount_type', 'discount_value', 'is_active']
    list_filter = ['category', 'discount_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['discount_value', 'is_active']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'is_active']
        }),
        ('Reward Classification', {
            'fields': ['category']
        }),
        ('Discount Details', {
            'fields': ['discount_type', 'discount_value']
        }),
    ] 