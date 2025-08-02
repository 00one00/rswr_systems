from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import Customer
from apps.technician_portal.models import Technician
from apps.customer_portal.models import CustomerUser


class Command(BaseCommand):
    help = 'Create test data for manual testing of the repair system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.clean_test_data()
        
        self.stdout.write(self.style.SUCCESS('Creating test data for repair system...'))
        
        # Create technician group
        tech_group, created = Group.objects.get_or_create(name='Technicians')
        if created:
            self.stdout.write('Created Technicians group')
        
        # Create test customer
        customer, created = Customer.objects.get_or_create(
            email='demo@example.com',
            defaults={
                'name': 'demo fleet services',
                'phone': '555-0100',
                'address': '123 Demo Street',
                'city': 'Demo City',
                'state': 'CA',
                'zip_code': '90210'
            }
        )
        if created:
            self.stdout.write(f'Created customer: {customer.name}')
        
        # Create customer user
        customer_user_obj, created = User.objects.get_or_create(
            username='democustomer',
            defaults={
                'email': 'customer@demo.com',
                'first_name': 'Demo',
                'last_name': 'Customer',
                'is_active': True
            }
        )
        if created:
            customer_user_obj.set_password('demo123')
            customer_user_obj.save()
            self.stdout.write(f'Created customer user: {customer_user_obj.username}')
        
        customer_user, created = CustomerUser.objects.get_or_create(
            user=customer_user_obj,
            defaults={
                'customer': customer,
                'is_primary_contact': True
            }
        )
        if created:
            self.stdout.write(f'Created customer profile for: {customer_user_obj.username}')
        
        # Create technicians
        tech_data = [
            {
                'username': 'tech1',
                'email': 'tech1@demo.com',
                'first_name': 'John',
                'last_name': 'Technician',
                'phone': '555-0101',
                'expertise': 'Windshield Repair'
            },
            {
                'username': 'tech2',
                'email': 'tech2@demo.com',
                'first_name': 'Jane',
                'last_name': 'Specialist',
                'phone': '555-0102',
                'expertise': 'Glass Replacement'
            },
            {
                'username': 'tech3',
                'email': 'tech3@demo.com',
                'first_name': 'Mike',
                'last_name': 'Expert',
                'phone': '555-0103',
                'expertise': 'Advanced Repairs'
            }
        ]
        
        for data in tech_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_active': True
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
                user.groups.add(tech_group)
                self.stdout.write(f'Created technician user: {user.username}')
            
            technician, created = Technician.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': data['phone'],
                    'expertise': data['expertise']
                }
            )
            if created:
                self.stdout.write(f'Created technician profile for: {user.username}')
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='demoadmin',
            defaults={
                'email': 'admin@demo.com',
                'first_name': 'Demo',
                'last_name': 'Admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('demo123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.username}')
        
        self.stdout.write(self.style.SUCCESS('\nTest data created successfully!'))
        self.stdout.write('\n=== TEST ACCOUNTS ===')
        self.stdout.write('Customer Portal:')
        self.stdout.write('  Username: democustomer')
        self.stdout.write('  Password: demo123')
        self.stdout.write('  URL: /app/login/')
        self.stdout.write('\nTechnician Portal:')
        self.stdout.write('  Username: tech1, tech2, or tech3')
        self.stdout.write('  Password: demo123')
        self.stdout.write('  URL: /tech/login/')
        self.stdout.write('\nAdmin Access:')
        self.stdout.write('  Username: demoadmin')
        self.stdout.write('  Password: demo123')
        self.stdout.write('  URL: /admin/')
        self.stdout.write('\n=== TESTING STEPS ===')
        self.stdout.write('1. Login as democustomer at /app/login/')
        self.stdout.write('2. Request a repair for unit "FLEET001"')
        self.stdout.write('3. Login as tech1 at /tech/login/')
        self.stdout.write('4. Check that the repair appears in your dashboard')
        self.stdout.write('5. Accept and progress the repair through all statuses')

    def clean_test_data(self):
        """Clean up existing test data"""
        self.stdout.write('Cleaning existing test data...')
        
        # Delete test users (this will cascade to related objects)
        test_usernames = ['democustomer', 'tech1', 'tech2', 'tech3', 'demoadmin']
        for username in test_usernames:
            try:
                user = User.objects.get(username=username)
                user.delete()
                self.stdout.write(f'Deleted user: {username}')
            except User.DoesNotExist:
                pass
        
        # Delete test customer
        try:
            customer = Customer.objects.get(email='demo@example.com')
            customer.delete()
            self.stdout.write('Deleted test customer')
        except Customer.DoesNotExist:
            pass