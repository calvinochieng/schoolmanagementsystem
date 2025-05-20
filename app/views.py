from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, HttpResponse

from django.utils.crypto import get_random_string

from .models import *
from .forms import *

def is_staff(user):
    return user.is_staff

# Django in built user login
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm

def login(request):
    """View for user login."""
    if request.user.is_authenticated:
        return redirect('index')  # Redirect authenticated users to index or dashboard
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')  # Redirect to index or dashboard
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

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
             return redirect('parent_portal_detail')
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
        # Could redirect to parent_portal_detail or login
        if not user.is_authenticated:
             return redirect(reverse_lazy('login'))
        # If authenticated but not staff, maybe parent dashboard?
        # Or just deny access if they somehow reach here without being staff.
        # Let's redirect known non-staff to parent dashboard, otherwise deny.
        try:
            # Check if they look like a parent
            if hasattr(user, 'parent_profile'):
                 return redirect('parent_portal_detail')
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



# --- Parent Creation, And Profile ---

@login_required
@user_passes_test(is_staff)
def create_parent_profile(request):
    """View for creating parent profile with Django user account."""
    
    if request.method == 'POST':
        form = ParentProfileForm(request.POST)
        
        if form.is_valid():
            # Get the student from the form
            student = form.cleaned_data['student']
            full_name = form.cleaned_data['full_name']
            parent_role = form.cleaned_data['parent_role']
            phone = form.cleaned_data['phone']
            
            # Create username in the format P-{enrollment_number}
            username = f"P-{student.enrollment_number}"
            
            # Check if username exists and append random characters if needed
            base_username = username
            # If user exists then redirect them to the larent page
            if User.objects.filter(username=username).exists():
                messages.warning = f"Parent of the student {student.name} already exists. Please choose a different student."
                redirect_url = reverse('parent_detail', args=[username])
            
            # Generate a random password
            password = get_random_string(length=8, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') 
            
            # Create the Django user
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data.get('email', ''),  # Email optional
                password=password
            )
            
            # Create parent profile linked to the user
            parent_profile = ParentProfile(
                user=user,
                full_name=full_name,
                parent_role=parent_role,
                phone=phone,
                student=student,
                added_by=request.user
            )
            parent_profile.save()
            
            # Store credentials in session to display once
            request.session['new_parent_credentials'] = {
                'username': username,
                'password': password,
                'parent_name': user.get_full_name() or username,
                'student_name': student.name
            }
            
            messages.success(request, "Parent profile created successfully.")
            return redirect('display_parent_credentials')
    else:
        form = ParentProfileForm()
    
    return render(request, 'parent/create_parent_profile.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def edit_parent_profile(request, pk):
    '''
    View for editing an existing parent profile. The current details are pre-filled in the form.
    '''
    parent_profile = get_object_or_404(ParentProfile, pk=pk)
    form = ParentProfileForm(instance=parent_profile)
    action = 'edit'
    if request.method == 'POST':
        form = ParentProfileForm(request.POST, instance = parent_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Parent profile updated successfully.")
            return redirect('parents_list')
    return render(request, 'parent/create_parent_profile.html', {'action': action,'form': form, 'parent_profile': parent_profile})

@login_required
@user_passes_test(is_staff)
def display_parent_credentials(request):
    """View to display the newly created parent credentials once."""
    
    credentials = request.session.get('new_parent_credentials', None)
    
    if credentials:
        # Remove from session after retrieving
        del request.session['new_parent_credentials']
        return render(request, 'parent/parent_credentials.html', {'credentials': credentials})
    else:
        messages.warning(request, "No new parent credentials to display.")
        return redirect('parents_list')  # Redirect to a suitable page

@login_required
@user_passes_test(is_staff)
def parents_list(request):
    """View to display all parent profiles."""
    parents = ParentProfile.objects.all().select_related('user', 'student')
    return render(request, 'parent/parents_list.html', {'parents': parents})

# Create parent detail view to show parent profile and their children/students it take the parents username as a parameter

@login_required
def parent_detail_view(request, username):
    """
    Displays detailed information about a specific parent profile.
    Includes personal info, children (students), and discipline reports.
    """
    # Get the parent profile or return 404
    parent_profile = get_object_or_404(ParentProfile.objects.select_related('user', 'student'), user__username=username)
    
    portal_url = (
        reverse('parent_portal_detail')
        + f'?parent_id={parent_profile.user_id}'
    )
    return redirect(portal_url)



# --- Parent Dashboard View ---
@login_required
def parent_portal_detail(request):
    """
    View for parent portal showing student details and discipline reports.
    Accessible by users with a parent profile and superusers who can filter between parents.
    """
    # For superusers: allow filtering by parent_id if provided
    if request.user.is_superuser:
        parent_id = request.GET.get('parent_id')
        
        # Get all parent profiles for dropdown filter
        all_parents = ParentProfile.objects.all().order_by('student__name')
        
        if parent_id:
            # If specific parent requested, get that parent's profile
            parent_profile = get_object_or_404(ParentProfile, user_id=parent_id)
        elif all_parents.exists():
            # Default to first parent if none specified
            parent_profile = all_parents.first()
        else:
            messages.warning(request, "No parent profiles exist in the system.")
            return redirect('dashboard')
            
        student = parent_profile.student
        
    else:
        # Regular parent user - check if they have a parent profile
        try:
            parent_profile = request.user.parent_profile
            student = parent_profile.student
            all_parents = None  # Regular parents don't need the list of all parents
        except ParentProfile.DoesNotExist:
            messages.error(request, "You don't have access to the parent portal.")
            return redirect('dashboard')
    
    # Get all discipline reports for this student, ordered by date (newest first)
    discipline_reports = DisciplineReport.objects.filter(
        student=student,
        is_deleted=False
    ).order_by('-date')
    
    context = {
        'parent_profile': parent_profile,
        'student': student,
        'discipline_reports': discipline_reports,
        'all_parents': all_parents,  # Will be None for regular parent users
        'is_superuser': request.user.is_superuser
    }
    
    return render(request, 'parent/parent_portal.html', context)


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
def discipline_report_detail_view(request, pk):
    """
    Detailed view of a specific discipline report.
    Shows report information, student details, and provides actions based on user permissions.
    
    Staff users can see all reports and update their status.
    Parent users can only see reports related to their children.
    """
    # Get the report or return 404
    report = get_object_or_404(DisciplineReport.objects.select_related(
        'student', 'added_by'
    ).prefetch_related(
        'student__parent_profiles',
        'student__parent_profiles__user'
    ), pk=pk, is_deleted=False)
    
    # Check permissions
    user = request.user
    has_access = False
    
    if user.is_staff:
        has_access = True
    elif hasattr(user, 'parent_profile'):
        # Check if this report is for the parent's student
        has_access = user.parent_profile.student == report.student
    
    if not has_access:
        raise PermissionDenied("You don't have permission to view this report.")
    
    # Handle status update form submission (staff only)
    if request.method == 'POST' and user.is_staff and 'status' in request.POST:
        previous_status = report.status
        form = StatusUpdateForm(request.POST, instance=report)
        
        if form.is_valid():
            # Save the updated report
            updated_report = form.save(commit=False)
            updated_report.updated_at = timezone.now()
            updated_report.save()
            
            # Add status change comment if provided
            status_comment = request.POST.get('status_comment', '').strip()
            if status_comment:
                # This assumes you have a StatusUpdate model or similar
                # If not, you could append to the report's comment field instead
                from .models import StatusUpdate  # Import here to avoid circular imports
                StatusUpdate.objects.create(
                    report=report,
                    previous_status=previous_status,
                    new_status=updated_report.status,
                    comment=status_comment,
                    updated_by=user
                )
            
            messages.success(request, f"Report status updated to {report.get_status_display()}")
            return redirect('discipline_report_detail', pk=pk)
        else:
            messages.error(request, "Error updating status. Please check the form.")
    else:
        form = StatusUpdateForm(instance=report)
    
    # Check if the user can edit/delete this report
    can_edit = user.is_staff
    can_delete = user.is_superuser or user == report.added_by
    
    context = {
        'report': report,
        'status_choices': DisciplineReport.STATUS_CHOICES,
        'severity_choices': DisciplineReport.SEVERITY_CHOICES,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'form': form,
        # Include any status updates history if you've implemented that
        'status_updates': report.status_updates.order_by('-created_at') if hasattr(report, 'status_updates') else None,
    }
    
    return render(request, 'discipline/discipline_report_detail.html', context)


@login_required
def discipline_report_update_status(request, pk):
    """
    Handle status updates independently from the main detail view.
    This allows for a cleaner separation of concerns and easier testing.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff members can update report status.")
    
    if request.method != 'POST':
        return redirect('discipline_report_detail', pk=pk)
    
    report = get_object_or_404(DisciplineReport, pk=pk, is_deleted=False)
    previous_status = report.status
    
    # Update the status
    new_status = request.POST.get('status')
    if new_status and new_status in dict(DisciplineReport.STATUS_CHOICES):
        report.status = new_status
        report.updated_at = timezone.now()
        report.save()
        
        # Handle status comment if provided
        status_comment = request.POST.get('status_comment', '').strip()
        if status_comment:
            # If you have a StatusUpdate model:
            try:
                from .models import StatusUpdate
                StatusUpdate.objects.create(
                    report=report,
                    previous_status=previous_status,
                    new_status=new_status,
                    comment=status_comment,
                    updated_by=request.user
                )
            except ImportError:
                # Otherwise append to report comment
                if report.comment:
                    report.comment += f"\n\n[Status Update by {request.user.get_full_name() or request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}]\n"
                else:
                    report.comment = f"[Status Update by {request.user.get_full_name() or request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}]\n"
                
                report.comment += f"Status changed from {dict(DisciplineReport.STATUS_CHOICES)[previous_status]} to {dict(DisciplineReport.STATUS_CHOICES)[new_status]}.\n"
                report.comment += f"Comment: {status_comment}"
                report.save()
        
        messages.success(request, f"Report status updated to {report.get_status_display()}")
    else:
        messages.error(request, "Invalid status value provided.")
    
    return redirect('discipline_report_detail', pk=pk)


@login_required
def discipline_report_delete(request, pk):
    """
    Soft delete a discipline report (mark as deleted).
    Only superusers or the report creator can delete.
    """
    report = get_object_or_404(DisciplineReport, pk=pk, is_deleted=False)
    
    # Check permissions
    if not (request.user.is_superuser or request.user == report.added_by):
        return HttpResponseForbidden("You don't have permission to delete this report.")
    
    if request.method == 'POST':
        # Soft delete
        report.is_deleted = True
        report.save()
        messages.success(request, "Discipline report has been deleted.")
        return redirect('discipline_report_list')
    
    # If not POST, redirect back to detail view
    return redirect('discipline_report_detail', pk=pk)


@login_required
def discipline_report_edit(request, pk):
    """
    Edit an existing discipline report.
    Only staff members can edit reports.
    """
    # This is a placeholder function - you would need to implement the full form handling
    # Including the form class and template
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff members can edit reports.")
    
    report = get_object_or_404(DisciplineReport, pk=pk, is_deleted=False)
    
    # Redirect to the actual edit view or render edit form
    # For now we'll just redirect back to the detail page
    messages.info(request, "Edit functionality to be implemented.")
    return redirect('discipline_report_detail', pk=pk)


# --- Students Views (for Admin/ Staff) ---
def create_student(request):
    """
    View for adding a new student.
    Accessible only by Staff/Admin users.
    """
    user = request.user
    if not user.is_staff:  # Only staff/admins can add students
        return HttpResponseForbidden("Access Denied.")

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.added_by = user
            student.save()
            messages.success(request, "Student added successfully.")
            return redirect('student_list')
    else:
        form = StudentForm()

    return render(request, 'student/add_student.html', {'form': form})

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


# ///////


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