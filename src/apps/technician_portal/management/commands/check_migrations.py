from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Check if the technician_portal migrations have been applied'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if the technician_notification table exists
            cursor.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables 
                   WHERE table_schema = 'public'
                   AND table_name = 'technician_portal_techniciannotification'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            # Check migrations in django_migrations table
            cursor.execute("""
                SELECT app, name FROM django_migrations WHERE app = 'technician_portal';
            """)
            migrations = cursor.fetchall()
            
        if table_exists:
            self.stdout.write(self.style.SUCCESS('technician_portal_techniciannotification table exists'))
        else:
            self.stdout.write(self.style.ERROR('technician_portal_techniciannotification table does NOT exist'))
            
        self.stdout.write("\nApplied migrations:")
        for migration in migrations:
            self.stdout.write(f"{migration[0]}.{migration[1]}") 