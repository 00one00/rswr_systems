from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Technician, Repair, UnitRepairCount, TechnicianNotification
from core.models import Customer
from .forms import TechnicianForm, RepairForm, CustomerForm, TechnicianRegistrationForm
from django.db.models import Count, F, Q
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from collections import defaultdict
from apps.customer_portal.models import RepairApproval, CustomerUser, CustomerRepairPreference
from apps.rewards_referrals.models import RewardRedemption
from apps.rewards_referrals.services import RewardFulfillmentService
import logging
from django.core.paginator import Paginator
from functools import wraps
from common.utils import convert_heic_to_jpeg

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

def is_working_manager(user):
    """
    Helper function to check if a user is a working manager.
    A working manager is someone who:
    1. Has a technician profile AND
    2. Has is_manager=True flag

    This allows them to both assign work AND complete repairs themselves.
    """
    if not hasattr(user, 'technician'):
        return False
    try:
        technician = user.technician
        return technician is not None and technician.is_manager
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
    
    # Get customer-requested repairs (ONLY for managers)
    if technician:
        # Only MANAGERS can see REQUESTED repairs (for assignment purposes)
        # Regular technicians should NOT see these
        if technician.is_manager:
            customer_requested_repairs = Repair.objects.filter(
                queue_status='REQUESTED'
            ).order_by('-repair_date')
        else:
            customer_requested_repairs = Repair.objects.none()
        
        # Get assigned reward redemptions for this technician
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

        # Get recently approved repairs for this technician (approved in last 24 hours)
        recent_approvals = RepairApproval.objects.filter(
            approved=True,
            approval_date__gte=timezone.now() - timedelta(hours=24)
        ).values_list('repair_id', flat=True)

        recently_approved_repairs = Repair.objects.filter(
            id__in=recent_approvals,
            technician=technician,
            queue_status='APPROVED'
        ).select_related('customer').order_by('-repair_date')[:5]  # Limit to 5 most recent
    else:
        # For admins without a technician profile, show all requested repairs (for assignment)
        customer_requested_repairs = Repair.objects.filter(
            queue_status='REQUESTED'
        ).order_by('-repair_date')

        # For admins, show all pending redemptions
        assigned_redemptions = []
        all_pending_redemptions = RewardRedemption.objects.filter(
            status='PENDING'
        ).order_by('-created_at')

        unread_notifications = None
        recently_approved_repairs = Repair.objects.none()
    
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
        'recently_approved_repairs': recently_approved_repairs,
        'is_admin': is_admin,
        'admin_data': admin_data,
    })

@technician_required
def repair_list(request):
    # For regular technicians, only show their repairs or their team's repairs if they're a manager
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to view repairs.")
            return redirect('technician_dashboard')

        technician = request.user.technician

        # If manager, show their team's repairs + their own + REQUESTED repairs
        if technician.is_manager:
            # Get repairs for managed technicians + own repairs
            managed_tech_ids = list(technician.managed_technicians.values_list('id', flat=True))
            managed_tech_ids.append(technician.id)  # Include own repairs
            repairs = Repair.objects.filter(
                Q(technician_id__in=managed_tech_ids) | Q(queue_status='REQUESTED')
            )
        else:
            # Regular technician - only their own repairs, EXCLUDING REQUESTED and PENDING
            repairs = Repair.objects.filter(
                technician=technician
            ).exclude(queue_status__in=['REQUESTED', 'PENDING'])
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
    
    # Group repairs by customer and unit number for better organization
    grouped_repairs = defaultdict(lambda: defaultdict(list))
    
    # Order repairs by date (newest first) for grouping
    ordered_repairs = repairs.order_by('-repair_date')
    
    for repair in ordered_repairs:
        grouped_repairs[repair.customer][repair.unit_number].append(repair)
    
    # Convert to regular dict for template
    repair_groups = {}
    for customer, units in grouped_repairs.items():
        repair_groups[customer] = dict(units)
    
    # For pagination, we'll paginate the customers instead of individual repairs
    customers_with_repairs = list(repair_groups.keys())
    paginator = Paginator(customers_with_repairs, 10)  # Show 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get repair groups for current page customers
    page_repair_groups = {customer: repair_groups[customer] for customer in page_obj}
    
    return render(request, 'technician_portal/repair_list.html', {
        'repair_groups': page_repair_groups,
        'customers': customers,
        'customer_search': customer_search,
        'status_filter': status_filter,
        'requested_repairs_count': requested_repairs_count,
        'queue_choices': Repair.QUEUE_CHOICES,
        'is_admin': request.user.is_staff,
        'page_obj': page_obj,  # For pagination
        'total_repairs': ordered_repairs.count()
    })

