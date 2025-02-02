from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Technician, Repair, Customer, UnitRepairCount
from .forms import TechnicianForm, RepairForm, CustomerForm
from django.db.models import Count, F
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)
@login_required
def technician_dashboard(request):
    technician = get_object_or_404(Technician, user=request.user)
    return render(request, 'technician_portal/dashboard.html', {
        'technician': technician,
    })

@login_required
def repair_list(request):
    technician = get_object_or_404(Technician, user=request.user)
    customers = Customer.objects.filter(repair__technician=technician).distinct()
    
    customer_search = request.GET.get('customer_search', '')
    if customer_search:
        customers = customers.filter(name__icontains=customer_search)

    return render(request, 'technician_portal/repair_list.html', {
        'customers': customers,
        'customer_search': customer_search,
    })

@login_required
def repair_detail(request, repair_id):
    repair = get_object_or_404(Repair, id=repair_id, technician__user=request.user)
    return render(request, 'technician_portal/repair_detail.html', {
        'repair': repair,
        'TIME_ZONE': timezone.get_current_timezone_name()
    })

@login_required
def create_repair(request):
    if request.method == 'POST':
        form = RepairForm(request.POST)
        if form.is_valid():
            repair = form.save(commit=False)
            repair.technician = request.user.technician
            repair.save()
            return redirect('repair_detail', repair_id=repair.id)
        else:
            logger.debug(f"Form errors: {form.errors}")
    else:
        form = RepairForm()
    
    pending_repair_warning = form.errors.get('__all__')
    return render(request, 'technician_portal/repair_form.html', {
        'form': form,
        'pending_repair_warning': pending_repair_warning
    })

@login_required
def update_repair(request, repair_id):
    repair = get_object_or_404(Repair, id=repair_id, technician__user=request.user)
    if request.method == 'POST':
        form = RepairForm(request.POST, instance=repair)
        if form.is_valid():
            form.save()
            return redirect('repair_detail', repair_id=repair.id)
    else:
        form = RepairForm(instance=repair)
    
    return render(request, 'technician_portal/repair_form.html', {'form': form, 'repair': repair})

@login_required
def update_queue_status(request, repair_id):
    repair = get_object_or_404(Repair, id=repair_id, technician__user=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('queue_status')
        if new_status in dict(Repair.QUEUE_CHOICES):
            repair.queue_status = new_status
            repair.save()
    return redirect('repair_detail', repair_id=repair.id)

@login_required
def update_technician_profile(request):
    technician = get_object_or_404(Technician, user=request.user)
    if request.method == 'POST':
        form = TechnicianForm(request.POST, instance=technician)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('technician_dashboard')
    else:
        form = TechnicianForm(instance=technician)
    return render(request, 'technician_portal/update_profile.html', {'form': form})

@login_required
def create_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' has been created successfully.")
            return redirect('technician_dashboard')
    else:
        form = CustomerForm()
    return render(request, 'technician_portal/customer_form.html', {'form': form})

@login_required
def customer_details(request, customer_id):
    technician = get_object_or_404(Technician, user=request.user)
    customer = get_object_or_404(Customer, id=customer_id)
    repairs = Repair.objects.filter(technician=technician, customer=customer)

    unit_search = request.GET.get('unit_search', '')
    if unit_search:
        repairs = repairs.filter(unit_number__icontains=unit_search)

    units = repairs.values_list('unit_number', flat=True).distinct()

    return render(request, 'technician_portal/customer_details.html', {
        'customer': customer,
        'units': units,
        'unit_search': unit_search,
    })

@login_required
def unit_details(request, customer_id, unit_number):
    technician = get_object_or_404(Technician, user=request.user)
    customer = get_object_or_404(Customer, id=customer_id)
    repairs = Repair.objects.filter(technician=technician, customer=customer, unit_number=unit_number)

    return render(request, 'technician_portal/unit_details.html', {
        'customer': customer,
        'unit_number': unit_number,
        'repairs': repairs,
    })

@login_required
def mark_unit_replaced(request, customer_id, unit_number):
    customer = get_object_or_404(Customer, id=customer_id)
    unit_repair_count = get_object_or_404(UnitRepairCount, customer=customer, unit_number=unit_number)
    unit_repair_count.repair_count = 0
    unit_repair_count.save()
    messages.success(request, f"Unit #{unit_number} for {customer.name} has been marked as replaced. Repair count reset to 0.")
    return redirect('customer_details', customer_id=customer_id)

from django.http import JsonResponse

@login_required
def check_existing_repair(request):
    customer_id = request.GET.get('customer')
    unit_number = request.GET.get('unit_number')
    existing_repair = Repair.objects.filter(
        customer_id=customer_id,
        unit_number=unit_number,
        queue_status__in=['PENDING', 'APPROVED', 'IN_PROGRESS']
    ).first()
    
    if existing_repair:
        return JsonResponse({
            'existing_repair': True,
            'status': existing_repair.get_queue_status_display(),
            'repair_id': existing_repair.id,
            'warning_message': f"There is already a {existing_repair.get_queue_status_display()} repair for this unit."
        })
    return JsonResponse({'existing_repair': False})
