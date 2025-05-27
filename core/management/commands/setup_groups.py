from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from apps.technician_portal.models import Technician

class Command(BaseCommand):
    help = 'Create default groups and permissions and admin user'

    def handle(self, *args, **options):
        # Create Technicians group if it doesn't exist
        technicians_group, created = Group.objects.get_or_create(name='Technicians')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created Technicians group'))
        else:
            self.stdout.write('Technicians group already exists')
            
        # Create admin user if doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                password='123',
                email='',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully created admin user'))
        else:
            admin_user = User.objects.get(username='admin')
            self.stdout.write('Admin user already exists')
            
            # Make sure admin has proper privileges
            if not admin_user.is_staff or not admin_user.is_superuser:
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save()
                self.stdout.write(self.style.SUCCESS('Updated admin privileges'))

        # Create a main technician manager user
        if not User.objects.filter(username='johndoe').exists():
            tech_user = User.objects.create_user(
                username='johndoe',
                password='123',
                email='tech@example.com',
                first_name='John',
                last_name='Doe'
            )
            
            # Add user to technicians group
            tech_user.groups.add(technicians_group)
            
            # Create technician profile
            technician = Technician.objects.create(
                user=tech_user,
                phone_number='123-456-7890',
                expertise='Technician Manager'
            )
            
            self.stdout.write(self.style.SUCCESS('Successfully created technician manager user'))
        else:
            tech_user = User.objects.get(username='johndoe')
            self.stdout.write('Technician user already exists')
            
            # Make sure user is in technicians group
            if not tech_user.groups.filter(name='Technicians').exists():
                tech_user.groups.add(technicians_group)
                self.stdout.write(self.style.SUCCESS('Added technician to Technicians group'))
                
            # Make sure user has technician profile
            if not hasattr(tech_user, 'technician'):
                Technician.objects.create(
                    user=tech_user,
                    phone_number='123-456-7890',
                    expertise='Technician Manager'
                )
                self.stdout.write(self.style.SUCCESS('Created missing technician profile'))

        # Create a test technician user
        if not User.objects.filter(username='janedoe').exists():
            tech_user = User.objects.create_user(
                username='jdoe',
                password='123',
                email='technician@example.com',
                first_name='Jane',
                last_name='Doe',
            )
            
            # Add user to technicians group
            tech_user.groups.add(technicians_group)
            
            # Create technician profile
            technician = Technician.objects.create(
                user=tech_user,
                phone_number='111-111-1111',
                expertise='Technician'
            )
            
            self.stdout.write(self.style.SUCCESS('Successfully created technician user'))
        else:
            tech_user = User.objects.get(username='jdoe')
            self.stdout.write('Technician user already exists')
            
            # Make sure user is in technicians group
            if not tech_user.groups.filter(name='Technicians').exists():
                tech_user.groups.add(technicians_group)
                self.stdout.write(self.style.SUCCESS('Added technician to Technicians group'))

        # You can add other groups here if needed
        
        # You can also assign permissions to groups if needed
        # Example:
        # view_repair = Permission.objects.get(codename='view_repair')
        # technicians_group.permissions.add(view_repair)