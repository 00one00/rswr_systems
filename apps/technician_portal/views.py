from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Technician, Repair, UnitRepairCount, TechnicianNotification
from core.models import Customer
from .forms import TechnicianForm, RepairForm, CustomerForm, TechnicianRegistrationForm
from django.db.models import Count, F
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import logging
from django.core.paginator import Paginator
from functools import wraps
from django.db.models import Q

# Add a helper function to safely check if a user has technician access
def has_technician_access(user):
    """Helper function to check if a user has technician access through profile or admin privileges"""
    # Admin users always have access
    if user.is_staff:
        return True
    
    # Check if user is in the Technicians group
    if user.groups.filter(name='Technicians').exists():
        return True
    
    # Non-admin users need a technician profile
    try:
        return hasattr(user, 'technician') and user.technician is not None
    except:
        return False

# Custom decorator to ensure only technicians can access views
def technician_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access the technician portal.")
            return redirect('login')
        
        # Check if user has technician access
        if has_technician_access(request.user):
            return view_func(request, *args, **kwargs)
            
        # User doesn't have access
        messages.warning(request, "Your account does not have technician access. Please contact an administrator if you believe this is an error.")
        return redirect('home')
    return _wrapped_view

# Admin required decorator
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access this feature.")
            return redirect('login')
        
        # Check if user is admin
        if not request.user.is_staff:
            messages.warning(request, "This action requires administrator privileges.")
            return redirect('technician_dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def register_technician(request):
    if request.method == 'POST':
        form = TechnicianRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}')
            return redirect('admin:index')
    else:
        form = TechnicianRegistrationForm()
    return render(request, 'registration/register_technician.html', {'form': form})

logger = logging.getLogger(__name__)
@technician_required
def technician_dashboard(request):
    # Get technician profile or None for admin users without a profile
    technician = None
    if hasattr(request.user, 'technician'):
        technician = request.user.technician
    
    # Get customer-requested repairs
    if technician:
        # For regular technicians, show all REQUESTED repairs (unassigned queue)
        # but highlight their specifically assigned ones
        customer_requested_repairs = Repair.objects.filter(
            queue_status='REQUESTED'
        ).order_by('-repair_date')
        
        # Add a flag to mark which repairs are assigned to this technician
        for repair in customer_requested_repairs:
            repair.assigned_to_me = repair.technician == technician
        
        # Get assigned reward redemptions for this technician
        from apps.rewards_referrals.models import RewardRedemption
        assigned_redemptions = RewardRedemption.objects.filter(
            assigned_technician=technician,
            status='PENDING'
        ).order_by('-created_at')
        
        # Get all pending redemptions (visible to all technicians)
        all_pending_redemptions = RewardRedemption.objects.filter(
            status='PENDING'
        ).exclude(
            id__in=[r.id for r in assigned_redemptions]
        ).order_by('-created_at')[:5]  # Limit to 5 most recent
        
        # Get unread notifications
        unread_notifications = technician.notifications.filter(read=False).order_by('-created_at')
    else:
        # For admins without a technician profile, show all requested repairs
        customer_requested_repairs = Repair.objects.filter(
            queue_status='REQUESTED'
        ).order_by('-repair_date')
        
        # For admins, show technician assignment info
        for repair in customer_requested_repairs:
            repair.assigned_to_me = False  # Admins don't have assignments
        
        # For admins, show all pending redemptions
        from apps.rewards_referrals.models import RewardRedemption
        assigned_redemptions = []
        all_pending_redemptions = RewardRedemption.objects.filter(
            status='PENDING'
        ).order_by('-created_at')
        
        unread_notifications = None
    
    # Extra data for admin users
    is_admin = request.user.is_staff
    admin_data = None
    
    if is_admin:
        # Get data that only admins should see
        admin_data = {
            'total_repairs': Repair.objects.count(),
            'pending_repairs': Repair.objects.filter(queue_status='PENDING').count(),
            'customers': Customer.objects.count(),
            'technicians': Technician.objects.count(),
            'pending_redemptions': RewardRedemption.objects.filter(status='PENDING').count()
        }
    
    return render(request, 'technician_portal/dashboard.html', {
        'technician': technician,
        'customer_requested_repairs': customer_requested_repairs,
        'assigned_redemptions': assigned_redemptions,
        'all_pending_redemptions': all_pending_redemptions,
        'unread_notifications': unread_notifications,
        'is_admin': is_admin,
        'admin_data': admin_data,
    })

