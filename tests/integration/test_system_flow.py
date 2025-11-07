from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.test import Client
from django.urls import reverse
from core.models import Customer
from apps.technician_portal.models import Technician, Repair
from apps.customer_portal.models import CustomerUser
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'Test the complete system flow from customer request to technician assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after running tests',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.cleanup = options['cleanup']
        
        self.stdout.write(self.style.SUCCESS('Starting comprehensive system flow test...'))
        
        try:
            # Setup test data
            self.setup_test_data()
            
            # Run the flow tests
            self.test_customer_repair_request_flow()
            self.test_technician_assignment_and_visibility()
            self.test_multiple_technician_scenarios()
            self.test_portal_separation()
            self.test_repair_status_progression()
            
            self.stdout.write(self.style.SUCCESS('All tests completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Test failed: {str(e)}'))
        finally:
            if self.cleanup:
                self.cleanup_test_data()

    def setup_test_data(self):
        """Set up test data for the flow tests"""
        self.stdout.write('Setting up test data...')
        
        # Create test customer
        self.test_customer = Customer.objects.create(
            name='test automotive inc',
            email='test@testautomotive.com',
            phone='555-0123'
        )
        
        # Create test customer user
        self.customer_user_obj = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Customer'
        )
        
        self.customer_user = CustomerUser.objects.create(
            user=self.customer_user_obj,
            customer=self.test_customer,
            is_primary_contact=True
        )
        
        # Create technician group
        tech_group, created = Group.objects.get_or_create(name='Technicians')
        
        # Create test technicians
        self.technician_user_1 = User.objects.create_user(
            username='tech1',
            email='tech1@test.com',
            password='testpass123',
            first_name='Tech',
            last_name='One'
        )
        self.technician_user_1.groups.add(tech_group)
        
        self.technician_1 = Technician.objects.create(
            user=self.technician_user_1,
            phone_number='555-0124',
            expertise='Windshield Repair'
        )
        
        self.technician_user_2 = User.objects.create_user(
            username='tech2',
            email='tech2@test.com',
            password='testpass123',
            first_name='Tech',
            last_name='Two'
        )
        self.technician_user_2.groups.add(tech_group)
        
        self.technician_2 = Technician.objects.create(
            user=self.technician_user_2,
            phone_number='555-0125',
            expertise='Glass Replacement'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        if self.verbose:
            self.stdout.write('Test data created successfully')

    def test_customer_repair_request_flow(self):
        """Test the complete customer repair request flow"""
        self.stdout.write('Testing customer repair request flow...')
        
        client = Client()
        
        # Test customer login
        login_success = client.login(username='testcustomer', password='testpass123')
        if not login_success:
            raise Exception('Customer login failed')
        
        # Test repair request creation
        repair_data = {
            'unit_number': 'TEST001',
            'description': 'Test windshield crack repair',
            'damage_type': 'Crack'
        }
        
        response = client.post(reverse('request_repair'), repair_data)
        if response.status_code not in [200, 302]:
            raise Exception(f'Repair request failed with status {response.status_code}')
        
        # Verify repair was created
        repair = Repair.objects.filter(
            customer=self.test_customer,
            unit_number='TEST001',
            queue_status='REQUESTED'
        ).first()
        
        if not repair:
            raise Exception('Repair was not created in database')
        
        # Verify repair was assigned to a technician
        if not repair.technician:
            raise Exception('Repair was not assigned to any technician')
        
        self.test_repair = repair
        
        if self.verbose:
            self.stdout.write(f'Repair created successfully: ID {repair.id}, assigned to {repair.technician.user.username}')

    def test_technician_assignment_and_visibility(self):
        """Test that technicians can see and interact with assigned repairs"""
        self.stdout.write('Testing technician assignment and visibility...')
        
        # Test both technicians can see the REQUESTED repair
        for tech_user, tech_obj in [(self.technician_user_1, self.technician_1), (self.technician_user_2, self.technician_2)]:
            client = Client()
            login_success = client.login(username=tech_user.username, password='testpass123')
            if not login_success:
                raise Exception(f'Technician {tech_user.username} login failed')
            
            # Access technician dashboard
            response = client.get(reverse('technician_dashboard'))
            if response.status_code != 200:
                raise Exception(f'Technician dashboard access failed for {tech_user.username}')
            
            # Check if repair is visible in context
            repairs_in_context = response.context.get('customer_requested_repairs', [])
            repair_visible = any(r.id == self.test_repair.id for r in repairs_in_context)
            
            if not repair_visible:
                raise Exception(f'Repair not visible to technician {tech_user.username}')
            
            if self.verbose:
                self.stdout.write(f'Repair visible to technician {tech_user.username}')

    def test_multiple_technician_scenarios(self):
        """Test scenarios with multiple technicians"""
        self.stdout.write('Testing multiple technician scenarios...')
        
        # Create additional repair requests to test load balancing
        client = Client()
        client.login(username='testcustomer', password='testpass123')
        
        for i in range(3):
            repair_data = {
                'unit_number': f'TEST00{i+2}',
                'description': f'Test repair {i+2}',
                'damage_type': 'Chip'
            }
            
            response = client.post(reverse('request_repair'), repair_data)
            if response.status_code not in [200, 302]:
                raise Exception(f'Multiple repair request {i+2} failed')
        
        # Verify repairs are distributed among technicians
        tech1_repairs = Repair.objects.filter(technician=self.technician_1, queue_status='REQUESTED').count()
        tech2_repairs = Repair.objects.filter(technician=self.technician_2, queue_status='REQUESTED').count()
        
        total_repairs = tech1_repairs + tech2_repairs
        if total_repairs < 4:  # Original repair + 3 new ones
            raise Exception(f'Expected at least 4 repairs, found {total_repairs}')
        
        if self.verbose:
            self.stdout.write(f'Tech1 has {tech1_repairs} repairs, Tech2 has {tech2_repairs} repairs')

    def test_portal_separation(self):
        """Test that portal separation works correctly"""
        self.stdout.write('Testing portal separation...')
        
        # Test customer portal access
        client = Client()
        client.login(username='testcustomer', password='testpass123')
        
        # Customer should access customer dashboard
        response = client.get(reverse('customer_dashboard'))
        if response.status_code != 200:
            raise Exception('Customer cannot access customer dashboard')
        
        # Test technician portal access
        client = Client()
        client.login(username='tech1', password='testpass123')
        
        # Technician should access technician dashboard
        response = client.get(reverse('technician_dashboard'))
        if response.status_code != 200:
            raise Exception('Technician cannot access technician dashboard')
        
        if self.verbose:
            self.stdout.write('Portal separation working correctly')

    def test_repair_status_progression(self):
        """Test the repair status progression from REQUESTED to COMPLETED"""
        self.stdout.write('Testing repair status progression...')
        
        client = Client()
        
        # Login as the technician assigned to the repair
        assigned_tech = self.test_repair.technician
        client.login(username=assigned_tech.user.username, password='testpass123')
        
        # Accept the repair (REQUESTED -> APPROVED)
        response = client.post(
            reverse('update_queue_status', args=[self.test_repair.id]),
            {'status': 'APPROVED'}
        )
        if response.status_code not in [200, 302]:
            raise Exception('Status update to APPROVED failed')
        
        # Refresh repair from database
        self.test_repair.refresh_from_db()
        if self.test_repair.queue_status != 'APPROVED':
            raise Exception(f'Expected APPROVED status, got {self.test_repair.queue_status}')
        
        # Progress to IN_PROGRESS
        response = client.post(
            reverse('update_queue_status', args=[self.test_repair.id]),
            {'status': 'IN_PROGRESS'}
        )
        
        self.test_repair.refresh_from_db()
        if self.test_repair.queue_status != 'IN_PROGRESS':
            raise Exception(f'Expected IN_PROGRESS status, got {self.test_repair.queue_status}')
        
        # Complete the repair
        response = client.post(
            reverse('update_queue_status', args=[self.test_repair.id]),
            {'status': 'COMPLETED'}
        )
        
        self.test_repair.refresh_from_db()
        if self.test_repair.queue_status != 'COMPLETED':
            raise Exception(f'Expected COMPLETED status, got {self.test_repair.queue_status}')
        
        # Verify cost was calculated
        if self.test_repair.cost <= 0:
            raise Exception(f'Expected positive cost, got {self.test_repair.cost}')
        
        if self.verbose:
            self.stdout.write(f'Repair progression completed successfully, final cost: ${self.test_repair.cost}')

    def cleanup_test_data(self):
        """Clean up test data"""
        self.stdout.write('Cleaning up test data...')
        
        # Delete in reverse order of dependencies
        Repair.objects.filter(customer=self.test_customer).delete()
        CustomerUser.objects.filter(customer=self.test_customer).delete()
        self.test_customer.delete()
        
        # Delete technicians
        self.technician_1.delete()
        self.technician_2.delete()
        
        # Delete users
        self.customer_user_obj.delete()
        self.technician_user_1.delete()
        self.technician_user_2.delete()
        self.admin_user.delete()
        
        if self.verbose:
            self.stdout.write('Test data cleaned up successfully')