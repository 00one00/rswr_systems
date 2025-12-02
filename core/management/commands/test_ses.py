"""
Management command to test AWS SES email configuration.

Usage:
    python manage.py test_ses recipient@example.com

This command sends a test email using Django's configured email backend
to verify that AWS SES is properly configured and working.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test AWS SES email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']

        # Basic email validation
        if '@' not in recipient or '.' not in recipient.split('@')[-1]:
            raise CommandError(f'Invalid email address: {recipient}')

        self.stdout.write('=' * 70)
        self.stdout.write(self.style.WARNING('AWS SES Email Test'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'Recipient: {recipient}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')

        if hasattr(settings, 'EMAIL_HOST'):
            self.stdout.write(f'SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')

        self.stdout.write('=' * 70)
        self.stdout.write('')

        try:
            # Send test email
            self.stdout.write(self.style.WARNING('Sending test email...'))

            num_sent = send_mail(
                subject='RS Systems - SES Configuration Test',
                message='''This is a test email from the RS Systems notification system.

If you received this email, your AWS SES configuration is working correctly!

Configuration Details:
- Email Backend: {}
- From Address: {}
- Sent via management command: python manage.py test_ses

Next Steps:
1. Verify this email arrived in your inbox
2. Check spam folder if not in inbox
3. Verify sender reputation in AWS SES console
4. Consider setting up DKIM/SPF records for better deliverability

RS Systems Notification System - Phase 2
'''.format(settings.EMAIL_BACKEND, settings.DEFAULT_FROM_EMAIL),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )

            self.stdout.write('')
            self.stdout.write('=' * 70)

            if num_sent > 0:
                self.stdout.write(self.style.SUCCESS('✅ Email sent successfully!'))
                self.stdout.write('')
                self.stdout.write('Next steps:')
                self.stdout.write('1. Check the recipient inbox: {}'.format(recipient))
                self.stdout.write('2. If using SES sandbox mode, verify the recipient email is verified')
                self.stdout.write('3. Check spam folder if not in inbox')
                self.stdout.write('4. Review AWS SES sending statistics in AWS Console')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Email may not have been sent (no error, but send count = 0)'))

        except Exception as e:
            self.stdout.write('')
            self.stdout.write('=' * 70)
            self.stdout.write(self.style.ERROR('❌ Failed to send email'))
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            self.stdout.write('')

            # Provide troubleshooting tips
            self.stdout.write(self.style.WARNING('Troubleshooting Tips:'))
            self.stdout.write('1. Verify AWS_SES_SMTP_USER and AWS_SES_SMTP_PASSWORD are set in .env')
            self.stdout.write('2. Check that EMAIL_HOST and EMAIL_PORT are correct')
            self.stdout.write('3. Ensure sender email is verified in AWS SES console')
            self.stdout.write('4. If in sandbox mode, verify recipient email is also verified')
            self.stdout.write('5. Check AWS SES sending limits haven\'t been exceeded')
            self.stdout.write('6. Verify IAM user has ses:SendEmail permissions')
            self.stdout.write('')
            self.stdout.write('For detailed setup instructions, see:')
            self.stdout.write('docs/development/notifications/AWS_SETUP_GUIDE.md')

            raise CommandError('Email test failed')

        self.stdout.write('=' * 70)
