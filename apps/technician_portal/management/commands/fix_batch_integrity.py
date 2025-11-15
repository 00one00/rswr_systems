"""
Management command to fix batch repair data integrity issues.
Ensures break_number and total_breaks_in_batch are consistent across all batches.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Max
from apps.technician_portal.models import Repair


class Command(BaseCommand):
    help = 'Fix batch repair data integrity (break numbers and totals)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Get all unique batch IDs
        batch_ids = Repair.objects.filter(
            repair_batch_id__isnull=False
        ).values_list('repair_batch_id', flat=True).distinct()

        total_batches = len(batch_ids)
        fixed_batches = 0
        issues_found = 0

        self.stdout.write(f'\nFound {total_batches} batches to check...\n')

        for batch_id in batch_ids:
            # Get all repairs in this batch
            repairs = Repair.objects.filter(repair_batch_id=batch_id).order_by('break_number')
            actual_count = repairs.count()

            # Get max break number and check for inconsistencies
            max_break_number = repairs.aggregate(Max('break_number'))['break_number__max']

            # Check if all repairs have the same total_breaks_in_batch value
            total_breaks_values = repairs.values_list('total_breaks_in_batch', flat=True).distinct()

            has_issue = False
            issue_details = []

            # Check 1: total_breaks_in_batch should match actual count
            if len(total_breaks_values) > 1:
                has_issue = True
                issue_details.append(f"  - Inconsistent total_breaks_in_batch values: {list(total_breaks_values)}")

            # Check 2: total_breaks_in_batch should match max break_number
            if max_break_number != actual_count:
                has_issue = True
                issue_details.append(f"  - Max break_number ({max_break_number}) doesn't match actual count ({actual_count})")

            # Check 3: all total_breaks_in_batch values should match actual count
            for val in total_breaks_values:
                if val != actual_count:
                    has_issue = True
                    issue_details.append(f"  - total_breaks_in_batch ({val}) doesn't match actual count ({actual_count})")
                    break

            if has_issue:
                issues_found += 1
                first_repair = repairs.first()
                self.stdout.write(self.style.ERROR(f'\nBatch {batch_id}:'))
                self.stdout.write(f'  Customer: {first_repair.customer.name}')
                self.stdout.write(f'  Unit: {first_repair.unit_number}')
                self.stdout.write(f'  Actual repairs in batch: {actual_count}')
                for detail in issue_details:
                    self.stdout.write(self.style.WARNING(detail))

                if not dry_run:
                    # Fix: Update all repairs in batch with correct values
                    # Re-number breaks sequentially and set correct total
                    for idx, repair in enumerate(repairs, start=1):
                        repair.break_number = idx
                        repair.total_breaks_in_batch = actual_count
                        repair.save(update_fields=['break_number', 'total_breaks_in_batch'])

                    fixed_batches += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Fixed: Set all to {actual_count} breaks with sequential numbering'))

        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDRY RUN COMPLETE'))
            self.stdout.write(f'Found {issues_found} batches with integrity issues')
            self.stdout.write('Run without --dry-run to apply fixes')
        else:
            self.stdout.write(self.style.SUCCESS(f'\nFIXES APPLIED'))
            self.stdout.write(f'Checked: {total_batches} batches')
            self.stdout.write(f'Issues found: {issues_found}')
            self.stdout.write(f'Batches fixed: {fixed_batches}')

        self.stdout.write('='*60 + '\n')
