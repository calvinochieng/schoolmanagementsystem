from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, HttpResponse


from .models import *

from .forms import DisciplineReportForm


# --- Index View ---
def index(request):
    """
    Simple public index page or redirect authenticated users.
    """
    if request.user.is_authenticated:
         # Check if user is staff/admin first
         if request.user.is_staff: # Covers both staff and superusers
             return redirect('dashboard')
         else:
             # Assume non-staff users might be parents
             # Add check for parent profile existence for robustness?
             return redirect('parent_dashboard')
    # If not authenticated, show index page
    return render(request, 'index.html', {})


# --- Official Dashboard View (Admin/Staff) ---
@login_required
def dashboard(request):
    """
    Displays the main dashboard for Admin (superuser) and Staff (is_staff=True) users.
    """
    user = request.user

    # Ensure only staff/admin can access this view
    if not user.is_staff:
        # Redirect non-staff users (likely parents) away
        # Could redirect to parent_dashboard or login
        if not user.is_authenticated:
             return redirect(reverse_lazy('login'))
        # If authenticated but not staff, maybe parent dashboard?
        # Or just deny access if they somehow reach here without being staff.
        # Let's redirect known non-staff to parent dashboard, otherwise deny.
        try:
            # Check if they look like a parent
            if hasattr(user, 'parent_profile'):
                 return redirect('parent_dashboard')
            else: # Authenticated, not staff, no parent profile? Deny.
                 return HttpResponseForbidden("Access Denied.")
        except ParentProfile.DoesNotExist: # Should not happen with OneToOneField check above
             return HttpResponseForbidden("Access Denied.")


    # --- Fetch data using native User model flags ---
    student_count = Student.objects.count()
    # Count parent users (active users who are NOT staff/superuser)
    parent_user_count = User.objects.filter(
        is_staff=False, is_superuser=False, is_active=True
    ).count()
    pending_reports_count = DisciplineReport.objects.filter(status='pending', is_deleted=False).count()

    recent_reports = DisciplineReport.objects.filter(is_deleted=False).select_related('student', 'added_by').order_by('-created_at')[:10]


    context = {
        'student_count': student_count,
        'parent_count': parent_user_count,
        'pending_reports': pending_reports_count,
        'recent_reports': recent_reports,
    }

    # Admin-specific counts (superuser flag)
    if user.is_superuser:
        context['admin_count'] = User.objects.filter(is_superuser=True, is_active=True).count()
        # Count staff who are NOT superusers
        context['staff_count'] = User.objects.filter(is_staff=True, is_superuser=False, is_active=True).count()
        # parent_count is already included

    # Render the official dashboard template
    return render(request, 'dashboards/official_portal.html', context)


# --- Parent Dashboard View ---
@login_required
def parent_dashboard(request):
    """
    Displays the dashboard specifically for logged-in Parent users.
    """
    user = request.user

    # Ensure user is NOT staff/admin
    if user.is_staff:
        # Redirect staff/admins to their dashboard
        return redirect('dashboard')

    try:
        # Get the profile linked to this parent user via OneToOneField
        # related_name is 'parent_profile'
        parent_profile = get_object_or_404(ParentProfile, user=user)
        student = parent_profile.student
    except ParentProfile.DoesNotExist:
         messages.error(request, "Your parent profile could not be found. Please contact administration.")
         # Log this critical error server-side
         return redirect(reverse_lazy('login'))

    # Fetch data specific to this parent's student
    student_reports = DisciplineReport.objects.filter(
        student=student, is_deleted=False
    ).order_by('-date', '-created_at')

    context = {
        'student': student,
        'profile': parent_profile,
        'reports': student_reports,
    }
    # Render the parent-specific portal template
    return render(request, 'dashboards/parent_portal.html', context)


# --- Discipline Report List View (for Admin/Staff) ---
@login_required
def discipline_report_list(request):
    """
    Lists all discipline reports with pagination and basic filtering.
    Accessible only by Staff/Admin users.
    """
    user = request.user
    if not user.is_staff: # Only staff/admins can access
        return HttpResponseForbidden("Access Denied.")

    status_filter = request.GET.get('status', None)
    student_filter = request.GET.get('student_id', None)

    report_list = DisciplineReport.objects.filter(is_deleted=False).select_related(
        'student', 'added_by'
    ).order_by('-created_at')

    if status_filter:
        report_list = report_list.filter(status=status_filter)
    if student_filter:
        # Add validation for student_id if needed
        report_list = report_list.filter(student_id=student_filter)

    paginator = Paginator(report_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_choices': DisciplineReport.STATUS_CHOICES,
        'severity_choices': DisciplineReport.SEVERITY_CHOICES,
        'current_status': status_filter,
        'current_student_id': student_filter,
    }
    return render(request, 'discipline/discipline_report_list.html', context)


