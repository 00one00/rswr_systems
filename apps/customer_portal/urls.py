from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_dashboard, name='customer_dashboard'),
    path('profile/create/', views.profile_creation, name='profile_creation'),
    path('repairs/', views.customer_repairs, name='customer_repairs'),
    path('repairs/<int:repair_id>/', views.customer_repair_detail, name='customer_repair_detail'),
    path('repairs/<int:repair_id>/approve/', views.customer_repair_approve, name='customer_repair_approve'),
    path('repairs/<int:repair_id>/deny/', views.customer_repair_deny, name='customer_repair_deny'),
    path('register/', views.customer_register, name='customer_register'),
    path('company/edit/', views.edit_company, name='edit_company'),
    path('repairs/request/', views.request_repair, name='request_repair'),
    path('account/settings/', views.account_settings, name='account_settings'),
    
    # API endpoints for data visualization
    path('api/unit-repair-data/', views.unit_repair_data_api, name='unit_repair_data_api'),
    path('api/repair-cost-data/', views.repair_cost_data_api, name='repair_cost_data_api'),
]
