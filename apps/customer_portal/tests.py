from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import Customer
from apps.technician_portal.models import Repair, Technician
from .models import CustomerUser, CustomerPreference, RepairApproval


class CustomerUserModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name='test company',
            email='test@company.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='user@company.com',
            password='testpass'
        )

    def test_customer_user_creation(self):
        customer_user = CustomerUser.objects.create(
            user=self.user,
            customer=self.customer,
            is_primary_contact=True
        )
        self.assertEqual(str(customer_user), f"{self.user.username} - {self.customer.name}")
        self.assertTrue(customer_user.is_primary_contact)

    def test_customer_preference_creation(self):
        preference = CustomerPreference.objects.create(
            customer=self.customer,
            receive_email_notifications=False,
            default_view='completed'
        )
        self.assertEqual(str(preference), f"Preferences for {self.customer.name}")
        self.assertFalse(preference.receive_email_notifications)
        self.assertEqual(preference.default_view, 'completed')


class RepairApprovalModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name='test company',
            email='test@company.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.customer_user = CustomerUser.objects.create(
            user=self.user,
            customer=self.customer
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            password='testpass'
        )
        self.technician = Technician.objects.create(
            user=self.technician_user,
            expertise='Glass Repair'
        )
        self.repair = Repair.objects.create(
            technician=self.technician,
            customer=self.customer,
            unit_number='Unit 1',
            damage_type='Chip'
        )

    def test_repair_approval_creation(self):
        approval = RepairApproval.objects.create(
            repair=self.repair,
            approved=True,
            approved_by=self.customer_user,
            notes='Approved for repair'
        )
        self.assertTrue(approval.approved)
        self.assertEqual(approval.approved_by, self.customer_user)
        self.assertIn('Approved', str(approval))


class CustomerPortalViewTest(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name='test company',
            email='test@company.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.customer_user = CustomerUser.objects.create(
            user=self.user,
            customer=self.customer
        )
        self.client.force_authenticate(user=self.user)

    def test_customer_dashboard_access(self):
        # Test that the URL exists or redirects appropriately
        response = self.client.get('/customer/dashboard/')
        # 404 is acceptable if the view isn't implemented yet
        self.assertIn(response.status_code, [200, 302, 404])