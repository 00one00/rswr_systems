# URL patterns for:
# - Referral code management
# - Referral tracking
# - Reward balance and history
# - Redemption workflows

from django.urls import path
from . import views

urlpatterns = [
    # Referral code management
    path('generate-referral-code/', views.generate_referral_code, name='generate_referral_code'),
    path('redeem-reward/', views.redeem_reward, name='redeem_reward'),
    path('reward-history/', views.reward_history, name='reward_history'),
    path('reward-balance/', views.reward_balance, name='reward_balance'),
    path('reward-options/', views.reward_options, name='reward_options'),
    path('referral-tracking/', views.referral_tracking, name='referral_tracking'),
    path('referral-code/', views.referral_code, name='referral_code'),
    path('referral-history/', views.referral_history, name='referral_history'),
    path('referral-stats/', views.referral_stats, name='referral_stats'),
    path('referral-leaderboard/', views.referral_leaderboard, name='referral_leaderboard'),
    path('referral-rewards/', views.referral_rewards, name='referral_rewards'),
    path('referral-rewards-history/', views.referral_rewards_history, name='referral_rewards_history'),
    path('referral-rewards-balance/', views.referral_rewards_balance, name='referral_rewards_balance'),
]
