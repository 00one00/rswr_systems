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

class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ['phone_number', 'expertise']


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
        super().__init__(attrs={'step': '60', **(attrs or {})}, format=format)

class RepairForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all().order_by('name'))
    technician = forms.ModelChoiceField(
        queryset=Technician.objects.all(),
        required=False,  # Not required because it might be set automatically for non-admin users
        help_text="Only required for admin users. Regular technicians will be automatically assigned."
    )
    repair_date = forms.DateTimeField(
        widget=CustomDateTimeInput(),
        initial=timezone.now
    )
    damage_type = forms.ChoiceField(
        choices=[],  # Will be set in __init__
        required=False,
        help_text="Select the type of windshield damage"
    )

    class Meta:
        model = Repair
        fields = ['technician', 'customer', 'unit_number', 'repair_date', 'queue_status', 'damage_type', 'drilled_before_repair', 'windshield_temperature', 'resin_viscosity', 'damage_photo_before', 'damage_photo_after', 'customer_notes', 'technician_notes']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(RepairForm, self).__init__(*args, **kwargs)
        
        # Set the damage type choices
        self.fields['damage_type'].choices = Repair.DAMAGE_TYPE_CHOICES
        
        # Hide technician field for non-admin users
        if self.user and not self.user.is_staff:
            self.fields['technician'].widget = forms.HiddenInput()
        
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

        # Admin users must select a technician
        if hasattr(self, 'user') and self.user.is_staff and not technician:
            self.add_error('technician', 'Please select a technician to assign this repair to.')

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
