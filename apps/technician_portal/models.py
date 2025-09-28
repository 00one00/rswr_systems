from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from core.models import Customer

class Technician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    expertise = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.expertise}"

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
        indexes = [
            models.Index(fields=['customer', 'unit_number']),
            models.Index(fields=['repair_count']),
        ]

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
    
    DAMAGE_TYPE_CHOICES = [
        ('', 'Unknown / Not Sure'),
        ('Chip', 'Chip'),
        ('Crack', 'Crack'),
        ('Star Break', 'Star Break'),
        ('Bull\'s Eye', 'Bull\'s Eye'),
        ('Combination Break', 'Combination Break'),
        ('Other', 'Other'),
    ]

    technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    unit_number = models.CharField(max_length=50)
    repair_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manual price override (overrides automatic pricing)"
    )
    override_reason = models.TextField(
        blank=True,
        help_text="Reason for price override (required when using custom price)"
    )
    queue_status = models.CharField(max_length=20, choices=QUEUE_CHOICES, default='PENDING')
    damage_type = models.CharField(max_length=100, choices=DAMAGE_TYPE_CHOICES, default='')
    drilled_before_repair = models.BooleanField(default=False)
    windshield_temperature = models.FloatField(null=True, blank=True)
    resin_viscosity = models.CharField(max_length=50, blank=True)
    
    # Photo documentation fields
    damage_photo_before = models.ImageField(
        upload_to='repair_photos/before/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        help_text="Photo of damage before repair"
    )
    damage_photo_after = models.ImageField(
        upload_to='repair_photos/after/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        help_text="Photo of repair after completion"
    )
    additional_photos = models.JSONField(
        default=list, 
        blank=True,
        help_text="Additional photos related to the repair (stored as list of URLs)"
    )
    
    # Separate notes fields for better organization
    customer_notes = models.TextField(
        blank=True,
        help_text="Notes provided by the customer during repair request or approval process"
    )
    technician_notes = models.TextField(
        blank=True,
        help_text="Internal notes added by technicians during repair process"
    )

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

                # Use override price if provided, otherwise calculate normally
                if self.cost_override is not None:
                    self.cost = self.cost_override
                else:
                    self.cost = self.calculate_cost(unit_repair_count.repair_count)

                # Check for available rewards to apply automatically
                self.apply_available_rewards()

                # Award points to customer for completed repair
                self.award_completion_points()
            else:
                # Keep any override even when not completed (for preview purposes)
                if self.cost_override is None:
                    self.cost = 0
                
            # Save after the cost calculation
            super().save(*args, **kwargs)
            
            # Update the original status after saving
            self.original_status = self.queue_status
        else:
            # Just save without updating repair counts
            super().save(*args, **kwargs)

    def apply_available_rewards(self):
        """
        Automatically apply any available rewards to this repair.
        
        Searches for pending reward redemptions associated with the repair's customer
        and automatically applies the oldest redemption to this repair. If the repair
        is being completed, the reward is also automatically fulfilled.
        
        This method is called during the repair save process when status changes to COMPLETED.
        """
        try:
            from apps.rewards_referrals.models import RewardRedemption
            from apps.customer_portal.models import CustomerUser
            
            # Check if there's already a reward applied to this repair
            if self.applied_rewards.exists():
                return
            
            # Find the customer user associated with this repair
            customer_users = CustomerUser.objects.filter(customer=self.customer)
            
            if not customer_users.exists():
                return
                
            # Check for pending reward redemptions that can be applied to repairs
            # Only include rewards that are repair-related (not merchandise like donuts/pizza)
            pending_redemptions = RewardRedemption.objects.filter(
                reward__customer_user__in=customer_users,
                status='PENDING',
                applied_to_repair__isnull=True,  # Not already applied to another repair
                reward_option__reward_type__category__in=[
                    'REPAIR_DISCOUNT', 
                    'FREE_SERVICE'
                ]  # Only auto-apply repair-related rewards, NOT merchandise like donuts/pizza
            ).order_by('created_at')
            
            # Apply the oldest pending redemption to this repair
            if pending_redemptions.exists():
                redemption = pending_redemptions.first()
                redemption.applied_to_repair = self
                
                # If there's a technician on the repair, assign them
                if not redemption.assigned_technician and hasattr(self, 'technician'):
                    redemption.assigned_technician = self.technician
                
                redemption.save()
                
                # Automatically mark as fulfilled if completing the repair
                if self.queue_status == 'COMPLETED':
                    from apps.rewards_referrals.services import RewardFulfillmentService
                    RewardFulfillmentService.mark_as_fulfilled(
                        redemption, 
                        self.technician, 
                        "Automatically applied when repair was completed"
                    )
        except Exception as e:
            # Log the error but don't fail the save
            print(f"Error auto-applying rewards: {e}")
    
    def award_completion_points(self):
        """
        Award points to customer when repair is completed.
        
        Awards base points per repair plus milestone bonuses for multiple repairs.
        Only awards points once per repair completion to prevent duplicate awards.
        """
        try:
            from apps.rewards_referrals.models import Reward
            from apps.customer_portal.models import CustomerUser
            
            # Skip if already awarded points for this repair (check if this is a status change to COMPLETED)
            if hasattr(self, 'original_status') and self.original_status == 'COMPLETED':
                return
            
            # Find the customer user associated with this repair
            customer_users = CustomerUser.objects.filter(customer=self.customer)
            
            if not customer_users.exists():
                return
                
            customer_user = customer_users.first()
            
            # Get or create reward record for this customer
            reward, created = Reward.objects.get_or_create(
                customer_user=customer_user,
                defaults={'points': 0}
            )
            
            # Base points per repair completion
            base_points = 50
            
            # Calculate milestone bonus based on total completed repairs for this customer
            completed_repairs_count = Repair.objects.filter(
                customer=self.customer,
                queue_status='COMPLETED'
            ).count()
            
            milestone_bonus = 0
            if completed_repairs_count == 5:
                milestone_bonus = 250  # 5th repair bonus
            elif completed_repairs_count == 10:
                milestone_bonus = 500  # 10th repair bonus
            elif completed_repairs_count % 25 == 0:  # Every 25th repair
                milestone_bonus = 1000
            
            total_points = base_points + milestone_bonus
            
            # Award the points
            reward.points += total_points
            reward.save()
            
            # Create a notification about the points earned (you could add this to a notifications system later)
            print(f"Awarded {total_points} points to {customer_user.user.email} for repair completion")
            if milestone_bonus > 0:
                print(f"Milestone bonus of {milestone_bonus} points awarded!")
                
        except Exception as e:
            # Log the error but don't fail the save
            print(f"Error awarding completion points: {e}")

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
            
    def get_discounted_cost(self):
        """Calculate the final cost with any applied rewards/discounts"""
        from decimal import Decimal
        
        # Start with the base cost
        base_cost = self.cost
        final_cost = base_cost
        discount_applied = False
        discount_description = ""
        
        # Check for any applied rewards - include both FULFILLED and PENDING rewards
        applied_rewards = self.applied_rewards.filter(status__in=['FULFILLED', 'PENDING'])
        
        for redemption in applied_rewards:
            if redemption.reward_option.reward_type:
                reward_type = redemption.reward_option.reward_type
                
                # Apply discount based on the reward type
                if reward_type.discount_type == 'PERCENTAGE':
                    # Percentage discount
                    discount_amount = (base_cost * Decimal(reward_type.discount_value)) / Decimal(100)
                    final_cost = base_cost - discount_amount
                    discount_description = f"{reward_type.discount_value}% off"
                    discount_applied = True
                    
                elif reward_type.discount_type == 'FIXED_AMOUNT':
                    # Fixed amount discount
                    discount_amount = Decimal(reward_type.discount_value)
                    final_cost = max(base_cost - discount_amount, Decimal(0))
                    discount_description = f"${reward_type.discount_value} off"
                    discount_applied = True
                    
                elif reward_type.discount_type == 'FREE':
                    # Free (100% off)
                    final_cost = Decimal(0)
                    discount_description = "Free repair"
                    discount_applied = True
                    
                # Only apply one discount (the first one found)
                break
        
        return {
            'original_cost': base_cost,
            'final_cost': final_cost,
            'discount_applied': discount_applied,
            'discount_description': discount_description,
            'savings': base_cost - final_cost
        }

    def get_expected_price(self):
        """Get the expected price before completion (for preview purposes)"""
        # If override is set, return that
        if self.cost_override is not None:
            return self.cost_override

        # Otherwise calculate based on repair count
        if self.customer:
            unit_repair_count, _ = UnitRepairCount.objects.get_or_create(
                customer=self.customer,
                unit_number=self.unit_number,
                defaults={'repair_count': 0}
            )
            # Add 1 to count since this will be the next repair when completed
            next_count = unit_repair_count.repair_count + 1
            return self.calculate_cost(next_count)
        return 0

    def has_price_override(self):
        """Check if this repair has a manual price override"""
        return self.cost_override is not None

    class Meta:
        ordering = ['-repair_date']
        indexes = [
            models.Index(fields=['queue_status']),
            models.Index(fields=['customer', 'unit_number']),
            models.Index(fields=['technician']),
            models.Index(fields=['repair_date']),
        ]

    def __str__(self):
        return f"Repair {self.id} - {self.customer.name} - Unit #{self.unit_number} - {self.repair_date.strftime('%Y-%m-%d')} - {self.queue_status}"

    def apply_reward(self, redemption, technician=None, auto_fulfill=False):
        """Manually apply a reward to this repair"""
        if redemption.applied_to_repair:
            # This reward is already applied to a repair
            return False, "This reward is already applied to another repair"
        
        # Check if this is a merchandise reward that should not be applied to repairs
        if redemption.reward_option.reward_type and redemption.reward_option.reward_type.category == 'MERCHANDISE':
            return False, "Merchandise rewards (like donuts and pizza) cannot be applied to repair costs. These are fulfilled separately by technicians."
        
        # Apply the reward to this repair
        redemption.applied_to_repair = self
        
        # Update technician if provided
        if technician and not redemption.assigned_technician:
            redemption.assigned_technician = technician
            
        redemption.save()
        
        # Auto-fulfill if requested and repair is completed
        if auto_fulfill and self.queue_status == 'COMPLETED':
            from apps.rewards_referrals.services import RewardFulfillmentService
            RewardFulfillmentService.mark_as_fulfilled(
                redemption, 
                technician or self.technician, 
                "Applied and fulfilled by technician"
            )
            
        return True, "Reward successfully applied to repair"
    
    def has_photos(self):
        """
        Check if this repair has any associated photos.
        
        Returns:
            bool: True if repair has before or after photos, False otherwise
        """
        return bool(self.damage_photo_before or self.damage_photo_after)
    
    def get_photo_count(self):
        """
        Get the total number of photos associated with this repair.
        
        Returns:
            int: Number of photos (before + after + additional)
        """
        count = 0
        if self.damage_photo_before:
            count += 1
        if self.damage_photo_after:
            count += 1
        if self.additional_photos:
            count += len(self.additional_photos)
        return count

class TechnicianNotification(models.Model):
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    redemption = models.ForeignKey('rewards_referrals.RewardRedemption', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Notification for {self.technician.user.username}: {self.message[:30]}..."
    
    class Meta:
        ordering = ['-created_at']