@technician_required
def repair_detail(request, repair_id):
    # First get the repair to check its status
    repair = get_object_or_404(Repair, id=repair_id)

    # Initialize permission flags
    can_update_status = False
    can_assign_repair = False
    can_reassign_to_self = False
    technician = None

    # For regular technicians
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to view repairs.")
            return redirect('technician_dashboard')

        technician = request.user.technician

        # BLOCK all techs from viewing PENDING repairs (customer approval only)
        if repair.queue_status == 'PENDING':
            messages.error(request, "This repair is pending customer approval and cannot be viewed by technicians.")
            return redirect('technician_dashboard')

        # Only MANAGERS can view REQUESTED repairs (for assignment or self-completion)
        if repair.queue_status == 'REQUESTED':
            if not technician.is_manager:
                messages.error(request, "Only managers can view customer-requested repairs.")
                return redirect('technician_dashboard')
            # Working managers can update REQUESTED repairs directly
            can_update_status = True
            can_assign_repair = True
        else:
            # Check if technician can view this repair
            can_view = False

            # Can view own repairs
            if repair.technician == technician:
                can_view = True
                can_update_status = True  # Can update own repairs
            # Managers can view repairs from their managed technicians
            elif technician.is_manager and repair.technician and technician.manages_technician(repair.technician):
                can_view = True
                can_reassign_to_self = True  # Manager can reassign team repair to themselves
            # Special case: viewing from form warning link
            elif '/create/' in request.META.get('HTTP_REFERER', '') or '/update/' in request.META.get('HTTP_REFERER', ''):
                can_view = True

            if not can_view:
                messages.error(request, "You don't have permission to view this repair.")
                return redirect('technician_dashboard')
    else:
        # Admins can do everything
        can_update_status = True
        can_assign_repair = repair.queue_status == 'REQUESTED'

    return render(request, 'technician_portal/repair_detail.html', {
        'repair': repair,
        'TIME_ZONE': timezone.get_current_timezone_name(),
        'is_admin': request.user.is_staff,
        'can_update_status': can_update_status,
        'can_assign_repair': can_assign_repair,
        'can_reassign_to_self': can_reassign_to_self,
        'technician': technician,
    })

@technician_required
def create_repair(request):
    if request.method == 'POST':
        # Convert HEIC images to JPEG for browser compatibility
        if 'damage_photo_before' in request.FILES:
            request.FILES['damage_photo_before'] = convert_heic_to_jpeg(request.FILES['damage_photo_before'])
        if 'damage_photo_after' in request.FILES:
            request.FILES['damage_photo_after'] = convert_heic_to_jpeg(request.FILES['damage_photo_after'])

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

                    # SECURITY: Check customer preferences for ALL tech-created repairs
                    # Technicians cannot bypass approval by setting status to anything other than PENDING
                    # Only customer REQUESTED repairs (created by customers) should skip this check

                    # Force check customer preferences regardless of what status tech tried to set
                    try:
                        preferences = repair.customer.repair_preferences
                        # Check if repair should be auto-approved
                        if preferences.should_auto_approve(repair.technician, repair.repair_date.date() if repair.repair_date else None):
                            repair.queue_status = 'APPROVED'
                            messages.info(request, "Repair auto-approved based on customer preferences.")
                        else:
                            # Force to PENDING - customer must approve
                            # This prevents technicians from setting status to COMPLETED/APPROVED to bypass approval
                            repair.queue_status = 'PENDING'
                            messages.warning(request, "This customer requires approval for field repairs. Repair submitted for customer approval.")
                    except CustomerRepairPreference.DoesNotExist:
                        # No preferences set - default to requiring approval for security
                        repair.queue_status = 'PENDING'
                        messages.warning(request, "Repair submitted for customer approval (customer preferences not configured).")

                    repair.save()
                    # Save the form to handle file uploads and many-to-many fields
                    form.save_m2m()
                except AttributeError:
                    messages.error(request, "You don't have a technician profile to create repairs.")
                    return redirect('technician_dashboard')

            # Add success message
            messages.success(request, f'Repair #{repair.id} created successfully!')

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

    # Calculate expected cost for the template if we have customer/unit info
    expected_cost = None
    if hasattr(form, 'instance') and form.instance.customer and form.instance.unit_number:
        expected_cost = form.instance.get_expected_price()

    return render(request, 'technician_portal/repair_form.html', {
        'form': form,
        'pending_repair_warning': pending_repair_warning,
        'is_admin': request.user.is_staff,
        'expected_cost': expected_cost
    })

