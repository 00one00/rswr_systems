from django.urls import path
from . import views

urlpatterns = [
    # Main technician portal entry points
    path('', views.technician_dashboard, name='technician_dashboard'),  # /tech/ now goes directly to dashboard
    path('dashboard/', views.technician_dashboard, name='technician_dashboard_alt'),  # alternative URL
    
    # Technician profile management
    path('profile/', views.update_technician_profile, name='technician_profile'),
    
    # Repair management
    path('repairs/', views.repair_list, name='repair_list'),
    path('repairs/assigned/', views.repair_list, name='assigned_repairs'),
    path('repairs/<int:repair_id>/', views.repair_detail, name='repair_detail'),
    path('repairs/<int:repair_id>/apply-reward/', views.apply_reward_to_repair, name='apply_reward_to_repair'),
    path('repairs/create/', views.create_repair, name='create_repair'),
    path('repairs/<int:repair_id>/update/', views.update_repair, name='update_repair'),
    path('repairs/<int:repair_id>/update-status/', views.update_queue_status, name='update_queue_status'),
    path('check-existing-repair/', views.check_existing_repair, name='check_existing_repair'),
    
    # Customer management
    path('customers/', views.customer_list, name='technician_customers'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('customers/<int:customer_id>/', views.customer_details, name='customer_detail'),
    path('customers/<int:customer_id>/units/<str:unit_number>/', views.unit_details, name='unit_details'),
    path('customers/<int:customer_id>/units/<str:unit_number>/replace/', views.mark_unit_replaced, name='mark_unit_replaced'),
    
    # Rewards and notifications
    path('reward-fulfillment/<int:redemption_id>/', views.reward_fulfillment_detail, name='reward_fulfillment_detail'),
    path('notification/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
