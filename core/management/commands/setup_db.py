from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = 'Set up database with migrations and create superuser'

    def handle(self, *args, **options):
        self.stdout.write('Setting up database...')
        
        # First, ensure all Django core migrations are applied
        try:
            self.stdout.write('Applying Django core migrations...')
            call_command('migrate', 'auth', verbosity=1, interactive=False)
            call_command('migrate', 'contenttypes', verbosity=1, interactive=False)
            call_command('migrate', 'sessions', verbosity=1, interactive=False)
            call_command('migrate', 'admin', verbosity=1, interactive=False)
            self.stdout.write(self.style.SUCCESS('Django core migrations applied successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error applying core migrations: {e}'))
        
        # Then create migrations for all custom apps
        try:
            self.stdout.write('Creating migrations for custom apps...')
            call_command('makemigrations', verbosity=1, interactive=False)
            self.stdout.write(self.style.SUCCESS('Custom migrations created successfully'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning creating migrations: {e}'))
        
        # Apply all remaining migrations
        try:
            self.stdout.write('Applying all migrations...')
            call_command('migrate', verbosity=1, interactive=False)
            self.stdout.write(self.style.SUCCESS('All migrations applied successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error applying migrations: {e}'))
            return
        
        # Collect static files
        try:
            self.stdout.write('Collecting static files...')
            call_command('collectstatic', verbosity=1, interactive=False)
            self.stdout.write(self.style.SUCCESS('Static files collected successfully'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning collecting static files: {e}'))
        
        # Create superuser
        User = get_user_model()
        try:
            if not User.objects.filter(username='admin').exists():
                self.stdout.write('Creating superuser...')
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
            else:
                self.stdout.write(self.style.WARNING('Superuser already exists'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Database setup completed!')) 