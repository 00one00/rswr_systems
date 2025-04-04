# Core models needed:
# - ReferralCode (linked to CustomerUser)
# - Referral (tracking successful referrals)
# - Reward (point balance for customers)
# - RewardOption (available redemption options)
# - RewardRedemption (tracking redemptions)

from django.db import models
from apps.customer_portal.models import CustomerUser

class ReferralCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    customer_user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.code
    
class Referral(models.Model):
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE)
    customer_user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class RewardType(models.Model):
    """Type of reward and how it should be applied"""
    REWARD_CATEGORY_CHOICES = [
        ('REPAIR_DISCOUNT', 'Repair Discount'),
        ('REPLACEMENT_DISCOUNT', 'Replacement Discount'),
        ('FREE_SERVICE', 'Free Service'),
        ('MERCHANDISE', 'Merchandise'),
        ('GIFT_CARD', 'Gift Card'),
        ('OTHER', 'Other'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED_AMOUNT', 'Fixed Amount Discount'),
        ('FREE', 'Free (100% Off)'),
        ('NONE', 'No Discount'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=REWARD_CATEGORY_CHOICES)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='NONE')
    discount_value = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                       help_text="Percentage or fixed amount, depending on discount type")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        if self.discount_type == 'PERCENTAGE':
            return f"{self.name} - {self.discount_value}% off"
        elif self.discount_type == 'FIXED_AMOUNT':
            return f"{self.name} - ${self.discount_value} off"
        elif self.discount_type == 'FREE':
            return f"{self.name} - Free"
        else:
            return self.name

class Reward(models.Model):
    customer_user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.customer_user.user.email} - {self.points} points"
    
class RewardOption(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    reward_type = models.ForeignKey(RewardType, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['points_required']

    def __str__(self):
        return f"{self.name} ({self.points_required} points)"
    
class RewardRedemption(models.Model):
    REDEMPTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('FULFILLED', 'Fulfilled'),
        ('REJECTED', 'Rejected'),
    ]
    
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    reward_option = models.ForeignKey(RewardOption, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=REDEMPTION_STATUS_CHOICES,
        default='PENDING'
    )
    notes = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_redemptions'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    assigned_technician = models.ForeignKey(
        'technician_portal.Technician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_redemptions'
    )
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    applied_to_repair = models.ForeignKey('technician_portal.Repair', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='applied_rewards')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reward.customer_user.user.email} - {self.reward_option.name} ({self.status})"
    
