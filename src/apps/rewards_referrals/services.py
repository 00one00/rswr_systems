# Service classes:
# - ReferralService (code generation, tracking)
# - RewardService (point calculation, redemption)

from django.utils import timezone
from .models import ReferralCode, Referral, Reward, RewardOption, RewardRedemption
from core.models import Customer
from apps.customer_portal.models import CustomerUser
import random
import string
from django.db.models import Sum

class ReferralService:
    @staticmethod
    def generate_referral_code(customer_user):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ReferralCode.objects.create(code=code, customer_user=customer_user)
        return code
    
    
    @staticmethod
    def track_referral(referral_code, customer_user):
        referral = Referral.objects.create(referral_code=referral_code, customer_user=customer_user)
        return referral
    
    @staticmethod
    def validate_referral_code(code):
        """
        Validate a referral code and return the ReferralCode object if valid
        """
        try:
            return ReferralCode.objects.get(code=code)
        except ReferralCode.DoesNotExist:
            return None
    
    @staticmethod
    def process_referral(referral_code_obj, customer_user):
        """
        Process a referral when a new user signs up with a referral code
        """
        # Ensure users can't refer themselves
        if referral_code_obj.customer_user == customer_user:
            return False
        
        # Check if this referral already exists
        if Referral.objects.filter(referral_code=referral_code_obj, customer_user=customer_user).exists():
            return False
        
        # Create the referral
        Referral.objects.create(
            referral_code=referral_code_obj,
            customer_user=customer_user
        )
        
        # Give points to the referrer
        referrer = referral_code_obj.customer_user
        reward, created = Reward.objects.get_or_create(customer_user=referrer)
        reward.points += 500  # Assume 500 points per referral
        reward.save()
        
        # Also give points to the referred user as a welcome bonus
        referred_reward, created = Reward.objects.get_or_create(customer_user=customer_user)
        referred_reward.points += 100  # Smaller bonus for using a referral code
        referred_reward.save()
        
        return True
    
    @staticmethod
    def get_referral_count(customer_user):
        """
        Get the number of successful referrals for a user
        """
        try:
            referral_code = ReferralCode.objects.get(customer_user=customer_user)
            return Referral.objects.filter(referral_code=referral_code).count()
        except ReferralCode.DoesNotExist:
            return 0
    
    @staticmethod
    def generate_code_for_user(customer_user, length=8):
        """
        Generate a new referral code for a user
        """
        # Check if user already has a code
        existing = ReferralCode.objects.filter(customer_user=customer_user).first()
        if existing:
            return existing
        
        # Generate a new code
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(length))
            if not ReferralCode.objects.filter(code=code).exists():
                return ReferralCode.objects.create(
                    code=code,
                    customer_user=customer_user
                )

class RewardService:
    @staticmethod
    def calculate_points(customer_user):
        # Calculate points based on customer's activity
        points = 0
        
        # Example: 1 point per completed task
        # points = Referral.objects.filter(customer_user=customer_user).count()
        return points
    
    @staticmethod
    def redeem_reward(reward):
        # Process reward redemption
        reward.redeemed = True
        reward.save()
        return reward

    @staticmethod
    def get_reward_options():
        return RewardOption.objects.all()
    
    @staticmethod
    def get_reward_redemptions(customer_user):
        return RewardRedemption.objects.filter(reward__customer_user=customer_user)
    
    @staticmethod
    def get_reward_balance(customer_user):
        """
        Get the current reward balance for a user
        """
        reward = Reward.objects.filter(customer_user=customer_user).first()
        return reward.points if reward else 0
    
    @staticmethod
    def get_reward_history(customer_user):
        return Reward.objects.filter(customer_user=customer_user).order_by('-created_at')
    
    @staticmethod
    def redeem_reward(customer_user, reward_option_id):
        """
        Redeem a reward for a user
        """
        try:
            reward_option = RewardOption.objects.get(id=reward_option_id)
            reward, created = Reward.objects.get_or_create(customer_user=customer_user)
            
            # Check if user has enough points
            if reward.points < reward_option.points_required:
                return False, f"Not enough points. You need {reward_option.points_required}, but have {reward.points}."
            
            # Create redemption record
            redemption = RewardRedemption.objects.create(
                reward=reward,
                reward_option=reward_option
            )
            
            # Deduct points
            reward.points -= reward_option.points_required
            reward.save()
            
            return True, redemption
            
        except RewardOption.DoesNotExist:
            return False, "Invalid reward option"
    
    @staticmethod
    def get_available_rewards(customer_user):
        """
        Get list of rewards the user can redeem based on their balance
        """
        reward = Reward.objects.filter(customer_user=customer_user).first()
        points = reward.points if reward else 0
        
        all_rewards = RewardOption.objects.all().order_by('points_required')
        
        result = {
            'available': [],
            'unavailable': []
        }
        
        for option in all_rewards:
            if option.points_required <= points:
                result['available'].append(option)
            else:
                result['unavailable'].append(option)
        
        return result
    
    @staticmethod
    def get_redemption_history(customer_user, limit=None):
        """
        Get reward redemption history for a user
        """
        redemptions = RewardRedemption.objects.filter(
            reward__customer_user=customer_user
        ).order_by('-created_at')
        
        if limit:
            redemptions = redemptions[:limit]
            
        return redemptions

class RewardFulfillmentService:
    @staticmethod
    def assign_technician(redemption):
        """
        Assign the most appropriate technician to fulfill a reward
        """
        from apps.technician_portal.models import Technician, Repair
        
        # Get active technicians
        technicians = Technician.objects.all()
        
        if not technicians.exists():
            return None
            
        # Simple algorithm: assign to technician with least active repairs
        technician_workloads = {}
        
        for tech in technicians:
            active_repairs = Repair.objects.filter(
                technician=tech
            ).exclude(
                queue_status__in=['COMPLETED', 'DENIED']
            ).count()
            
            technician_workloads[tech.id] = active_repairs
        
        # Find technician with minimum workload
        min_workload_tech_id = min(technician_workloads, key=technician_workloads.get)
        assigned_technician = Technician.objects.get(id=min_workload_tech_id)
        
        # Assign to redemption
        redemption.assigned_technician = assigned_technician
        redemption.save()
        
        # Send notification
        RewardFulfillmentService.notify_technician(redemption, assigned_technician)
        
        return assigned_technician
    
    @staticmethod
    def notify_technician(redemption, technician):
        """
        Send notification to technician about new reward fulfillment
        """
        # For now, we'll implement a simple notification in the DB
        # In a real system, this might send an email, SMS, or push notification
        from django.utils import timezone
        from apps.technician_portal.models import TechnicianNotification
        
        TechnicianNotification.objects.create(
            technician=technician,
            message=f"New reward redemption to fulfill: {redemption.reward_option.name} for {redemption.reward.customer_user.user.email}",
            redemption=redemption,
            created_at=timezone.now()
        )
        
    @staticmethod
    def mark_as_fulfilled(redemption, technician, notes=None):
        """
        Mark a redemption as fulfilled by a technician
        """
        from django.utils import timezone
        
        redemption.status = 'FULFILLED'
        redemption.processed_by = technician.user
        redemption.processed_at = timezone.now()
        redemption.fulfilled_at = timezone.now()
        
        if notes:
            redemption.notes = notes
            
        redemption.save()
        
        # Notify the customer (implementation will vary based on system requirements)
        # This could send an email, SMS, or update the customer dashboard
        
        return redemption
    