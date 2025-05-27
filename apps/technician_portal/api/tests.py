from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
<<<<<<< HEAD

class TechnicianTests(APITestCase):
    def test_create_technician(self):
        url = reverse('technician-list')
        data = {
            'user': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 
=======
from django.contrib.auth.models import User
from apps.technician_portal.models import Technician

class TechnicianTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_create_technician(self):
        url = reverse('technician-list')
        data = {'user': self.user.id, 'phone_number': '1234567890', 'expertise': 'Testing'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Technician.objects.count(), 1)
        self.assertEqual(Technician.objects.get().expertise, 'Testing')
>>>>>>> 7e7f4cf (Updated technician portal with repair management functionality)