@technician_required
def repair_list(request):
    # For regular technicians, only show their repairs
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to view repairs.")
            return redirect('technician_dashboard')
            
        technician = request.user.technician
        # Get all repairs for this technician
        repairs = Repair.objects.filter(technician=technician)
    else:
        # For admins, show all repairs
        repairs = Repair.objects.all()
        technician = None
    
    # Get filter parameters
    customer_search = request.GET.get('customer_search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Apply customer filter if provided
    if customer_search:
        repairs = repairs.filter(customer__name__icontains=customer_search)
    
    # Apply status filter if provided
    if status_filter != 'all':
        repairs = repairs.filter(queue_status=status_filter)
    
    # Get unique customers from filtered repairs
    customer_ids = repairs.values_list('customer_id', flat=True).distinct()
    customers = Customer.objects.filter(id__in=customer_ids)
    
    # Count customer-requested repairs
    requested_repairs_count = repairs.filter(queue_status='REQUESTED').count()
    
    # Paginate the repairs
    paginator = Paginator(repairs.order_by('-repair_date'), 15)  # Show 15 repairs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'technician_portal/repair_list.html', {
        'repairs': page_obj,
        'customers': customers,
        'customer_search': customer_search,
        'status_filter': status_filter,
        'requested_repairs_count': requested_repairs_count,
        'queue_choices': Repair.QUEUE_CHOICES,
        'is_admin': request.user.is_staff
    })

@technician_required
def repair_detail(request, repair_id):
    # First get the repair to check its status
    repair = get_object_or_404(Repair, id=repair_id)
    
    # For regular technicians
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to view repairs.")
            return redirect('technician_dashboard')
        
        # Allow any technician to view customer-requested repairs (unassigned queue)
        if repair.queue_status == 'REQUESTED':
            # Any technician can view customer-requested repairs
            pass
        else:
            # For all other statuses, only the assigned technician can view
            if repair.technician != request.user.technician:
                messages.error(request, "You don't have permission to view this repair.")
                return redirect('technician_dashboard')
    # else: Admins can view any repair (no additional check needed)
        
    return render(request, 'technician_portal/repair_detail.html', {
        'repair': repair,
        'TIME_ZONE': timezone.get_current_timezone_name(),
        'is_admin': request.user.is_staff
    })

@technician_required
def create_repair(request):
    if request.method == 'POST':
        form = RepairForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # For admin users, use the selected technician
            if request.user.is_staff:
                if form.cleaned_data.get('technician'):
                    # Set technician before saving
                    repair = form.save(commit=False)
                    repair.technician = form.cleaned_data.get('technician')
                    repair.save()
                    # Save the form to handle file uploads and many-to-many fields
                    form.save_m2m()
                    messages.success(request, f"Repair has been created and assigned to {repair.technician.user.get_full_name()}")
                else:
                    messages.error(request, "As an admin, you must select a technician to assign the repair to.")
                    return render(request, 'technician_portal/repair_form.html', {
                        'form': form,
                        'is_admin': True
                    })
            else:
                # Regular technicians create repairs assigned to themselves
                try:
                    # Set technician before saving
                    repair = form.save(commit=False)
                    repair.technician = request.user.technician
                    repair.save()
                    # Save the form to handle file uploads and many-to-many fields
                    form.save_m2m()
                    messages.success(request, "Repair has been created successfully.")
                except AttributeError:
                    messages.error(request, "You don't have a technician profile to create repairs.")
                    return redirect('technician_dashboard')
            
            return redirect('repair_detail', repair_id=repair.id)
        else:
            logger.debug(f"Form errors: {form.errors}")
            # Add form errors to messages so user can see them
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Create a form with the current user
        form = RepairForm(user=request.user)
    
    pending_repair_warning = form.errors.get('__all__')
    return render(request, 'technician_portal/repair_form.html', {
        'form': form,
        'pending_repair_warning': pending_repair_warning,
        'is_admin': request.user.is_staff
    })

