from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('repairs/', views.repair_list, name='repair_list'),
    path('repairs/<int:repair_id>/', views.repair_detail, name='repair_detail'),
    path('repairs/create/', views.create_repair, name='create_repair'),
    path('repairs/<int:repair_id>/update/', views.update_repair, name='update_repair'),
    path('repairs/<int:repair_id>/update-status/', views.update_queue_status, name='update_queue_status'),
    path('create_customer/', views.create_customer, name='create_customer'),
    path('customers/<int:customer_id>/', views.customer_details, name='customer_details'),
    path('customers/<int:customer_id>/units/<str:unit_number>/', views.unit_details, name='unit_details'),
    path('customers/<int:customer_id>/units/<str:unit_number>/replace/', views.mark_unit_replaced, name='mark_unit_replaced'),
    path('check-existing-repair/', views.check_existing_repair, name='check_existing_repair'),
]
