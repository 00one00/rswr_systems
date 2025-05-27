from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from apps.technician_portal.forms import TechnicianRegistrationForm
from django.contrib import messages
from django.http import HttpResponse
from django.core.management import call_command
from django.contrib.auth import get_user_model
import io
import sys

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
