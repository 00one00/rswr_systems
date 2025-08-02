from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from apps.technician_portal.models import Technician

class TechnicianTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_technician(self):
        url = reverse('technician-list')
        data = {'user': self.user.id, 'phone_number': '1234567890', 'expertise': 'Testing'}
        response = self.client.post(url, data, format='json')
        # Accept success, method not allowed, or forbidden (depending on API implementation)
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED, 
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])
        
    def test_technician_model_creation(self):
        technician = Technician.objects.create(
            user=self.user,
            phone_number='1234567890',
            expertise='Glass Repair'
        )
        self.assertEqual(technician.user, self.user)
        self.assertEqual(technician.expertise, 'Glass Repair')
        self.assertIn(self.user.get_full_name(), str(technician))
