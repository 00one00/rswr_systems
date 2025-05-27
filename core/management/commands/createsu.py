import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Creates a superuser for initial deployment'

    def handle(self, *args, **options):
        admin_username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('DJANGO_ADMIN_PASSWORD')

        if not admin_password:
            self.stdout.write(self.style.WARNING('DJANGO_ADMIN_PASSWORD environment variable not set. Skipping superuser creation.'))
            return

        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {admin_username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser {admin_username} already exists. Skipping creation.')) 