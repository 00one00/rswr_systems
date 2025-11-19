"""
Management command to set up default viscosity recommendation rules.
Run with: python manage.py setup_viscosity_rules
"""
from django.core.management.base import BaseCommand
from apps.technician_portal.models import ViscosityRecommendation


class Command(BaseCommand):
    help = 'Set up default temperature-based viscosity recommendation rules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing rules before creating new ones',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)

        if reset:
            self.stdout.write(self.style.WARNING('Deleting existing viscosity rules...'))
            deleted_count = ViscosityRecommendation.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} existing rules'))

        # Check if rules already exist
        existing_count = ViscosityRecommendation.objects.count()
        if existing_count > 0 and not reset:
            self.stdout.write(
                self.style.WARNING(
                    f'Found {existing_count} existing viscosity rules. '
                    'Use --reset flag to delete and recreate them.'
                )
            )
            return

        self.stdout.write('Creating default viscosity recommendation rules...')

        # Define default rules with corrected boundaries
        default_rules = [
            {
                'name': 'Cold Weather',
                'min_temperature': None,
                'max_temperature': 59.9,
                'recommended_viscosity': 'Low',
                'suggestion_text': 'Low viscosity recommended for cold conditions',
                'badge_color': 'blue',
                'display_order': 1,
            },
            {
                'name': 'Standard Conditions',
                'min_temperature': 60.0,
                'max_temperature': 84.9,
                'recommended_viscosity': 'Medium',
                'suggestion_text': 'Medium viscosity recommended for optimal conditions',
                'badge_color': 'green',
                'display_order': 2,
            },
            {
                'name': 'Hot Weather',
                'min_temperature': 85.0,
                'max_temperature': None,
                'recommended_viscosity': 'High',
                'suggestion_text': 'High viscosity recommended for hot conditions',
                'badge_color': 'orange',
                'display_order': 3,
            },
        ]

        # Create rules
        created_count = 0
        for rule_data in default_rules:
            rule, created = ViscosityRecommendation.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )

            if created:
                created_count += 1
                temp_range = rule._get_temp_range_display()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {rule.name} ({temp_range}) → {rule.recommended_viscosity}'
                    )
                )
            else:
                temp_range = rule._get_temp_range_display()
                self.stdout.write(
                    self.style.WARNING(
                        f'- Already exists: {rule.name} ({temp_range})'
                    )
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new viscosity rules')
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Total active rules: {ViscosityRecommendation.objects.filter(is_active=True).count()}'
            )
        )
