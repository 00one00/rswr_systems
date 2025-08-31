from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from apps.technician_portal.forms import TechnicianRegistrationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection
import io
import sys

def health_check(request):
    """Health check endpoint for AWS load balancer - bypasses ALLOWED_HOSTS"""
    try:
        # Simple database connectivity test
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy', 
            'error': str(e)
        }, status=500)

def home(request):
    # The root page is now a marketing landing page
    # No automatic redirects for authenticated users
    return render(request, 'landing.html')

def customer_login_view(request):
    """Login view specifically for customers"""
    if request.user.is_authenticated:
        return redirect('customer_dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Verify user is a customer
                from apps.customer_portal.models import CustomerUser
                try:
                    customer_user = CustomerUser.objects.get(user=user)
                    login(request, user)
                    next_url = request.GET.get('next', 'customer_dashboard')
                    return redirect(next_url)
                except CustomerUser.DoesNotExist:
                    messages.error(request, "This account is not authorized for customer access.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'customer_login.html', {'form': form, 'portal_type': 'customer'})

def technician_login_view(request):
    """Login view specifically for technicians"""
    if request.user.is_authenticated:
        from apps.technician_portal.models import Technician
        try:
            technician = Technician.objects.get(user=request.user)
            return redirect('technician_dashboard')
        except Technician.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Verify user is a technician
                from apps.technician_portal.models import Technician
                try:
                    technician = Technician.objects.get(user=user)
                    login(request, user)
                    next_url = request.GET.get('next', 'technician_dashboard')
                    return redirect(next_url)
                except Technician.DoesNotExist:
                    messages.error(request, "This account is not authorized for technician access.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'technician_login.html', {'form': form, 'portal_type': 'technician'})

def login_router(request):
    """Legacy login URL that redirects to appropriate portal"""
    # Check if user is already authenticated
    if request.user.is_authenticated:
        from apps.customer_portal.models import CustomerUser
        from apps.technician_portal.models import Technician
        
        try:
            customer_user = CustomerUser.objects.get(user=request.user)
            return redirect('customer_dashboard')
        except CustomerUser.DoesNotExist:
            try:
                technician = Technician.objects.get(user=request.user)
                return redirect('technician_dashboard')
            except Technician.DoesNotExist:
                pass
    
    # For unauthenticated users, show portal selection
    return render(request, 'login_router.html')

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

@csrf_exempt
def setup_database(request):
    """Setup database with migrations and create superuser"""
    if request.method != 'POST':
        return HttpResponse("""
        <html>
        <body>
            <h1>Database Setup</h1>
            <p>Click the button below to set up the database:</p>
            <form method="post">
                <button type="submit">Setup Database</button>
            </form>
        </body>
        </html>
        """)
    
    # Capture output
    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output
    
    try:
        # Run migrations
        call_command('migrate', verbosity=1, interactive=False)
        print("Migrations completed successfully")
        
        # Create superuser if it doesn't exist
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print("Superuser 'admin' created successfully")
        else:
            print("Superuser 'admin' already exists")
        
        # Collect static files
        call_command('collectstatic', verbosity=1, interactive=False)
        print("Static files collected successfully")
        
        print("Database setup completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sys.stdout = old_stdout
    
    result = output.getvalue()
    
    return HttpResponse(f"""
    <html>
    <body>
        <h1>Database Setup Results</h1>
        <pre>{result}</pre>
        <p><a href="/">Return to Home</a></p>
        <p><a href="/admin/">Go to Admin</a> (username: admin, password: admin123)</p>
    </body>
    </html>
    """)
