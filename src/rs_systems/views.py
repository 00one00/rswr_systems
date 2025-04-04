from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from apps.technician_portal.forms import TechnicianRegistrationForm
from django.contrib import messages

def home(request):
    if request.user.is_authenticated:
        # Check if the user is a customer or technician
        from apps.customer_portal.models import CustomerUser
        from apps.technician_portal.models import Technician
        
        # Try to get customer user record
        try:
            customer_user = CustomerUser.objects.get(user=request.user)
            return redirect('customer_dashboard')
        except CustomerUser.DoesNotExist:
            # If not a customer, check if technician
            try:
                technician = Technician.objects.get(user=request.user)
                return redirect('technician_dashboard')
            except Technician.DoesNotExist:
                # If neither, show a warning
                messages.warning(request, "Your account is not linked to a customer or technician profile.")
    
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check if the user is a customer or technician
                from apps.customer_portal.models import CustomerUser
                from apps.technician_portal.models import Technician
                
                # Try to get customer user record
                try:
                    customer_user = CustomerUser.objects.get(user=user)
                    return redirect('customer_dashboard')
                except CustomerUser.DoesNotExist:
                    # If not a customer, check if technician
                    try:
                        technician = Technician.objects.get(user=user)
                        return redirect('technician_dashboard')
                    except Technician.DoesNotExist:
                        # If neither, redirect to a default page
                        messages.warning(request, "Your account is not linked to a customer or technician profile.")
                        return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')

@staff_member_required
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