@technician_required
def update_repair(request, repair_id):
    # For regular technicians, they can only edit their own repairs
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to manage repairs.")
            return redirect('technician_dashboard')
            
        repair = get_object_or_404(Repair, id=repair_id, technician=request.user.technician)
        
        # Check if repair is editable (not completed or in certain stages)
        if repair.queue_status in ['COMPLETED', 'APPROVED']:
            messages.warning(request, "This repair cannot be edited in its current state. Please contact an administrator for assistance.")
            return redirect('repair_detail', repair_id=repair.id)
    else:
        # Admins can edit any repair
        repair = get_object_or_404(Repair, id=repair_id)
    
    if request.method == 'POST':
        form = RepairForm(request.POST, request.FILES, instance=repair, user=request.user)
        if form.is_valid():
            updated_repair = form.save(commit=False)
            
            # For admin users, update the technician if changed
            if request.user.is_staff and form.cleaned_data.get('technician'):
                updated_repair.technician = form.cleaned_data.get('technician')
            
            # Save the repair with all form data including uploaded files
            updated_repair.save()
            # Also save many-to-many fields if any exist
            form.save_m2m()
            
            messages.success(request, "Repair has been updated successfully.")
            return redirect('repair_detail', repair_id=repair.id)
    else:
        form = RepairForm(instance=repair, user=request.user)
    
    return render(request, 'technician_portal/repair_form.html', {
        'form': form, 
        'repair': repair,
        'is_admin': request.user.is_staff
    })

@technician_required
def update_queue_status(request, repair_id):
    # First get the repair to check its status
    repair = get_object_or_404(Repair, id=repair_id)
    
    # For regular technicians
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to update repairs.")
            return redirect('technician_dashboard')
        
        # Allow any technician to update customer-requested repairs
        if repair.queue_status == 'REQUESTED':
            # When accepting a customer request, assign it to this technician
            if request.POST.get('status') == 'APPROVED':
                repair.technician = request.user.technician
        else:
            # For all other statuses, only the assigned technician can update
            if repair.technician != request.user.technician:
                messages.error(request, "You don't have permission to update this repair.")
                return redirect('technician_dashboard')
    # else: Admins can update any repair (no additional check needed)
        
    old_status = repair.queue_status
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Repair.QUEUE_CHOICES):
            # Special handling for customer-requested repairs
            if old_status == 'REQUESTED' and new_status == 'APPROVED':
                repair.queue_status = new_status
                repair.save()
                
                # Create an automatic approval record since the customer already implicitly approved it
                from apps.customer_portal.models import CustomerUser, RepairApproval
                from django.utils import timezone
                
                # Find the customer user who would be the primary contact
                customer_users = CustomerUser.objects.filter(customer=repair.customer)
                customer_user = customer_users.filter(is_primary_contact=True).first()
                if not customer_user and customer_users.exists():
                    customer_user = customer_users.first()
                
                if customer_user:
                    # Create an approval record
                    RepairApproval.objects.create(
                        repair=repair,
                        approved=True,
                        approved_by=customer_user,
                        approval_date=timezone.now(),
                        notes="Auto-approved as customer initiated the request"
                    )
                
                messages.success(request, f"Repair request has been accepted and added to your schedule. The customer has been notified.")
            else:
                repair.queue_status = new_status
                # Auto-update repair date when marking as completed
                if new_status == 'COMPLETED':
                    from django.utils import timezone
                    repair.repair_date = timezone.now()
                repair.save()
                messages.success(request, f"Repair status updated to {repair.get_queue_status_display()}")
                
    return redirect('repair_detail', repair_id=repair.id)

