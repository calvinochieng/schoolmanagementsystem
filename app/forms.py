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

class ParentProfileForm(forms.ModelForm):    
    class Meta:
        model = ParentProfile  # Specify the model the form is based on
        # List the fields from the model to include in the form
        fields = ['student', 'full_name', 'parent_role', 'phone', 'email']
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),   # we’ll override this in __init__
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
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control input'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # base queryset: only students with no parent profiles
        qs = Student.objects.filter(parent_profiles__isnull=True)

        # if we’re editing, include that student even though they have a profile
        if self.instance and self.instance.pk:
            qs = qs | Student.objects.filter(pk=self.instance.student_id)

        self.fields['student'].queryset = qs.distinct()
    
class StudentForm(forms.ModelForm):
    """
    Form for creating or updating a Student profile.
    """
    class Meta:
        model = Student
        #all fields from the Student model
        fields = [
            'name',
            'grade',
            'gender',
            'enrollment_date',
            'enrolled_by',]
        widgets = {
            'name': forms.TextInput(attrs={                
                'placeholder': 'Full Name',
                'class': 'input'
            }),
            'grade': forms.Select(attrs={''
                'class': 'select', 
                'class': 'input'
                }),
            'enrollment_date':forms.DateInput(attrs={
                'type': 'date', 
                'class': 'input'
                }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'input'
                }),
        }