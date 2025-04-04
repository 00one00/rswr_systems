# URL patterns for the rewards_referrals application
#
# This file defines all URL routes for the rewards and referrals system, including:
# - Referral code management: generating and retrieving referral codes
# - Referral tracking: processing and viewing referrals
# - Reward management: checking balances, viewing available options
# - Redemption workflows: redeeming points and tracking redemption status

from django.urls import path
from . import views

urlpatterns = [
    # Referral code management
    path('generate-referral-code/', views.generate_referral_code, name='generate_referral_code'),  # Generate a new referral code
    path('referral-code/', views.referral_code, name='referral_code'),  # Get the current user's referral code
    
    # Referral tracking
    path('referral-tracking/', views.referral_tracking, name='referral_tracking'),  # Process a referral
    path('referral-history/', views.referral_history, name='referral_history'),  # View referral history
    path('referral-stats/', views.referral_stats, name='referral_stats'),  # Get statistics about referrals
    path('referral-leaderboard/', views.referral_leaderboard, name='referral_leaderboard'),  # View top referrers
    
    # Reward management
    path('reward-balance/', views.reward_balance, name='reward_balance'),  # Check current reward balance
    path('reward-options/', views.reward_options, name='reward_options'),  # View available reward options
    path('reward-history/', views.reward_history, name='reward_history'),  # View reward history
    
    # Redemption workflows
    path('redeem-reward/', views.redeem_reward, name='redeem_reward'),  # Redeem points for a reward
    
    # Main dashboards
    path('referral-rewards/', views.referral_rewards, name='referral_rewards'),  # Main rewards dashboard
    path('referral-rewards-history/', views.referral_rewards_history, name='referral_rewards_history'),  # Complete redemption history
    path('referral-rewards-balance/', views.referral_rewards_balance, name='referral_rewards_balance'),  # Detailed balance view
]
