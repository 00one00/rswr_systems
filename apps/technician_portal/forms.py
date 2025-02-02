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
    repair_date = forms.DateTimeField(
        widget=CustomDateTimeInput(),
        initial=timezone.now
    )

    class Meta:
        model = Repair
        fields = ['customer', 'unit_number', 'repair_date', 'description', 'queue_status', 'damage_type', 'drilled_before_repair', 'windshield_temperature', 'resin_viscosity']

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        unit_number = cleaned_data.get('unit_number')
        queue_status = cleaned_data.get('queue_status')

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
                        f"<a href='/technician/repairs/{existing_repair.id}/'>View existing repair</a>",
                        code='existing_repair'
                    )

        return cleaned_data
