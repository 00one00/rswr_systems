from django.apps import AppConfig


class RewardsReferralsConfig(AppConfig):
    """
    Configuration for the Rewards and Referrals app.
    
    This app provides a complete referral and rewards system that enables customers to:
    - Generate unique referral codes to share with others
    - Earn points when new customers sign up using their code
    - Redeem points for various rewards including discounts and services
    - Track their referrals and reward redemptions
    
    The system also provides tools for technicians to fulfill reward redemptions.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rewards_referrals'
    verbose_name = 'Rewards & Referrals' 