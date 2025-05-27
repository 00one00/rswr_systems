from rest_framework import serializers
from apps.technician_portal.models import Technician, Repair
from core.models import Customer

class TechnicianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technician
        fields = ['id', 'user', 'first_name', 'last_name', 'email'] 

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'address', 'city', 'state', 'zip_code']

class RepairSerializer(serializers.ModelSerializer):
    class Meta:
        technician = TechnicianSerializer(read_only=True)
        customer = CustomerSerializer(read_only=True)
        fields = ['id', 'technician', 'customer', 'description', 'status', 'created_at', 'updated_at']