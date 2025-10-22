#!/usr/bin/env python
"""
Sprint 1 Implementation Validation Script
Tests all Phase 1 features to ensure they work correctly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rs_systems.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth.models import User
from core.models import Customer
from apps.customer_portal.pricing_models import CustomerPricing
from apps.technician_portal.models import Technician, Repair, UnitRepairCount
from apps.technician_portal.services.pricing_service import (
    calculate_repair_cost,
    calculate_repair_cost_with_volume_discount,
    can_manager_override_price,
    get_pricing_info
)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test(description):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            try:
                result = func()
                status = f"{Colors.GREEN}✓ PASS{Colors.END}"
                print(f"{status} - {description}")
                return True
            except AssertionError as e:
                status = f"{Colors.RED}✗ FAIL{Colors.END}"
                print(f"{status} - {description}")
                print(f"       Error: {e}")
                return False
            except Exception as e:
                status = f"{Colors.YELLOW}⚠ ERROR{Colors.END}"
                print(f"{status} - {description}")
                print(f"       Exception: {e}")
                return False
        return wrapper
    return decorator

# Test Suite
tests_passed = 0
tests_failed = 0

print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
print(f"{Colors.BLUE}SPRINT 1 VALIDATION TEST SUITE{Colors.END}")
print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

# Phase 1.1: Customer Pricing Model Tests
print(f"{Colors.BLUE}Phase 1.1: Customer Pricing Model{Colors.END}")
print("-" * 70)

@test("CustomerPricing model exists and has all required fields")
def test_customer_pricing_model():
    fields = [f.name for f in CustomerPricing._meta.get_fields()]
    required_fields = [
        'customer', 'use_custom_pricing', 'repair_1_price', 'repair_2_price',
        'repair_3_price', 'repair_4_price', 'repair_5_plus_price',
        'volume_discount_threshold', 'volume_discount_percentage',
        'created_by', 'created_at', 'updated_at', 'notes'
    ]
    for field in required_fields:
        assert field in fields, f"Missing field: {field}"
    return True

if test_customer_pricing_model():
    tests_passed += 1
else:
    tests_failed += 1

@test("CustomerPricing helper methods work correctly")
def test_customer_pricing_methods():
    # Create test customer
    customer, _ = Customer.objects.get_or_create(
        name="Test Customer - Pricing",
        defaults={'email': 'test@pricing.com', 'phone': '555-0001'}
    )

    # Create pricing config
    pricing, _ = CustomerPricing.objects.get_or_create(
        customer=customer,
        defaults={
            'use_custom_pricing': True,
            'repair_1_price': Decimal('45.00'),
            'volume_discount_threshold': 5,
            'volume_discount_percentage': Decimal('10.00')
        }
    )

    # Test get_repair_price
    assert pricing.get_repair_price(1) == Decimal('45.00'), "Tier 1 price incorrect"

    # Test has_volume_discount
    assert pricing.has_volume_discount(6) == True, "Volume discount check failed"
    assert pricing.has_volume_discount(4) == False, "Volume discount false positive"

    # Test apply_volume_discount
    discounted = pricing.apply_volume_discount(Decimal('100.00'), 6)
    assert discounted == Decimal('90.00'), "Volume discount calculation incorrect"

    return True

if test_customer_pricing_methods():
    tests_passed += 1
else:
    tests_failed += 1

# Phase 1.2: Enhanced Technician Role System
print(f"\n{Colors.BLUE}Phase 1.2: Enhanced Technician Role System{Colors.END}")
print("-" * 70)

@test("Technician model has all manager fields")
def test_technician_manager_fields():
    fields = [f.name for f in Technician._meta.get_fields()]
    required_fields = [
        'is_manager', 'approval_limit', 'can_assign_work', 'can_override_pricing',
        'managed_technicians', 'repairs_completed', 'average_repair_time',
        'customer_rating', 'is_active', 'working_hours'
    ]
    for field in required_fields:
        assert field in fields, f"Missing field: {field}"
    return True

if test_technician_manager_fields():
    tests_passed += 1
else:
    tests_failed += 1

@test("Technician helper methods work correctly")
def test_technician_methods():
    # Create test user and technician
    user, _ = User.objects.get_or_create(
        username='test_manager',
        defaults={'email': 'manager@test.com'}
    )

    tech, _ = Technician.objects.get_or_create(
        user=user,
        defaults={
            'is_manager': True,
            'approval_limit': Decimal('200.00'),
            'can_override_pricing': True
        }
    )

    # Test can_approve_amount
    assert tech.can_approve_amount(Decimal('150.00')) == True, "Should approve within limit"
    assert tech.can_approve_amount(Decimal('250.00')) == False, "Should reject over limit"

    return True

if test_technician_methods():
    tests_passed += 1
else:
    tests_failed += 1

# Phase 1.3: Pricing Service Integration
print(f"\n{Colors.BLUE}Phase 1.3: Pricing Service Integration{Colors.END}")
print("-" * 70)

@test("Pricing service calculates default pricing correctly")
def test_default_pricing():
    customer, _ = Customer.objects.get_or_create(
        name="Test Customer - Default",
        defaults={'email': 'default@test.com', 'phone': '555-0002'}
    )

    # Default pricing should be: 50, 40, 35, 30, 25
    assert calculate_repair_cost(customer, 1) == Decimal('50'), "Default tier 1 incorrect"
    assert calculate_repair_cost(customer, 2) == Decimal('40'), "Default tier 2 incorrect"
    assert calculate_repair_cost(customer, 3) == Decimal('35'), "Default tier 3 incorrect"
    assert calculate_repair_cost(customer, 4) == Decimal('30'), "Default tier 4 incorrect"
    assert calculate_repair_cost(customer, 5) == Decimal('25'), "Default tier 5 incorrect"

    return True

if test_default_pricing():
    tests_passed += 1
else:
    tests_failed += 1

@test("Pricing service uses custom pricing when configured")
def test_custom_pricing():
    customer, _ = Customer.objects.get_or_create(
        name="Test Customer - Custom",
        defaults={'email': 'custom@test.com', 'phone': '555-0003'}
    )

    # Create custom pricing
    pricing, _ = CustomerPricing.objects.get_or_create(
        customer=customer,
        defaults={
            'use_custom_pricing': True,
            'repair_1_price': Decimal('45.00'),
            'repair_2_price': Decimal('35.00'),
        }
    )
    pricing.use_custom_pricing = True
    pricing.save()

    # Should use custom pricing
    assert calculate_repair_cost(customer, 1) == Decimal('45.00'), "Custom tier 1 not applied"
    assert calculate_repair_cost(customer, 2) == Decimal('35.00'), "Custom tier 2 not applied"

    # Tier 3 not set, should fall back to default
    assert calculate_repair_cost(customer, 3) == Decimal('35'), "Default fallback failed"

    return True

if test_custom_pricing():
    tests_passed += 1
else:
    tests_failed += 1

@test("Volume discount calculation works correctly")
def test_volume_discount():
    customer, _ = Customer.objects.get_or_create(
        name="Test Customer - Volume",
        defaults={'email': 'volume@test.com', 'phone': '555-0004'}
    )

    pricing, _ = CustomerPricing.objects.get_or_create(
        customer=customer,
        defaults={
            'use_custom_pricing': True,
            'volume_discount_threshold': 10,
            'volume_discount_percentage': Decimal('15.00')
        }
    )
    pricing.use_custom_pricing = True
    pricing.save()

    # Test with 12 total repairs (above threshold)
    final_price, discount_applied, discount_amount = calculate_repair_cost_with_volume_discount(
        customer, 1, 12
    )

    assert discount_applied == True, "Volume discount not applied"
    expected_price = Decimal('50.00') * Decimal('0.85')  # 15% off
    assert final_price == expected_price, f"Expected {expected_price}, got {final_price}"

    return True

if test_volume_discount():
    tests_passed += 1
else:
    tests_failed += 1

@test("Manager override permission validation works")
def test_manager_override_permission():
    # Create manager with limit
    user, _ = User.objects.get_or_create(
        username='test_manager_override',
        defaults={'email': 'override@test.com'}
    )

    tech, _ = Technician.objects.get_or_create(
        user=user,
        defaults={
            'is_manager': True,
            'approval_limit': Decimal('150.00'),
            'can_override_pricing': True
        }
    )

    # Test within limit
    assert can_manager_override_price(tech, Decimal('100.00')) == True, "Should allow within limit"

    # Test over limit
    assert can_manager_override_price(tech, Decimal('200.00')) == False, "Should block over limit"

    # Test non-manager
    tech.is_manager = False
    tech.save()
    assert can_manager_override_price(tech, Decimal('50.00')) == False, "Should block non-manager"

    return True

if test_manager_override_permission():
    tests_passed += 1
else:
    tests_failed += 1

@test("Repair model uses pricing service in save method")
def test_repair_pricing_integration():
    # Create test data
    customer, _ = Customer.objects.get_or_create(
        name="Test Customer - Repair",
        defaults={'email': 'repair@test.com', 'phone': '555-0005'}
    )

    user, _ = User.objects.get_or_create(
        username='test_tech_repair',
        defaults={'email': 'tech@test.com'}
    )

    tech, _ = Technician.objects.get_or_create(user=user)

    # Create custom pricing
    pricing, _ = CustomerPricing.objects.get_or_create(
        customer=customer,
        defaults={
            'use_custom_pricing': True,
            'repair_1_price': Decimal('42.00'),
        }
    )
    pricing.use_custom_pricing = True
    pricing.save()

    # Create repair
    repair = Repair.objects.create(
        technician=tech,
        customer=customer,
        unit_number='TEST-001',
        queue_status='PENDING'
    )

    # Cost should be custom price (next repair would be 1st)
    assert repair.cost == Decimal('42.00'), f"Expected 42.00, got {repair.cost}"

    return True

if test_repair_pricing_integration():
    tests_passed += 1
else:
    tests_failed += 1

# Print Summary
print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
print(f"{Colors.BLUE}{'='*70}{Colors.END}")
print(f"{Colors.GREEN}Passed: {tests_passed}{Colors.END}")
print(f"{Colors.RED}Failed: {tests_failed}{Colors.END}")
print(f"Total:  {tests_passed + tests_failed}")
print()

if tests_failed == 0:
    print(f"{Colors.GREEN}✓ ALL TESTS PASSED - Sprint 1 is fully functional!{Colors.END}\n")
    sys.exit(0)
else:
    print(f"{Colors.RED}✗ SOME TESTS FAILED - Please review the failures above{Colors.END}\n")
    sys.exit(1)
