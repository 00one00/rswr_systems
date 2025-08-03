from django.core.management.base import BaseCommand
from apps.rewards_referrals.models import RewardType, RewardOption

class Command(BaseCommand):
    help = 'Setup simplified reward options with balanced point requirements for professional customers'

    def handle(self, *args, **options):
        self.stdout.write('Setting up simplified reward options...')
        
        # Clear existing reward options to start fresh
        RewardOption.objects.all().delete()
        self.stdout.write('Cleared existing reward options.')
        
        # Create or get reward types
        repair_discount_type, _ = RewardType.objects.get_or_create(
            name="Repair Service Discount",
            category="REPAIR_DISCOUNT",
            defaults={
                'discount_type': 'PERCENTAGE',
                'discount_value': 50,
                'description': 'Percentage discount on repair services'
            }
        )
        
        free_service_type, _ = RewardType.objects.get_or_create(
            name="Free Service",
            category="FREE_SERVICE",
            defaults={
                'discount_type': 'FREE',
                'discount_value': 0,
                'description': 'Complimentary repair services'
            }
        )
        
        office_treats_type, _ = RewardType.objects.get_or_create(
            name="Office Treats",
            category="MERCHANDISE",
            defaults={
                'discount_type': 'FREE',
                'discount_value': 0,
                'description': 'Complimentary office treats and team activities'
            }
        )

        # Create simplified reward options (only 4 professional options)
        reward_options = [
            {
                'name': '50% Off Next Repair',
                'description': 'Get 50% discount on your next windshield repair service',
                'points_required': 2000,
                'reward_type': repair_discount_type
            },
            {
                'name': 'Free Windshield Repair',
                'description': 'Get one completely free windshield repair service',
                'points_required': 3500,
                'reward_type': free_service_type
            },
            {
                'name': '5 Dozen Donuts for the Office',
                'description': 'Fresh donuts delivered to your office team (5 dozen assorted)',
                'points_required': 1500,
                'reward_type': office_treats_type
            },
            {
                'name': '5 Large Pizzas for Team',
                'description': 'Pizza party for your office (5 large pizzas with variety of toppings)',
                'points_required': 2500,
                'reward_type': office_treats_type
            }
        ]

        # Create the reward options
        created_count = 0
        for option_data in reward_options:
            option, created = RewardOption.objects.get_or_create(
                name=option_data['name'],
                defaults=option_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created reward option: {option.name} ({option.points_required} points)")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} simplified reward options! '
                f'Total reward options available: {RewardOption.objects.count()}'
            )
        )
        
        # Display summary
        self.stdout.write('\n--- Simplified Rewards Summary ---')
        self.stdout.write('50% Off Next Repair: 2,000 points')
        self.stdout.write('Free Windshield Repair: 3,500 points') 
        self.stdout.write('5 Dozen Donuts for Office: 1,500 points')
        self.stdout.write('5 Large Pizzas for Team: 2,500 points')
        self.stdout.write('\nNote: With 500 points per referral, customers need 3-7 referrals for rewards.')