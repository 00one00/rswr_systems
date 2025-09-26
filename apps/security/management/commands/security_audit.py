"""
Security audit command to check for suspicious users and activity.
Usage: python manage.py security_audit
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.security.models import LoginAttempt
import re


class Command(BaseCommand):
    help = 'Run security audit to identify suspicious accounts and activity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-user',
            type=str,
            help='Check specific username for suspicious patterns'
        )
        parser.add_argument(
            '--delete-suspicious',
            action='store_true',
            help='Delete suspicious bot-like users (use with caution!)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back for activity (default: 30)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== SECURITY AUDIT REPORT ===\n'))

        # Check for specific user if requested
        if options['check_user']:
            self.check_specific_user(options['check_user'])
            return

        # Find suspicious usernames
        suspicious_users = self.find_suspicious_users()

        # Check recent failed login attempts
        self.check_failed_logins(options['days'])

        # Check for users created recently
        self.check_recent_registrations(options['days'])

        # Handle deletion if requested
        if options['delete_suspicious'] and suspicious_users:
            self.handle_suspicious_user_deletion(suspicious_users)

    def find_suspicious_users(self):
        """Find users with bot-like usernames"""
        self.stdout.write('\n📋 Checking for suspicious usernames...')

        suspicious_patterns = [
            (r'^[a-z]{10,}$', 'All lowercase, 10+ characters'),
            (r'^[0-9a-f]{8,}$', 'Hex-like string'),
            (r'^user[0-9]{5,}$', 'Generic userNNNNN pattern'),
            (r'^test', 'Test account'),
            (r'^temp', 'Temporary account'),
        ]

        suspicious_users = []

        for pattern, description in suspicious_patterns:
            users = User.objects.filter(username__regex=pattern)
            for user in users:
                # Check if it's a known test account
                if user.username in ['tech1', 'tech2', 'tech3', 'democustomer', 'demoadmin']:
                    continue

                # Additional check for randomness
                if self.is_likely_bot(user.username):
                    suspicious_users.append(user)
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  {user.username} - {description} '
                            f'(created: {user.date_joined.date()}, '
                            f'last login: {user.last_login.date() if user.last_login else "Never"})'
                        )
                    )

        # Check for specific problematic username patterns
        all_lowercase = User.objects.filter(username__regex=r'^[a-z]{8,}$')
        for user in all_lowercase:
            if user not in suspicious_users and self.is_likely_bot(user.username):
                suspicious_users.append(user)
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  {user.username} - Random character pattern detected '
                        f'(created: {user.date_joined.date()}, '
                        f'last login: {user.last_login.date() if user.last_login else "Never"})'
                    )
                )

        if not suspicious_users:
            self.stdout.write(self.style.SUCCESS('  ✅ No suspicious usernames found'))
        else:
            self.stdout.write(f'\n  Found {len(suspicious_users)} suspicious accounts')

        return suspicious_users

    def is_likely_bot(self, username):
        """Check if username has bot-like characteristics"""
        # Check for the specific pattern like 'ygzwnplsgv'
        if len(username) >= 8 and username.isalpha() and username.islower():
            vowels = set('aeiou')
            consonant_run = 0
            vowel_count = 0

            for char in username:
                if char in vowels:
                    vowel_count += 1
                    consonant_run = 0
                else:
                    consonant_run += 1
                    if consonant_run > 4:
                        return True

            # Less than 20% vowels is suspicious
            if vowel_count < len(username) * 0.2:
                return True

        return False

    def check_specific_user(self, username):
        """Check a specific user for suspicious patterns"""
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'\n📋 Analysis for user: {username}')
            self.stdout.write(f'  Created: {user.date_joined}')
            self.stdout.write(f'  Last login: {user.last_login or "Never"}')
            self.stdout.write(f'  Email: {user.email or "Not provided"}')
            self.stdout.write(f'  Active: {user.is_active}')

            # Check if bot-like
            if self.is_likely_bot(username):
                self.stdout.write(
                    self.style.WARNING('  ⚠️  This username matches bot patterns!')
                )

                # Check consonant/vowel ratio
                vowels = sum(1 for c in username if c in 'aeiou')
                consonants = sum(1 for c in username if c.isalpha() and c not in 'aeiou')
                self.stdout.write(f'  Vowels: {vowels}, Consonants: {consonants}')

                if vowels > 0:
                    ratio = consonants / vowels
                    self.stdout.write(f'  Consonant/Vowel ratio: {ratio:.2f}')
                    if ratio > 4:
                        self.stdout.write(
                            self.style.WARNING('  ⚠️  Very high consonant ratio (bot indicator)')
                        )
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Username appears legitimate'))

            # Check login attempts
            attempts = LoginAttempt.objects.filter(username=username).order_by('-timestamp')[:10]
            if attempts:
                self.stdout.write(f'\n  Recent login attempts:')
                for attempt in attempts:
                    status = '✅' if attempt.success else '❌'
                    self.stdout.write(
                        f'    {status} {attempt.timestamp} from {attempt.ip_address}'
                    )

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found'))

    def check_failed_logins(self, days):
        """Check for excessive failed login attempts"""
        self.stdout.write(f'\n🔒 Failed login attempts (last {days} days)...')

        cutoff = timezone.now() - timedelta(days=days)
        failed_attempts = LoginAttempt.objects.filter(
            success=False,
            timestamp__gte=cutoff
        )

        # Group by username
        by_username = {}
        for attempt in failed_attempts:
            if attempt.username not in by_username:
                by_username[attempt.username] = []
            by_username[attempt.username].append(attempt)

        # Sort by number of attempts
        sorted_users = sorted(by_username.items(), key=lambda x: len(x[1]), reverse=True)

        if sorted_users:
            self.stdout.write(f'  Top failed login attempts:')
            for username, attempts in sorted_users[:10]:
                count = len(attempts)
                if count >= 5:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠️  {username}: {count} failures')
                    )
                else:
                    self.stdout.write(f'    {username}: {count} failures')
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ No failed login attempts'))

    def check_recent_registrations(self, days):
        """Check users registered recently"""
        self.stdout.write(f'\n👤 Recent registrations (last {days} days)...')

        cutoff = timezone.now() - timedelta(days=days)
        recent_users = User.objects.filter(date_joined__gte=cutoff).order_by('-date_joined')

        if recent_users:
            self.stdout.write(f'  {recent_users.count()} new users:')
            for user in recent_users[:20]:
                warning = ''
                if self.is_likely_bot(user.username):
                    warning = ' ⚠️  (SUSPICIOUS)'
                self.stdout.write(
                    f'    {user.username} - {user.date_joined.date()}{warning}'
                )
        else:
            self.stdout.write('  No new registrations')

    def handle_suspicious_user_deletion(self, suspicious_users):
        """Handle deletion of suspicious users"""
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Ready to delete {len(suspicious_users)} suspicious users'
            )
        )

        for user in suspicious_users:
            self.stdout.write(f'  - {user.username}')

        confirm = input('\nAre you sure you want to delete these users? (yes/no): ')

        if confirm.lower() == 'yes':
            for user in suspicious_users:
                username = user.username
                user.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Deleted user: {username}')
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully deleted {len(suspicious_users)} suspicious users'
                )
            )
        else:
            self.stdout.write('Deletion cancelled')