from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.models import Customer
from apps.technician_portal.models import Repair, UnitRepairCount
from .models import CustomerUser, RepairApproval
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.db.models import Sum, Q
from django.contrib.auth import update_session_auth_hash
from functools import wraps
from django.http import JsonResponse
from collections import defaultdict
from datetime import datetime

# Custom decorator to ensure only customers can access views
def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access the customer portal.")
            return redirect('login')
            
        # Check if user has a customer profile
        try:
            customer_user = CustomerUser.objects.get(user=request.user)
            return view_func(request, *args, **kwargs)
        except CustomerUser.DoesNotExist:
            # Redirect user to profile creation if they don't have a profile
            messages.info(request, "Please complete your profile setup to access customer features.")
            return redirect('profile_creation')
    return _wrapped_view

@customer_required
def customer_dashboard(request):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get statistics for the customer dashboard
        active_repairs = Repair.objects.filter(customer=customer).exclude(queue_status='COMPLETED').exclude(queue_status='DENIED').count()
        completed_repairs = Repair.objects.filter(customer=customer, queue_status='COMPLETED').count()
        pending_approval = Repair.objects.filter(customer=customer, queue_status='PENDING').count()
        
        # Get total spent on completed repairs
        total_spent = Repair.objects.filter(customer=customer, queue_status='COMPLETED').aggregate(sum=Sum('cost'))['sum'] or 0
        
        # Get recent repairs (limited to 5) for the customer
        recent_repairs = Repair.objects.filter(customer=customer).order_by('-repair_date')[:5]
        
        # Check which of the recent repairs were customer-initiated
        repair_ids = [repair.id for repair in recent_repairs]
        customer_initiated_approvals = RepairApproval.objects.filter(
            repair_id__in=repair_ids, 
            notes="Auto-approved as customer initiated the request"
        ).values_list('repair_id', flat=True)
        
        # Add a flag to each repair indicating if it was customer initiated
        for repair in recent_repairs:
            repair.customer_initiated = repair.id in customer_initiated_approvals
        
        # Get repairs that are awaiting customer approval
        repairs_awaiting_approval = Repair.objects.filter(customer=customer, queue_status='PENDING')
        
        # Get detailed repair statistics for visualizations
        stats = {
            'active_repairs': active_repairs,
            'completed_repairs': completed_repairs,
            'pending_approval': pending_approval,
            'total_spent': total_spent,
            # Detailed repair status counts for the visualization
            'repairs_requested': Repair.objects.filter(customer=customer, queue_status='REQUESTED').count(),
            'repairs_pending': pending_approval,
            'repairs_approved': Repair.objects.filter(customer=customer, queue_status='APPROVED').count(),
            'repairs_in_progress': Repair.objects.filter(customer=customer, queue_status='IN_PROGRESS').count(),
            'repairs_completed': completed_repairs,
            'repairs_denied': Repair.objects.filter(customer=customer, queue_status='DENIED').count(),
        }
        
        return render(request, 'customer_portal/dashboard.html', {
            'customer': customer,
            'stats': stats,
            'active_repairs_count': active_repairs,
            'completed_repairs_count': completed_repairs,
            'pending_approval_count': pending_approval,
            'recent_repairs': recent_repairs,
            'pending_approval_repairs': repairs_awaiting_approval,
            'customer_user': customer_user,
            'customer_initiated_repair_ids': list(customer_initiated_approvals)
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@login_required
def profile_creation(request):
    # Check if user already has a CustomerUser profile
    if CustomerUser.objects.filter(user=request.user).exists():
        return redirect('customer_dashboard')
        
    if request.method == 'POST':
        # Process the form submission
        is_new_company = request.POST.get('is_new_company') == 'yes'
        
        if is_new_company:
            # Create a new customer
            company_name = request.POST.get('company_name')
            company_email = request.POST.get('company_email')
            company_phone = request.POST.get('company_phone')
            company_address = request.POST.get('company_address')
            
            try:
                # Create new customer
                customer = Customer.objects.create(
                    name=company_name,
                    email=company_email,
                    phone=company_phone,
                    address=company_address
                )
            except Exception as e:
                messages.error(request, f"Error creating company: {str(e)}")
                customers = Customer.objects.all()
                return render(request, 'customer_portal/profile_creation.html', {'customers': customers})
        else:
            # Use existing customer
            customer_id = request.POST.get('customer')
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                messages.error(request, "Selected company does not exist.")
                customers = Customer.objects.all()
                return render(request, 'customer_portal/profile_creation.html', {'customers': customers})
        
        # Create CustomerUser record
        try:
            CustomerUser.objects.create(
                user=request.user,
                customer=customer,
                is_primary_contact=request.POST.get('is_primary_contact') == 'True'
            )
            messages.success(request, "Profile created successfully!")
            return redirect('customer_dashboard')
        except Exception as e:
            messages.error(request, f"Error creating profile: {str(e)}")
    
    # Get all customers for the dropdown
    customers = Customer.objects.all()
    return render(request, 'customer_portal/profile_creation.html', {'customers': customers})

@customer_required
def customer_repairs(request):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        sort_by = request.GET.get('sort', '-repair_date')  # Default: newest first
        
        # Get all repairs for this customer
        repairs = Repair.objects.filter(customer=customer)
        
        # Apply filters
        if status_filter == 'pending':
            repairs = repairs.filter(queue_status='PENDING')
        elif status_filter == 'approved':
            repairs = repairs.filter(queue_status='APPROVED')
        elif status_filter == 'in_progress':
            repairs = repairs.filter(queue_status='IN_PROGRESS')
        elif status_filter == 'completed':
            repairs = repairs.filter(queue_status='COMPLETED')
        
        # Apply sorting
        repairs = repairs.order_by(sort_by)
        
        # Check which repairs were customer-initiated and mark them
        repair_ids = [repair.id for repair in repairs]
        customer_initiated_approvals = RepairApproval.objects.filter(
            repair_id__in=repair_ids, 
            notes="Auto-approved as customer initiated the request"
        ).values_list('repair_id', flat=True)
        
        # Add a flag to each repair indicating if it was customer initiated
        for repair in repairs:
            repair.customer_initiated = repair.id in customer_initiated_approvals
        
        return render(request, 'customer_portal/repairs.html', {
            'repairs': repairs,
            'customer': customer,
            'status_filter': status_filter,
            'sort_by': sort_by,
            'customer_initiated_repair_ids': list(customer_initiated_approvals)
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@customer_required
def customer_repair_detail(request, repair_id):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get the repair and ensure it belongs to this customer
        repair = get_object_or_404(Repair, id=repair_id, customer=customer)
        
        # Get approval record if it exists
        try:
            approval = RepairApproval.objects.get(repair=repair)
            customer_initiated = approval.notes == "Auto-approved as customer initiated the request"
        except RepairApproval.DoesNotExist:
            approval = None
            customer_initiated = False
        
        # Mark if this was a customer-initiated repair
        repair.customer_initiated = customer_initiated
        
        return render(request, 'customer_portal/repair_detail.html', {
            'repair': repair,
            'customer': customer,
            'approval': approval
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@customer_required
def customer_repair_approve(request, repair_id):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get the repair and ensure it belongs to this customer
        repair = get_object_or_404(Repair, id=repair_id, customer=customer)
        
        if request.method == 'POST':
            notes = request.POST.get('notes', '')
            
            # Create or update the approval
            approval, created = RepairApproval.objects.get_or_create(
                repair=repair,
                defaults={
                    'approved': True,
                    'approved_by': customer_user,
                    'approval_date': timezone.now(),
                    'notes': notes
                }
            )
            
            if not created:
                approval.approved = True
                approval.approved_by = customer_user
                approval.approval_date = timezone.now()
                approval.notes = notes
                approval.save()
            
            # Update the repair status
            repair.queue_status = 'APPROVED'
            repair.save()
            
            messages.success(request, "Repair has been approved successfully.")
            return redirect('customer_repair_detail', repair_id=repair.id)
        
        return render(request, 'customer_portal/repair_approve.html', {
            'repair': repair,
            'customer': customer
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@customer_required
def customer_repair_deny(request, repair_id):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get the repair and ensure it belongs to this customer
        repair = get_object_or_404(Repair, id=repair_id, customer=customer)
        
        if request.method == 'POST':
            reason = request.POST.get('reason', '')
            
            # Create or update the approval record to mark as denied
            approval, created = RepairApproval.objects.get_or_create(
                repair=repair,
                defaults={
                    'approved': False,
                    'approved_by': customer_user,
                    'approval_date': timezone.now(),
                    'notes': reason
                }
            )
            
            if not created:
                approval.approved = False
                approval.approved_by = customer_user
                approval.approval_date = timezone.now()
                approval.notes = reason
                approval.save()
            
            # Update the repair status to indicate it was denied
            # Using a special value for DENIED to distinguish from regular PENDING
            repair.queue_status = 'DENIED'  # You'll need to add this to the model choices
            repair.save()
            
            messages.success(request, "Repair request has been denied.")
            return redirect('customer_repair_detail', repair_id=repair.id)
        
        return render(request, 'customer_portal/repair_deny.html', {
            'repair': repair,
            'customer': customer
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")

def customer_register(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')
        
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'customer_portal/register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'customer_portal/register.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, 'customer_portal/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Log user in
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {first_name}.")
            return redirect('profile_creation')
            
    return render(request, 'customer_portal/register.html')

@customer_required
def edit_company(request):
    # Get the customer user record
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        if request.method == 'POST':
            # Update customer information
            customer.name = request.POST.get('name', '').lower()
            customer.email = request.POST.get('email', '')
            customer.phone = request.POST.get('phone', '')
            customer.address = request.POST.get('address', '')
            customer.city = request.POST.get('city', '')
            customer.state = request.POST.get('state', '')
            customer.zip_code = request.POST.get('zip_code', '')
            
            try:
                customer.save()
                messages.success(request, "Company information updated successfully!")
                return redirect('customer_dashboard')
            except Exception as e:
                messages.error(request, f"Error updating company: {str(e)}")
        
        # Render the edit form
        return render(request, 'customer_portal/edit_company.html', {
            'customer': customer
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@customer_required
def request_repair(request):
    # Get the customer user record
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        if request.method == 'POST':
            # Create a new repair request
            unit_number = request.POST.get('unit_number', '')
            description = request.POST.get('description', '')
            damage_type = request.POST.get('damage_type', '')
            
            if not unit_number or not description or not damage_type:
                messages.error(request, "Please fill out all required fields.")
                return render(request, 'customer_portal/request_repair.html')
            
            # Find an available technician (for demo purposes, just get the first one)
            from apps.technician_portal.models import Technician
            technicians = Technician.objects.all()
            
            if not technicians.exists():
                messages.error(request, "No technicians available. Please try again later.")
                return render(request, 'customer_portal/request_repair.html')
            
            technician = technicians.first()
            
            # Create the repair with a special "REQUESTED" status
            # This distinguishes it from technician-created PENDING repairs that need customer approval
            try:
                repair = Repair.objects.create(
                    technician=technician,
                    customer=customer,
                    unit_number=unit_number,
                    description=description,
                    damage_type=damage_type,
                    queue_status='REQUESTED'  # Using a new status for customer-initiated requests
                )
                
                messages.success(request, "Repair request submitted successfully! A technician will review your request.")
                return redirect('customer_dashboard')  # Redirect to dashboard instead of repair details
            except Exception as e:
                messages.error(request, f"Error creating repair request: {str(e)}")
        
        # Render the repair request form
        return render(request, 'customer_portal/request_repair.html')
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@customer_required
def account_settings(request):
    # Get the customer user record
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        user = request.user
        
        if request.method == 'POST':
            # Update user information
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            is_primary_contact = request.POST.get('is_primary_contact') == 'on'
            
            # Update password if provided
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validate and save user info
            if email and email != user.email:
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, "This email is already in use by another account.")
                    return render(request, 'customer_portal/account_settings.html', {
                        'customer_user': customer_user
                    })
                user.email = email
            
            user.first_name = first_name
            user.last_name = last_name
            
            # Handle password change if provided
            if current_password and new_password and confirm_password:
                if not user.check_password(current_password):
                    messages.error(request, "Current password is incorrect.")
                    return render(request, 'customer_portal/account_settings.html', {
                        'customer_user': customer_user
                    })
                
                if new_password != confirm_password:
                    messages.error(request, "New passwords don't match.")
                    return render(request, 'customer_portal/account_settings.html', {
                        'customer_user': customer_user
                    })
                
                if len(new_password) < 8:
                    messages.error(request, "Password must be at least 8 characters long.")
                    return render(request, 'customer_portal/account_settings.html', {
                        'customer_user': customer_user
                    })
                
                user.set_password(new_password)
                update_session_auth_hash(request, user)  # Keep user logged in
            
            # Update primary contact status
            customer_user.is_primary_contact = is_primary_contact
            
            try:
                user.save()
                customer_user.save()
                messages.success(request, "Account settings updated successfully!")
                return redirect('customer_dashboard')
            except Exception as e:
                messages.error(request, f"Error updating account: {str(e)}")
        
        # Render the account settings form
        return render(request, 'customer_portal/account_settings.html', {
            'customer_user': customer_user
        })
    except CustomerUser.DoesNotExist:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile_creation')

@customer_required
def unit_repair_data_api(request):
    """API endpoint to provide unit repair data for visualizations"""
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get all unit repair counts for this customer
        unit_repairs = UnitRepairCount.objects.filter(customer=customer)
        
        # Format the data for the chart
        data = [
            {
                'unit_number': unit.unit_number,
                'count': unit.repair_count
            }
            for unit in unit_repairs
        ]
        
        return JsonResponse(data, safe=False)
    except CustomerUser.DoesNotExist:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)

@customer_required
def repair_cost_data_api(request):
    """API endpoint to provide repair frequency data for visualizations"""
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get all repairs for this customer
        repairs = Repair.objects.filter(
            customer=customer
        ).order_by('repair_date')
        
        # Group repairs by month and count them
        monthly_counts = defaultdict(int)
        
        # Count repairs by month
        for repair in repairs:
            # Format as YYYY-MM
            month_key = repair.repair_date.strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        # Format the data for the chart
        data = [
            {
                'date': f"{month}-01",  # Add day to make it a valid date for D3
                'count': count
            }
            for month, count in sorted(monthly_counts.items())
        ]
        
        return JsonResponse(data, safe=False)
    except CustomerUser.DoesNotExist:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)
    