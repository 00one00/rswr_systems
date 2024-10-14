from rest_framework import viewsets
from apps.technician_portal.models import Technician, Repair, Customer
from .serializers import TechnicianSerializer, RepairSerializer, CustomerSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class TechnicianViewSet(viewsets.ModelViewSet):
    queryset = Technician.objects.all()
    serializer_class = TechnicianSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class RepairViewSet(viewsets.ModelViewSet):
    queryset = Repair.objects.all()
    serializer_class = RepairSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        # Associate the repair with the logged-in technician
        serializer.save(technician=self.request.user.technician)

