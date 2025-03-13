from rest_framework import routers
from .views import TechnicianViewSet, CustomerViewSet, RepairViewSet

router = routers.DefaultRouter()
router.register(r'technicians', TechnicianViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'repairs', RepairViewSet)

urlpatterns = router.urls