@technician_required
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

@admin_required
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

@technician_required
def customer_list(request):
    """View to list all customers that a technician can access"""
    if request.user.is_staff:
        # Admin can see all customers
        customers = Customer.objects.all().order_by('name')
    else:
        # Regular technicians can only see customers with repairs assigned to them
        if hasattr(request.user, 'technician'):
            technician = request.user.technician
            # Get customer IDs from repairs assigned to this technician
            customer_ids = Repair.objects.filter(technician=technician).values_list('customer_id', flat=True).distinct()
            customers = Customer.objects.filter(id__in=customer_ids).order_by('name')
        else:
            customers = Customer.objects.none()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Annotate each customer with active repairs count
    for customer in customers:
        active_repairs = Repair.objects.filter(
            customer=customer
        ).exclude(
            queue_status='COMPLETED'
        ).count()
        customer.active_repairs_count = active_repairs
    
    return render(request, 'technician_portal/customer_list.html', {
        'customers': customers,
        'search_query': search_query,
        'is_admin': request.user.is_staff
    })

@technician_required
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

@technician_required
def unit_details(request, customer_id, unit_number):
    technician = get_object_or_404(Technician, user=request.user)
    customer = get_object_or_404(Customer, id=customer_id)
    repairs = Repair.objects.filter(technician=technician, customer=customer, unit_number=unit_number)

    return render(request, 'technician_portal/unit_details.html', {
        'customer': customer,
        'unit_number': unit_number,
        'repairs': repairs,
    })

@technician_required
def mark_unit_replaced(request, customer_id, unit_number):
    customer = get_object_or_404(Customer, id=customer_id)
    unit_repair_count = get_object_or_404(UnitRepairCount, customer=customer, unit_number=unit_number)
    unit_repair_count.repair_count = 0
    unit_repair_count.save()
    messages.success(request, f"Unit #{unit_number} for {customer.name} has been marked as replaced. Repair count reset to 0.")
    return redirect('customer_detail', customer_id=customer_id)

from django.http import JsonResponse

@technician_required
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

@technician_required
def reward_fulfillment_detail(request, redemption_id):
    """View details of a reward redemption and mark as fulfilled"""
    # Get the technician
    technician = get_object_or_404(Technician, user=request.user)
    
    # Get the redemption
    from apps.rewards_referrals.models import RewardRedemption
    
    # Any technician can view reward details, but actions depend on assignment
    redemption = get_object_or_404(RewardRedemption, id=redemption_id)
    
    # Check if current technician is assigned to this redemption
    is_assigned_technician = (redemption.assigned_technician == technician)
    is_admin = request.user.is_staff
    can_fulfill = is_assigned_technician or is_admin
    
    # Get customer repairs for applying reward
    customer_repairs = []
    if redemption.reward and redemption.reward.customer_user and redemption.reward.customer_user.user:
        customer_email = redemption.reward.customer_user.user.email
        try:
            customer = Customer.objects.get(email=customer_email)
            customer_repairs = Repair.objects.filter(
                customer=customer,
                queue_status__in=['APPROVED', 'IN_PROGRESS']
            ).order_by('-repair_date')
        except Customer.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Only assigned technicians or admins can fulfill rewards
        if not can_fulfill:
            messages.error(request, "You don't have permission to fulfill this reward. Only the assigned technician or administrators can fulfill rewards.")
            return redirect('technician_dashboard')
        
        # Handle claim assignment action
        action = request.POST.get('action')
        if action == 'claim' and not redemption.assigned_technician:
            redemption.assigned_technician = technician
            redemption.save()
            messages.success(request, f'You have claimed the reward: {redemption.reward_option.name}')
            return redirect('reward_fulfillment_detail', redemption_id=redemption.id)
        
        # Process fulfillment
        notes = request.POST.get('notes', '')
        
        # Check if a repair was selected to apply the reward to
        repair_id = request.POST.get('apply_to_repair')
        if repair_id:
            try:
                repair = Repair.objects.get(id=repair_id)
                redemption.applied_to_repair = repair
            except Repair.DoesNotExist:
                pass
        
        from apps.rewards_referrals.services import RewardFulfillmentService
        RewardFulfillmentService.mark_as_fulfilled(redemption, technician, notes)
        
        messages.success(request, f'Reward {redemption.reward_option.name} has been marked as fulfilled.')
        return redirect('technician_dashboard')
    
    return render(request, 'technician_portal/reward_fulfillment.html', {
        'redemption': redemption,
        'customer_repairs': customer_repairs,
        'is_assigned_technician': is_assigned_technician,
        'can_fulfill': can_fulfill,
        'current_technician': technician,
        'is_admin': is_admin,
    })