@technician_required
def update_repair(request, repair_id):
    logger = logging.getLogger(__name__)

    # For regular technicians, they can only edit their own repairs
    if not request.user.is_staff:
        # Ensure user has a technician profile
        if not hasattr(request.user, 'technician'):
            messages.error(request, "You don't have a technician profile to manage repairs.")
            return redirect('technician_dashboard')

        # First get the repair WITHOUT filtering by technician (to avoid crash on NULL technician)
        repair = get_object_or_404(Repair, id=repair_id)
        logger.info(f"UPDATE_REPAIR: Got repair #{repair.id}, technician_id={repair.technician_id}")

        # SECURITY: Check if repair is in a final/locked state
        if repair.queue_status in ['COMPLETED', 'DENIED']:
            messages.error(request, "This repair is closed and cannot be edited.")
            return redirect('repair_detail', repair_id=repair.id)

        # SECURITY: Check if technician is assigned to this repair
        # Customer-submitted repairs (REQUESTED) have no technician yet - block editing
        # Use technician_id to avoid RelatedObjectDoesNotExist error
        if not repair.technician_id:
            messages.error(request, "This repair has not been assigned yet and cannot be edited by technicians.")
            return redirect('repair_detail', repair_id=repair.id)

        # SECURITY: Only allow editing own repairs
        if repair.technician_id != request.user.technician.id:
            messages.error(request, "You can only edit repairs assigned to you.")
            return redirect('repair_detail', repair_id=repair.id)
    else:
        # Admins can edit any repair
        repair = get_object_or_404(Repair, id=repair_id)
    
    if request.method == 'POST':
        logger.info(f"UPDATE_REPAIR POST: Processing form for repair #{repair.id}")

        # Convert HEIC images to JPEG for browser compatibility
        if 'damage_photo_before' in request.FILES:
            request.FILES['damage_photo_before'] = convert_heic_to_jpeg(request.FILES['damage_photo_before'])
        if 'damage_photo_after' in request.FILES:
            request.FILES['damage_photo_after'] = convert_heic_to_jpeg(request.FILES['damage_photo_after'])

        # CRITICAL FIX: Save the technician_id BEFORE creating the form
        # because form.save(commit=False) will modify the original instance
        original_technician_id = repair.technician_id
        logger.info(f"UPDATE_REPAIR: Saved original_technician_id={original_technician_id}")

        form = RepairForm(request.POST, request.FILES, instance=repair, user=request.user)
        if form.is_valid():
            logger.info(f"UPDATE_REPAIR: Form is valid, calling save(commit=False)")
            updated_repair = form.save(commit=False)
            logger.info(f"UPDATE_REPAIR: After form.save(), updated_repair.technician_id={updated_repair.technician_id}")

            # Handle photo deletion
            for field_name in ['damage_photo_before', 'damage_photo_after']:
                delete_flag = request.POST.get(f'{field_name}-DELETE')
                if delete_flag == 'true':
                    # Delete the photo if it exists
                    current_photo = getattr(updated_repair, field_name)
                    if current_photo:
                        current_photo.delete(save=False)  # Delete the file
                        setattr(updated_repair, field_name, None)  # Clear the field

            # For non-admin users, preserve the existing technician (form hides this field)
            if not request.user.is_staff:
                # CRITICAL FIX: form.save(commit=False) sets technician to NULL when field is hidden
                # We must restore the original technician_id that we saved before creating the form
                logger.info(f"UPDATE_REPAIR: Restoring technician_id from original_technician_id={original_technician_id}")
                updated_repair.technician_id = original_technician_id
                logger.info(f"UPDATE_REPAIR: Set updated_repair.technician_id={updated_repair.technician_id}")
            # For admin users, update the technician if changed
            elif form.cleaned_data.get('technician'):
                updated_repair.technician = form.cleaned_data.get('technician')

            # Save the repair with all form data including uploaded files
            logger.info(f"UPDATE_REPAIR: About to save repair, technician_id={updated_repair.technician_id}")
            updated_repair.save()
            logger.info(f"UPDATE_REPAIR: Save successful!")
            # Also save many-to-many fields if any exist
            form.save_m2m()
            
            messages.success(request, "Repair has been updated successfully.")
            return redirect('repair_detail', repair_id=repair.id)
    else:
        form = RepairForm(instance=repair, user=request.user)
    
    # Calculate expected cost for the template
    expected_cost = repair.get_expected_price() if repair.customer and repair.unit_number else None

    return render(request, 'technician_portal/repair_form.html', {
        'form': form,
        'repair': repair,
        'is_admin': request.user.is_staff,
        'expected_cost': expected_cost
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

        technician = request.user.technician

        # BLOCK all techs from PENDING repairs (customer approval only)
        if repair.queue_status == 'PENDING':
            messages.error(request, "This repair is pending customer approval. Technicians cannot modify it.")
            return redirect('technician_dashboard')

        # Only MANAGERS can handle REQUESTED repairs
        # Working managers can update REQUESTED repairs directly (auto-assigns to them)
        if repair.queue_status == 'REQUESTED':
            if not technician.is_manager:
                messages.error(request, "Only managers can assign customer-requested repairs.")
                return redirect('technician_dashboard')
            # If manager is updating a REQUESTED repair, allow it (will auto-assign to manager)
        else:
            # Check if technician can update this repair
            can_update = False

            # Can update own repairs (assigned to them)
            if repair.technician == technician:
                can_update = True
            # Managers can only update team repairs if they've been reassigned to the manager
            # They cannot directly modify repairs assigned to other team members
            elif technician.is_manager and repair.technician and technician.manages_technician(repair.technician):
                # If repair is assigned to a team member (not the manager), block modification
                messages.error(request, "You cannot modify repairs assigned to other technicians. Use the reassign feature to take over this repair.")
                return redirect('repair_detail', repair_id=repair.id)

            if not can_update:
                messages.error(request, "You don't have permission to update this repair.")
                return redirect('technician_dashboard')
    # else: Admins can update any repair (no additional check needed)
        
    old_status = repair.queue_status
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Repair.QUEUE_CHOICES):
            # Special handling for customer-requested repairs
            if old_status == 'REQUESTED':
                # Auto-assign to the manager who is accepting the repair
                if not request.user.is_staff and hasattr(request.user, 'technician'):
                    repair.technician = request.user.technician
                    messages.info(request, f"Repair assigned to you.")

                # Update status
                repair.queue_status = new_status
                repair.save()

                # Create an automatic approval record since the customer already implicitly approved it

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
                    repair.repair_date = timezone.now()

                    # Handle price override if provided
                    cost_override = request.POST.get('cost_override')
                    override_reason = request.POST.get('override_reason')

                    if cost_override:
                        try:
                            repair.cost_override = float(cost_override)
                            repair.override_reason = override_reason or "Manual price adjustment"
                            messages.info(request, f"Custom price of ${cost_override} has been applied.")
                        except (ValueError, TypeError):
                            messages.warning(request, "Invalid custom price. Using automatic pricing.")

                repair.save()
                messages.success(request, f"Repair status updated to {repair.get_queue_status_display()}")
                
    return redirect('repair_detail', repair_id=repair.id)

@technician_required
def update_technician_profile(request):
    technician = get_object_or_404(Technician, user=request.user)

    if request.method == 'POST':
        form = TechnicianForm(request.POST, user=request.user, technician=technician)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')

            # If password was changed, update session to prevent logout
            if form.cleaned_data.get('password1'):
                update_session_auth_hash(request, request.user)
                messages.info(request, 'Your password has been changed successfully.')

            return redirect('technician_dashboard')
    else:
        form = TechnicianForm(user=request.user, technician=technician)

    return render(request, 'technician_portal/update_profile.html', {
        'form': form,
        'technician': technician
    })

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

    # Only show repairs assigned to this technician, exclude REQUESTED and PENDING
    repairs = Repair.objects.filter(
        technician=technician,
        customer=customer
    ).exclude(queue_status__in=['REQUESTED', 'PENDING'])

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

    # Only show repairs assigned to this technician, exclude REQUESTED and PENDING
    repairs = Repair.objects.filter(
        technician=technician,
        customer=customer,
        unit_number=unit_number
    ).exclude(queue_status__in=['REQUESTED', 'PENDING'])

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
def assign_repair(request, repair_id):
    """Manager assigns a REQUESTED repair to a technician"""
    # Only managers can assign repairs
    if not request.user.is_staff:
        if not hasattr(request.user, 'technician') or not request.user.technician.is_manager:
            messages.error(request, "Only managers can assign repairs.")
            return redirect('technician_dashboard')

    repair = get_object_or_404(Repair, id=repair_id)

    # Can only assign REQUESTED repairs
    if repair.queue_status != 'REQUESTED':
        messages.error(request, "Only REQUESTED repairs can be assigned. This repair is already assigned.")
        return redirect('repair_detail', repair_id=repair.id)

    if request.method == 'POST':
        technician_id = request.POST.get('technician_id')

        if not technician_id:
            messages.error(request, "Please select a technician.")
            return redirect('assign_repair', repair_id=repair.id)

        try:
            assigned_tech = Technician.objects.get(id=technician_id)

            # If regular manager (not admin), verify they manage this technician OR assigning to themselves
            if not request.user.is_staff:
                manager = request.user.technician
                # Allow if assigning to themselves OR to a technician they manage
                if assigned_tech.id != manager.id and not manager.manages_technician(assigned_tech):
                    messages.error(request, "You can only assign repairs to yourself or technicians you manage.")
                    return redirect('assign_repair', repair_id=repair.id)

            # Assign the repair
            repair.technician = assigned_tech
            repair.queue_status = 'APPROVED'  # Customer already approved by requesting
            repair.save()

            # Create approval record

            customer_users = CustomerUser.objects.filter(customer=repair.customer)
            customer_user = customer_users.filter(is_primary_contact=True).first()
            if not customer_user and customer_users.exists():
                customer_user = customer_users.first()

            if customer_user:
                RepairApproval.objects.create(
                    repair=repair,
                    approved=True,
                    approved_by=customer_user,
                    approval_date=timezone.now(),
                    notes="Auto-approved - customer requested repair"
                )

            # Create notification for assigned technician
            TechnicianNotification.objects.create(
                technician=assigned_tech,
                message=f"You have been assigned Repair #{repair.id} for {repair.customer.name} - Unit {repair.unit_number}",
                read=False,
                repair=repair
            )

            messages.success(request, f"Repair #{repair.id} assigned to {assigned_tech.user.get_full_name()}")
            return redirect('repair_detail', repair_id=repair.id)

        except Technician.DoesNotExist:
            messages.error(request, "Selected technician not found.")
            return redirect('assign_repair', repair_id=repair.id)

    # GET request - show assignment form
    if request.user.is_staff:
        # Admins can assign to any technician
        available_technicians = Technician.objects.filter(is_active=True).order_by('user__first_name')
    else:
        # Managers can assign to technicians they manage OR to themselves
        manager = request.user.technician
        # Get managed technicians
        managed_techs = manager.managed_technicians.filter(is_active=True)
        # Include the manager themselves in the list
        available_technicians = Technician.objects.filter(
            Q(id=manager.id) | Q(id__in=managed_techs)
        ).filter(is_active=True).order_by('user__first_name')

    return render(request, 'technician_portal/assign_repair.html', {
        'repair': repair,
        'available_technicians': available_technicians,
    })

@technician_required
def reassign_to_self(request, repair_id):
    """Manager reassigns a team member's repair to themselves"""
    # Only managers can reassign repairs
    if not request.user.is_staff:
        if not hasattr(request.user, 'technician') or not request.user.technician.is_manager:
            messages.error(request, "Only managers can reassign repairs.")
            return redirect('technician_dashboard')

    repair = get_object_or_404(Repair, id=repair_id)

    # Verify user has permission
    if not request.user.is_staff:
        manager = request.user.technician

        # Check if repair is assigned to one of their managed technicians
        if not repair.technician or not manager.manages_technician(repair.technician):
            messages.error(request, "You can only reassign repairs from your managed technicians.")
            return redirect('repair_detail', repair_id=repair.id)

        # Cannot reassign if already assigned to themselves
        if repair.technician.id == manager.id:
            messages.error(request, "This repair is already assigned to you.")
            return redirect('repair_detail', repair_id=repair.id)

    if request.method == 'POST':
        old_technician = repair.technician

        if not request.user.is_staff:
            # Reassign to the manager
            repair.technician = request.user.technician
            repair.save()

            messages.success(request, f"Repair reassigned from {old_technician.user.get_full_name()} to you.")

            # Create notification for the old technician
            TechnicianNotification.objects.create(
                technician=old_technician,
                message=f"Repair #{repair.id} for {repair.customer.name} - Unit {repair.unit_number} has been reassigned to {request.user.get_full_name()}",
                read=False,
                repair=repair
            )
        else:
            # Admins would use the regular assign_repair view
            messages.info(request, "Admins should use the regular assignment interface.")
            return redirect('assign_repair', repair_id=repair.id)

        return redirect('repair_detail', repair_id=repair.id)

    # GET request - show confirmation
    return render(request, 'technician_portal/reassign_to_self.html', {
        'repair': repair,
    })

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
        redemption = get_object_or_404(RewardRedemption, id=redemption_id)
        
        # Validate that the reward belongs to the customer of this repair
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
