from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status

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