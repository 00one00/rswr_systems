from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.models import Customer

class Technician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    expertise = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.expertise}"

    @receiver(post_save, sender=User)
    def create_technician(sender, instance, created, **kwargs):
        # We don't want to automatically create a technician profile for every user anymore
        # Admin users and customer users shouldn't automatically get technician profiles
        pass

    @receiver(post_save, sender=User)
    def save_technician(sender, instance, **kwargs):
        # Only save the technician if it exists
        if hasattr(instance, 'technician'):
            instance.technician.save()

class UnitRepairCount(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=50)
    repair_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['customer', 'unit_number']

    def __str__(self):
        return f"{self.customer.name} - Unit #{self.unit_number} - Repairs: {self.repair_count}"

class Repair(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_status = self.queue_status
        
    QUEUE_CHOICES = [
        ('REQUESTED', 'Customer Requested'),
        ('PENDING', 'Approval Pending'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DENIED', 'Denied by Customer'),
    ]

    technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    unit_number = models.CharField(max_length=50)
    repair_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    queue_status = models.CharField(max_length=20, choices=QUEUE_CHOICES, default='PENDING')
    damage_type = models.CharField(max_length=100)
    drilled_before_repair = models.BooleanField(default=False)
    windshield_temperature = models.FloatField(null=True, blank=True)
    resin_viscosity = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        # Ensure we have a customer before trying to access UnitRepairCount
        if self.customer:
            # Get or create the unit repair count
            unit_repair_count, created = UnitRepairCount.objects.get_or_create(
                customer=self.customer,
                unit_number=self.unit_number,
                defaults={'repair_count': 0}
            )
            
            # Handle completed repairs
            if self.queue_status == 'COMPLETED':
                if not self.pk or (self.pk and self.original_status != 'COMPLETED'):
                    unit_repair_count.repair_count += 1
                    unit_repair_count.save()
                
                self.cost = self.calculate_cost(unit_repair_count.repair_count)
            else:
                self.cost = 0
                
            # Save after the cost calculation
            super().save(*args, **kwargs)
            
            # Update the original status after saving
            self.original_status = self.queue_status
        else:
            # Just save without updating repair counts
            super().save(*args, **kwargs)

    @staticmethod
    def calculate_cost(repair_count):
        if repair_count == 1:
            return 50
        elif repair_count == 2:
            return 40
        elif repair_count == 3:
            return 35
        elif repair_count == 4:
            return 30
        else:
            return 25

    def __str__(self):
        return f"Repair {self.id} - {self.customer.name} - Unit #{self.unit_number} - {self.repair_date.strftime('%Y-%m-%d')} - {self.queue_status}"