# --- Create Discipline Report View (for Admin/Staff) ---
@login_required
def create_discipline_report(request):
    """
    Handles the creation of a new discipline report via a form.
    Accessible only by Staff/Admin users.
    """
    user = request.user
    if not user.is_staff: # Only staff/admins can create reports
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = DisciplineReportForm(request.POST)
        if form.is_valid():
            try:
                report = form.save(commit=False)
                report.added_by = user
                report.save()

                messages.success(request, f"Discipline report '{report.title}' for {report.student.name} created successfully.")
                # Redirect to list view (or detail view if you create one)
                return redirect('discipline_report_list')
            except Exception as e:
                 messages.error(request, f"Failed to save report or create Report: {e}")
                 # Log the error e server-side
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        form = DisciplineReportForm() # Initialize empty form

    # Limit student choices in the form if needed, or handle in the form definition
    context = {
        'form': form
    }
    return render(request, 'discipline/discipline_report_form.html', context)


@login_required
def student_list(request):
    """
    Lists all students with pagination and search functionality.
    Accessible by Staff/Admin users.
    """
    user = request.user
    if not user.is_staff:  # Only staff/admins can view student list
        return HttpResponseForbidden("Access Denied.")

    # Get search query from request
    search_query = request.GET.get('search', '')
    
    # Base queryset
    student_list_qs = Student.objects.all()
    
    # Apply search filter if provided
    if search_query:
        # Search in name or enrollment_number fields
        student_list_qs = student_list_qs.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(enrollment_number__icontains=search_query)
        )
    
    # Apply sorting
    student_list_qs = student_list_qs.order_by('grade', 'name')
    
    # Pagination
    paginator = Paginator(student_list_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': student_list_qs.count(),
    }
    return render(request, 'student/student_list.html', context)

@login_required
def student_detail_view(request, student_id):
    """
    Displays detailed information about a specific student.
    Includes personal info, parent information, and discipline reports.
    """
    # Get the student or return 404
    student = get_object_or_404(Student, pk=student_id)
    
    user = request.user
    
    # Check if user has permission to view this student
    # Staff can view any student
    # Parents can only view their own children
    if not user.is_staff:
        # Check if the user is a parent of this student
        try:
            parent_profile = ParentProfile.objects.get(user=user, student=student)
        except ParentProfile.DoesNotExist:
            return HttpResponseForbidden("Access Denied. You don't have permission to view this student.")
    
    # Get related data
    parents = student.parent_profiles.all().select_related('user', 'added_by')
    
    # Get discipline reports, newest first
    discipline_reports = (student.discipline_reports
                         .filter(is_deleted=False)
                         .select_related('added_by')
                         .order_by('-date'))
    
    context = {
        'student': student,
        'parents': parents,
        'discipline_reports': discipline_reports,
        # Adding additional data for breadcrumbs and navigation
        'page_title': f"{student.name} - Student Profile",
    }
    
    return render(request, 'student/student_detail.html', context)

@login_required
def discipline_report_detail_view(request, pk):
    # TODO: Implement actual report detail logic
    report = get_object_or_404(DisciplineReport, pk=pk)
    # Check permissions if needed (e.g., only staff or parent of student involved)
    return HttpResponse(f"<h1>Placeholder for Report Detail: {report.title} (ID: {pk})</h1>")


# Add more placeholders as needed for edit/delete/profile/etc.
# def update_discipline_report(request, pk): ...
# def delete_discipline_report(request, pk): ...
# def profile_view(request): ...
# def profile_edit_view(request): ...
# def register_parent_view(request): ...
# --- TODO / Next Steps ---
# - Define DisciplineReportForm in forms.py (ensure fields like 'student' are handled correctly)
# - Create Detail Views (Student, Discipline Report, Parent Profile)
# - Create Update/Edit Views (Report Status/Severity, Profile info?)
# - Create Delete Views (using soft delete 'is_deleted=True' for reports)
# - Implement Parent Registration View (using native User, setting is_staff=False, is_superuser=False)
# - Implement "force password change on first login" for parents