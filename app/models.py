import random
from django.db import models
from django.contrib.auth.models import User # Import the default User model
from django.conf import settings # Still use settings.AUTH_USER_MODEL which now points to default User
from django.utils import timezone
from django.core.exceptions import ValidationError # For potential validation

class Student(models.Model):
    # Choices for Grades based on CBC (Junior, Senior School)
    GRADE_CHOICES = [
        ('G7', 'Grade 7 (Form 1)'),
        ('G8', 'Grade 8 (Form 2)'),
        ('G9', 'Grade 9 (Form 3)'),
        # Senior School
        ('G10', 'Grade 10 (Form 4)'),
        ('G11', 'Grade 11'),
        ('G12', 'Grade 12'),
    ]

    # Choices for Gender
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'), # Optional: Consider adding 'Other' or 'Prefer not to say'
    ]
    name = models.CharField(max_length=255)
    grade = models.CharField(
        max_length=20,
        choices=GRADE_CHOICES,
        help_text="Select the student's current grade level (CBC System)."
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )
    enrollment_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now) # Added default for convenience
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Allow blank for cases where enrollment isn't tied to a specific staff user initially
        related_name='enrolled_students',
        limit_choices_to={'is_staff': True},
         help_text="Staff member who enrolled the student."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Use get_grade_display() to show the human-readable choice name
        return f"{self.name} ({self.get_grade_display()})"

    def save(self, *args, **kwargs):
        # Generate enrollment number if it doesn't exist
        if not self.enrollment_number:
            year = timezone.now().year
            while True:
                random_number = str(random.randint(1, 99999)).zfill(5)
                potential_enrollment_number = f"{year}-{random_number}"
                if not Student.objects.filter(enrollment_number=potential_enrollment_number).exists():
                    self.enrollment_number = potential_enrollment_number
                    break
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name', 'grade']

class ParentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        primary_key=True, # Often good practice for profile models
    )
    PARENT_ROLE_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
    ]
    parent_role = models.CharField(max_length=10, choices=PARENT_ROLE_CHOICES)
    phone = models.CharField(max_length=15, unique=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='parent_profiles'
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_parent_profiles',
        # Limit choices to users who are staff
        limit_choices_to={'is_staff': True}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add validation to ensure linked user is not staff/superuser
    def clean(self):
        if self.user_id and (self.user.is_staff or self.user.is_superuser):
             raise ValidationError("Parent profiles cannot be linked to staff or admin accounts.")
        super().clean()

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_parent_role_display()} of {self.student.name})"


# DisciplineReport model to track student behavior and incidents
class DisciplineReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'),
    ]
    SEVERITY_CHOICES = [
        ('minor', 'Minor'), ('moderate', 'Moderate'), ('serious', 'Serious'), ('critical', 'Critical'),
    ]

    date = models.DateField(default=timezone.now)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logged_reports',
        # Limit choices to users who are staff
        limit_choices_to={'is_staff': True}
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='discipline_reports'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Report for {self.student.name} on {self.date} ({self.title})"


