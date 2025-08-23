from django.urls import path
from . import views

urlpatterns = [
    # Main customer portal entry points
    path('', views.customer_dashboard, name='customer_dashboard'),  # /app/ now goes directly to dashboard
    path('dashboard/', views.customer_dashboard, name='customer_dashboard_alt'),  # alternative URL
    
    # User onboarding and registration
    path('register/', views.customer_register, name='customer_register'),
    path('profile/create/', views.profile_creation, name='profile_creation'),
    
    # Repairs management
    path('repairs/', views.customer_repairs, name='customer_repairs'),
    path('repairs/<int:repair_id>/', views.customer_repair_detail, name='customer_repair_detail'),
    path('repairs/<int:repair_id>/approve/', views.customer_repair_approve, name='customer_repair_approve'),
    path('repairs/<int:repair_id>/deny/', views.customer_repair_deny, name='customer_repair_deny'),
    path('repairs/request/', views.request_repair, name='customer_request_repair'),
    
    # Company and account management
    path('company/edit/', views.edit_company, name='edit_company'),
    path('account/settings/', views.account_settings, name='customer_account_settings'),
    
    # Rewards and referrals dashboard
    path('rewards/', views.customer_rewards_redirect, name='customer_rewards'),
    
    # API endpoints for data visualization
    path('api/unit-repair-data/', views.unit_repair_data_api, name='unit_repair_data_api'),
    path('api/repair-cost-data/', views.repair_cost_data_api, name='repair_cost_data_api'),
]
