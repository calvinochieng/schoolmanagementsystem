# Inside your app's forms.py (e.g., core/forms.py)

from django import forms
from django.utils import timezone
# Import your models (adjust path if needed)
from .models import DisciplineReport, Student, ParentProfile

class StatusUpdateForm(forms.ModelForm):
    """Form for updating the status of a discipline report."""
    
    class Meta:
        model = DisciplineReport
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'select is-fullwidth'})
        }


# 1. Discipline Report Form
class DisciplineReportForm(forms.ModelForm):
    """
    Form for Admin/Staff to create or update a Discipline Report.
    """
    # Use DateInput with type='date' for better browser support for date pickers
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date() # Default to today's date
    )
    # Ensure student selection is clear
    student = forms.ModelChoiceField(
        queryset=Student.objects.all().order_by('name'), # Or filter for active students
        widget=forms.Select(attrs={'class': 'select is-fullwidth'}), # Add Bulma class
        label="Select Student"
    )

    class Meta:
        model = DisciplineReport
        # Fields to include in the form
        fields = [
            'student',
            'date',
            'title',
            'description',
            'comment', # Note for parent
            'severity',
            'status',
        ]
        # Customize widgets for better UI/UX
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Late for Class, Uniform Violation'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detailed description of the incident...'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': '(Optional) Specific comment or action required from the parent...'}),
            'severity': forms.Select(attrs={'class': 'select'}), # Add Bulma class
            'status': forms.Select(attrs={'class': 'select'}),   # Add Bulma class
        }
        # Customize labels if needed
        labels = {
            'comment': 'Note to Parent (Optional)',
            'date': 'Date of Incident',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bulma classes or other customizations dynamically if needed
        # Example: Add 'input' class to relevant fields
        for field_name in ['title', 'date']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'input'})
        # Example: Add 'textarea' class
        for field_name in ['description', 'comment']:
             if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'textarea'})


# 2. Parent Registration Form (Fields Definition)
# NOTE: This is a standard forms.Form because it doesn't map directly to one model.
# The logic to create User and ParentProfile objects, generate passwords, etc.,
# will reside primarily in the VIEW function that processes this form.

class ParentProfileForm(forms.ModelForm):    
    class Meta:
        model = ParentProfile  # Specify the model the form is based on
        # List the fields from the model to include in the form
        fields = ['student', 'full_name', 'parent_role', 'phone', 'email']
    student = forms.ModelChoiceField(        
        queryset=Student.objects.filter(parent_profiles__isnull=True),
        label="Select Student",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    full_name = forms.CharField(
        max_length=255,
        label="Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control input'})
    )
    
    parent_role = forms.ChoiceField(
        choices=ParentProfile.PARENT_ROLE_CHOICES,
        label="Parent Role",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    phone = forms.CharField(
        max_length=15,
        label="Phone Number",
        widget=forms.TextInput(attrs={'class': 'form-control input'})
    )
    
    email = forms.EmailField(
        required=False,
        label="Email Address (Optional)",
        widget=forms.EmailInput(attrs={'class': 'form-control input'})
    )
    
    
# class ParentProfileForm(forms.ModelForm):
#     email = forms.EmailField(
#         required=False, # Corresponds to blank=True on the model field
#         label="Email Address (Optional)",
#         widget=forms.EmailInput(attrs={'class': 'form-control input'})
#     )

#     class Meta:
#         model = ParentProfile  # Specify the model the form is based on
#         # List the fields from the model to include in the form
#         fields = ['student', 'full_name', 'parent_role', 'phone', 'email']

#         # Define labels for fields (optional, defaults to model field's verbose_name)
#         labels = {
#             'student': "Select Student",
#             'full_name': "Full Name",
#             'parent_role': "Parent Role",
#             'phone': "Phone Number",
#             # 'email' label is handled by the explicit field definition above
#         }

#         # Define widgets for fields (optional, defaults to Django's default widgets)
#         widgets = {
#             'student': forms.Select(attrs={'class': 'form-control'}),
#             'full_name': forms.TextInput(attrs={'class': 'form-control input'}),
#             'parent_role': forms.Select(attrs={'class': 'form-control'}), # Choices come from the model field
#             'phone': forms.TextInput(attrs={'class': 'form-control input'}),
#             # 'email' widget is handled by the explicit field definition above
#         }


# --- Other Potential Forms (To be created later) ---
# class StudentForm(forms.ModelForm): ...
# class UserProfileForm(forms.ModelForm): ... # For users editing their own info
# class CustomAuthenticationForm(AuthenticationForm): ... # If styling/customization needed
# class CustomPasswordChangeForm(PasswordChangeForm): ... # If needed