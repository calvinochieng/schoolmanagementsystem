import random
from django.db import models
from django.contrib.auth.models import User # Import the default User model
from django.conf import settings # Still use settings.AUTH_USER_MODEL which now points to default User
from django.utils import timezone
from django.core.exceptions import ValidationError # For potential validation
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

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
    full_name = models.CharField(max_length=255, null=True, blank=True)
    PARENT_ROLE_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
    ]
    parent_role = models.CharField(max_length=10, choices=PARENT_ROLE_CHOICES)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, null=True)
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

    # get parents name if not there return username
    def get_full_name(self):
        if self.full_name:
            return self.full_name
        return self.user.username

    # Add validation to ensure linked user is not staff/superuser
    def clean(self):
        if self.user_id and (self.user.is_staff or self.user.is_superuser):
             raise ValidationError("Parent profiles cannot be linked to staff or admin accounts.")
        super().clean()

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_parent_role_display()} of {self.student.name})"


def send_discipline_notification(discipline_report):
    """
    Send email notification to parents when a discipline report is created.
    """
    student = discipline_report.student
    
    # Get all parents associated with the student
    parents = student.parent_profiles.all()
    print(f"Found {parents.count()} parents for student {student.name}.")
    
    if not parents:
        print(f"No parents found for student {student.name}. Email notification not sent.")
        return
    
    # Create email subject
    subject = f"Discipline Report for {student.name}: {discipline_report.title}"
    print(f"Email subject: {subject}")
    
    # Get the absolute URL for the discipline report detail page
    try:
        report_url = reverse('discipline_report_detail_view', kwargs={'pk': discipline_report.pk})
        report_absolute_url = f"{settings.SITE_URL}{report_url}"
    except:
        report_absolute_url = f"https://schoolmanagementsystem-a0cm.onrender.com/reports/{discipline_report.pk}"
    
    # For each parent, send a personalized email
    for parent in parents:
        # Skip if parent has no email
        if not parent.email:
            continue
            
        # Prepare context for email template
        context = {
            'parent_name': parent.get_full_name(),
            'student_name': student.name,
            'report_title': discipline_report.title,
            'report_date': discipline_report.date,
            'report_severity': discipline_report.get_severity_display(),
            'report_description': discipline_report.description,
            'report_url': report_absolute_url,
        }
        
        # Render email templates
        html_message = render_to_string('emails/discipline_report_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[parent.email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"Discipline report notification sent to {parent.email}")
        except Exception as e:
            print(f"Failed to send email to {parent.email}: {str(e)}")


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
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new report
        super().save(*args, **kwargs)
        
        # Send email notification only when a new report is created
        if is_new:
            print(f"New discipline report created for {self.student.name}. Sending notification email.")
            send_discipline_notification(self)

    def __str__(self):
        return f"Report for {self.student.name} on {self.date} ({self.title})"