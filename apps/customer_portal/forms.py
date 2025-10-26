"""
Customer Portal Forms

Django Forms: These classes automatically generate HTML forms from your models
and handle validation. This is one of Django's most powerful features!
"""

from django import forms
from .models import CustomerRepairPreference


class RepairPreferenceForm(forms.ModelForm):
    """
    Form for CustomerRepairPreference model.

    ModelForm automatically creates form fields from your model fields.
    You just specify which model and which fields to include!
    """

    # Days of week for lot walking (multi-select checkboxes)
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    # Override the lot_walking_days field to make it checkbox-friendly
    lot_walking_days_choices = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Preferred Days for Lot Walking",
        help_text="Select all days that work for your schedule"
    )

    class Meta:
        model = CustomerRepairPreference
        fields = [
            'field_repair_approval_mode',
            'units_per_visit_threshold',
            'lot_walking_enabled',
            'lot_walking_frequency',
            'lot_walking_time',
        ]

        # Customize how fields appear in the form
        widgets = {
            'field_repair_approval_mode': forms.RadioSelect(),  # Radio buttons instead of dropdown
            'units_per_visit_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '50'
            }),
            'lot_walking_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }

        # Custom labels (what users see)
        labels = {
            'field_repair_approval_mode': 'Field Repair Approval Mode',
            'units_per_visit_threshold': 'Units Per Visit Threshold',
            'lot_walking_enabled': 'Enable Lot Walking Service',
            'lot_walking_frequency': 'Lot Walking Frequency',
            'lot_walking_time': 'Preferred Time',
        }

    def __init__(self, *args, **kwargs):
        """
        Custom initialization to pre-populate the days checkboxes
        from the JSONField data
        """
        super().__init__(*args, **kwargs)

        # If editing existing preference, populate the days checkboxes
        if self.instance and self.instance.pk and self.instance.lot_walking_days:
            self.fields['lot_walking_days_choices'].initial = self.instance.lot_walking_days

    def save(self, commit=True):
        """
        Custom save method to handle the days checkboxes
        and save them to the JSONField
        """
        instance = super().save(commit=False)

        # Convert checkbox selections to list and store in JSONField
        instance.lot_walking_days = self.cleaned_data.get('lot_walking_days_choices', [])

        if commit:
            instance.save()

        return instance