@technician_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(TechnicianNotification, id=notification_id)
    
    # Ensure the notification belongs to this technician
    if notification.technician.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to access this notification.")
        return redirect('technician_dashboard')
    
    notification.read = True
    notification.save()
    
    # If notification is for a redemption, redirect to the redemption
    if notification.redemption:
        return redirect('reward_fulfillment_detail', redemption_id=notification.redemption.id)
    
    return redirect('technician_dashboard')

@technician_required
def apply_reward_to_repair(request, repair_id):
    """Apply a reward redemption to a specific repair"""
    # Get the repair
    if request.user.is_staff:
        repair = get_object_or_404(Repair, id=repair_id)
    else:
        # Non-admin technicians can only access their own repairs
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile.")
            return redirect('technician_dashboard')
        repair = get_object_or_404(Repair, id=repair_id, technician=request.user.technician)
    
    if request.method == 'POST':
        redemption_id = request.POST.get('redemption_id')
        auto_fulfill = request.POST.get('auto_fulfill') == 'on'
        
        if not redemption_id:
            messages.error(request, "No reward selected")
            return redirect('repair_detail', repair_id=repair.id)
        
        # Get the redemption
        from apps.rewards_referrals.models import RewardRedemption
        redemption = get_object_or_404(RewardRedemption, id=redemption_id)
        
        # Validate that the reward belongs to the customer of this repair
        from apps.customer_portal.models import CustomerUser
        customer_users = CustomerUser.objects.filter(customer=repair.customer)
        reward_customer_user = redemption.reward.customer_user
        
        if not customer_users.filter(id=reward_customer_user.id).exists():
            messages.error(request, "This reward belongs to a different customer and cannot be applied to this repair.")
            return redirect('repair_detail', repair_id=repair.id)
        
        # Apply the reward to the repair
        success, message = repair.apply_reward(
            redemption,
            technician=getattr(request.user, 'technician', None),
            auto_fulfill=auto_fulfill
        )
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('repair_detail', repair_id=repair.id)
    
    # GET request - show available rewards for this customer
    from apps.rewards_referrals.models import RewardRedemption
    from apps.customer_portal.models import CustomerUser
    
    # Find CustomerUser records for this customer
    customer_users = CustomerUser.objects.filter(customer=repair.customer)
    
    # Get all pending rewards for these customer users
    available_redemptions = RewardRedemption.objects.filter(
        reward__customer_user__in=customer_users,
        status='PENDING',
        applied_to_repair__isnull=True  # Not already applied
    ).select_related('reward_option', 'reward_option__reward_type')
    
    return render(request, 'technician_portal/apply_reward.html', {
        'repair': repair,
        'available_redemptions': available_redemptions,
    })
