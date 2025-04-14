# app/urls.py

from django.urls import path
# Import the views from the current app's views.py
from . import views

urlpatterns = [
    # --- Main/Dashboard URLs ---
    path('', views.index, name='index'), # Root URL of the app
    path('dashboard/', views.dashboard, name='dashboard'), # Official (Admin/Staff) dashboard
    path('portal/', views.parent_dashboard, name='parent_dashboard'), # Parent portal/dashboard

    # --- Student URLs ---
    path('students/', views.student_list, name='student_list'),
    # Placeholder for student detail - needs a view function `student_detail_view`
    path('students/<int:student_id>/', views.student_detail_view, name='student_detail'),

    # --- Discipline Report URLs ---
    path('reports/', views.discipline_report_list, name='discipline_report_list'),
    path('reports/new/', views.create_discipline_report, name='create_discipline_report'),
    # Placeholder for report detail - needs a view function `discipline_report_detail_view`
    path('reports/<int:pk>/', views.discipline_report_detail_view, name='discipline_report_detail'),
    # Placeholder for editing a report - needs a view function `update_discipline_report`
    path('reports/<int:pk>/edit/', views.discipline_report_edit, name='discipline_report_edit'),
    path('reports/<int:pk>/edit/status/', views.discipline_report_update_status, name='discipline_report_update_status'),
    # Placeholder for deleting a report (soft delete) - needs a view function `delete_discipline_report`
    path('reports/<int:pk>/delete/', views.discipline_report_delete, name='discipline_report_delete'),

    # --- User/Profile URLs (Examples - more needed) ---
    # Placeholder for viewing own profile - needs a view function `profile_view`
    # path('profile/', views.profile_view, name='profile_view'),
    # Placeholder for editing own profile - needs a view function `profile_edit_view`
    # path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # --- Parent Registration URL (Example) ---
    # Placeholder for the Admin/Staff view to register parents - needs a view function `register_parent_view`
    # path('parents/register/', views.register_parent_view, name='register_parent'),

    # Note: Login, Logout, Password Change/Reset are typically handled at the project level
    # using django.contrib.auth.urls
]