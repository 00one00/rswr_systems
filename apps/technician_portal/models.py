from django.db import models
from django.contrib.auth.models import User
<<<<<<< HEAD
from django.db.models.signals import post_save
from django.dispatch import receiver
=======
>>>>>>> 7e7f4cf (Updated technician portal with repair management functionality)
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Technician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    expertise = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.expertise}"

<<<<<<< HEAD
@receiver(post_save, sender=User)
def create_technician(sender, instance, created, **kwargs):
    if created:
        Technician.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_technician(sender, instance, **kwargs):
    instance.technician.save()

=======
>>>>>>> 7e7f4cf (Updated technician portal with repair management functionality)
class Customer(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

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
        ('PENDING', 'Approval Pending'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    unit_number = models.CharField(max_length=50)
    repair_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    queue_status = models.CharField(max_length=20, choices=QUEUE_CHOICES, default='PENDING')
    damage_type = models.CharField(max_length=100)
    ai_recommendation = models.TextField(blank=True, null=True)
    drilled_before_repair = models.BooleanField(default=False)
    windshield_temperature = models.FloatField(null=True, blank=True)
    resin_viscosity = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        logger.debug(f"Saving repair: {self.id}, Status: {self.queue_status}")
        unit_repair_count, created = UnitRepairCount.objects.get_or_create(
            customer=self.customer,
            unit_number=self.unit_number
        )
        
        logger.debug(f"Unit repair count: {unit_repair_count.repair_count}")
        
        if self.queue_status == 'COMPLETED':
            if not self.pk or (self.pk and self.original_status != 'COMPLETED'):
                unit_repair_count.repair_count += 1
                unit_repair_count.save()
                logger.debug(f"Incremented repair count to: {unit_repair_count.repair_count}")
            
            self.cost = self.calculate_cost(unit_repair_count.repair_count)
            logger.debug(f"Calculated cost: {self.cost}")
        else:
            self.cost = 0
            logger.debug("Set cost to 0 for non-completed repair")

        super().save(*args, **kwargs)
        self.original_status = self.queue_status

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

class Invoice(models.Model):
    repair = models.OneToOneField(Repair, on_delete=models.CASCADE)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='UNPAID')
    generated_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.id} - Repair {self.repair.id} - {self.payment_status}"
<<<<<<< HEAD
=======

>>>>>>> 7e7f4cf (Updated technician portal with repair management functionality)
