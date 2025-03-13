from django.db import models
from django.contrib.auth.models import User
from core.models import Customer
from apps.technician_portal.models import Repair

class CustomerUser(models.Model):
    """Links Django User to a Customer account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    is_primary_contact = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.customer.name}"

class CustomerPreference(models.Model):
    """Stores customer preferences for the portal"""
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    receive_email_notifications = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=False)
    default_view = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending Repairs'), ('completed', 'Completed Repairs')],
        default='pending'
    )
    
    def __str__(self):
        return f"Preferences for {self.customer.name}"

class RepairApproval(models.Model):
    """Tracks customer approvals for repairs"""
    repair = models.OneToOneField(Repair, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        status = "Approved" if self.approved else "Pending"
        return f"{status} - {self.repair}"