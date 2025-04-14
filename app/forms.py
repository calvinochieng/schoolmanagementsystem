# Inside your app's forms.py (e.g., core/forms.py)

from django import forms
from django.utils import timezone
# Import your models (adjust path if needed)
from .models import DisciplineReport, Student, ParentProfile, User # Import native User

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
class ParentRegistrationForm(forms.Form):
    """
    Form for Admin/Staff to input data for creating a new Parent User
    and their associated ParentProfile.
    """
    full_name = forms.CharField(
        max_length=150, # Match User model's first/last name constraints roughly
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Parent\'s Full Name'})
        )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'parent@example.com'})
        )
    # Optional: Allow specifying a username, otherwise view can default to email
    # username = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '+2547XXXXXXXX'})
        )
    parent_role = forms.ChoiceField(
        choices=ParentProfile.PARENT_ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'select'}) # Add Bulma class
        )
    # Gender field if needed (assuming it's on ParentProfile, as native User doesn't have it)
    # gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], required=False) # Example choices
    student = forms.ModelChoiceField(
        queryset=Student.objects.all().order_by('name'),
        required=True,
        widget=forms.Select(attrs={'class': 'select is-fullwidth'}), # Add Bulma class
        label="Link to Student"
        )

    # Custom validation methods
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    # Optional: Add username validation if you include that field
    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if username and User.objects.filter(username__iexact=username).exists():
    #         raise forms.ValidationError("This username is already taken.")
    #     return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Add specific phone validation if needed (e.g., format)
        if ParentProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already associated with another parent profile.")
        return phone

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if ' ' not in full_name.strip(): # Basic check for at least two names
             raise forms.ValidationError("Please enter both first and last names.")
        return full_name

    # NOTE: No save() method here. The view will handle:
    # 1. Validating this form.
    # 2. Generating a temporary password.
    # 3. Creating the User instance (is_staff=False, is_superuser=False).
    # 4. Creating the ParentProfile instance.
    # 5. Returning the generated password to the Admin/Staff.

# --- Other Potential Forms (To be created later) ---
# class StudentForm(forms.ModelForm): ...
# class UserProfileForm(forms.ModelForm): ... # For users editing their own info
# class CustomAuthenticationForm(AuthenticationForm): ... # If styling/customization needed
# class CustomPasswordChangeForm(PasswordChangeForm): ... # If needed