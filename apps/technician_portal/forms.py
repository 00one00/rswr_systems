from django import forms
from .models import Technician, Repair, Customer, UnitRepairCount
from django.utils import timezone
from django.forms.widgets import DateTimeInput
import logging

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Technician, Repair, Customer, UnitRepairCount
from django.utils import timezone
from django.forms.widgets import DateTimeInput
from django.db import transaction
import logging
logger = logging.getLogger(__name__)

class TechnicianForm(forms.Form):
    """
    Form for technicians to update their profile.
    Combines User and Technician model fields.
    Expertise is read-only (only admins can change it).
    """
    # User fields (editable)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)

    # Technician fields (editable)
    phone_number = forms.CharField(max_length=15, required=False)

    # Password fields (optional)
    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank if you don't want to change your password."
    )
    password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput,
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.technician = kwargs.pop('technician', None)
        super().__init__(*args, **kwargs)

        # Pre-populate fields if instances provided
        if self.user and not kwargs.get('data'):
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            self.fields['username'].initial = self.user.username

        if self.technician and not kwargs.get('data'):
            self.fields['phone_number'].initial = self.technician.phone_number

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username is taken by another user
        if self.user:
            if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
                raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # If password fields are provided, validate they match
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match.")
            if password1 and len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")

        return cleaned_data

    def save(self):
        """Save both User and Technician data"""
        if not self.user or not self.technician:
            raise ValueError("User and Technician instances required")

        # Update User fields
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.username = self.cleaned_data['username']

        # Update password if provided
        if self.cleaned_data.get('password1'):
            self.user.set_password(self.cleaned_data['password1'])

        self.user.save()

        # Update Technician fields
        self.technician.phone_number = self.cleaned_data['phone_number']
        self.technician.save()

        return self.user


class TechnicianRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    expertise = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create the technician profile
            Technician.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                expertise=self.cleaned_data['expertise']
            )
        return user
    
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name']

class CustomDateTimeInput(DateTimeInput):
    input_type = 'datetime-local'
    def __init__(self, attrs=None, format=None):
        super().__init__(attrs={'step': '60', **(attrs or {})}, format='%Y-%m-%dT%H:%M')

class RepairForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all().order_by('name'))
    technician = forms.ModelChoiceField(
        queryset=Technician.objects.all(),
        required=False,  # Not required because it might be set automatically for non-admin users
        help_text="Only required for admin users. Regular technicians will be automatically assigned."
    )
    repair_date = forms.DateTimeField(
        widget=CustomDateTimeInput()
    )
    damage_type = forms.ChoiceField(
        choices=[],  # Will be set in __init__
        required=False,
        help_text="Select the type of windshield damage"
    )

    class Meta:
        model = Repair
        fields = ['technician', 'customer', 'unit_number', 'repair_date', 'queue_status', 'damage_type',
                  'drilled_before_repair', 'windshield_temperature', 'resin_viscosity', 'damage_photo_before',
                  'damage_photo_after', 'customer_notes', 'technician_notes', 'cost_override', 'override_reason']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(RepairForm, self).__init__(*args, **kwargs)
        
        # Set the damage type choices
        self.fields['damage_type'].choices = Repair.DAMAGE_TYPE_CHOICES
        
        # Hide technician field for non-admin users
        if self.user and not self.user.is_staff:
            self.fields['technician'].widget = forms.HiddenInput()

        # Hide pricing override fields for non-managers
        if self.user and hasattr(self.user, 'technician'):
            technician = self.user.technician
            if not (technician.is_manager and technician.can_override_pricing):
                self.fields['cost_override'].widget = forms.HiddenInput()
                self.fields['override_reason'].widget = forms.HiddenInput()
        else:
            # Hide for users without technician profiles
            self.fields['cost_override'].widget = forms.HiddenInput()
            self.fields['override_reason'].widget = forms.HiddenInput()
        
        # Auto-populate repair_date for all repairs (new and existing)
        current_time = timezone.now()
        if self.instance and self.instance.pk:
            # This is an existing repair being edited - use existing date unless not completed
            if self.instance.queue_status != 'COMPLETED':
                self.fields['repair_date'].initial = current_time
        else:
            # This is a new repair - set initial date to current time
            self.fields['repair_date'].initial = current_time
            # Also set the widget value directly
            self.fields['repair_date'].widget.attrs['value'] = current_time.strftime('%Y-%m-%dT%H:%M')
        
        # Make customer_notes read-only for technicians - they should not modify customer input
        if 'customer_notes' in self.fields:
            self.fields['customer_notes'].widget.attrs['readonly'] = True
            self.fields['customer_notes'].help_text = "Notes provided by the customer (read-only)"
        
        # Add helpful labels for the note fields
        if 'technician_notes' in self.fields:
            self.fields['technician_notes'].help_text = "Add your internal notes about the repair process"
        
    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        unit_number = cleaned_data.get('unit_number')
        queue_status = cleaned_data.get('queue_status')
        technician = cleaned_data.get('technician')
        cost_override = cleaned_data.get('cost_override')
        override_reason = cleaned_data.get('override_reason')

        # Admin users must select a technician
        if hasattr(self, 'user') and self.user.is_staff and not technician:
            self.add_error('technician', 'Please select a technician to assign this repair to.')

        # Validate pricing override permissions and limits
        if cost_override is not None:
            if not (hasattr(self, 'user') and hasattr(self.user, 'technician')):
                self.add_error('cost_override', 'Only managers can override pricing.')
            else:
                user_technician = self.user.technician
                if not (user_technician.is_manager and user_technician.can_override_pricing):
                    self.add_error('cost_override', 'You do not have permission to override pricing.')
                elif user_technician.approval_limit and cost_override > user_technician.approval_limit:
                    self.add_error('cost_override', f'Override amount exceeds your approval limit of ${user_technician.approval_limit}.')
                elif not override_reason:
                    self.add_error('override_reason', 'Override reason is required when setting a custom price.')

        # If override reason is provided, cost_override should also be provided
        if override_reason and cost_override is None:
            self.add_error('cost_override', 'Please provide an override amount when specifying a reason.')

        if customer and unit_number:
            existing_repairs = Repair.objects.filter(
                customer=customer,
                unit_number=unit_number,
                queue_status__in=['PENDING', 'APPROVED', 'IN_PROGRESS']
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing_repairs.exists():
                existing_repair = existing_repairs.first()
                if queue_status in ['PENDING', 'APPROVED', 'IN_PROGRESS']:
                    raise forms.ValidationError(
                        f"There is already a {existing_repair.get_queue_status_display()} repair for this unit. "
                        f"<a href='/tech/repairs/{existing_repair.id}/'>View existing repair</a>",
                        code='existing_repair'
                    )

        return cleaned_data
