# app/urls.py

from django.urls import path
# Import the views from the current app's views.py
from . import views

urlpatterns = [
    # --- Main/Dashboard URLs ---
    path('', views.index, name='index'), # Root URL of the app
    path('dashboard/', views.dashboard, name='dashboard'), # Official (Admin/Staff) dashboard

    # --- Student URLs ---
    path('students/create/', views.create_student, name='create_student'),
    path('students/', views.student_list, name='student_list'),
    # Placeholder for student detail 
    path('students/<int:student_id>/', views.student_detail_view, name='student_detail'),

    # --- Discipline Report URLs ---
    path('reports/', views.discipline_report_list, name='discipline_report_list'),
    path('reports/new/', views.create_discipline_report, name='create_discipline_report'),
    # Placeholder for report detail
    path('reports/<int:pk>/', views.discipline_report_detail_view, name='discipline_report_detail'),
    # Placeholder for editing a report
    path('reports/<int:pk>/edit/', views.discipline_report_edit, name='discipline_report_edit'),
    path('reports/<int:pk>/edit/status/', views.discipline_report_update_status, name='discipline_report_update_status'),
    # Placeholder for deleting a report (soft delete) 
    path('reports/<int:pk>/delete/', views.discipline_report_delete, name='discipline_report_delete'),

    # --- User/Profile URLs (Examples - more needed) ---
    # Placeholder for viewing own profile - needs a view function `profile_view`
    # path('profile/', views.profile_view, name='profile_view'),
    # Placeholder for editing own profile - needs a view function `profile_edit_view`
    # path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # --- Parent Registration URL  ---
  
    path('parents/create/', views.create_parent_profile, name='create_parent_profile'),
    path('parents/credentials/', views.display_parent_credentials, name='display_parent_credentials'),
    path('parents/', views.parents_list, name='parents_list'),
    path('parent-portal/', views.parent_portal_detail, name='parent_portal_detail'),    
    # parent_detail view is a placeholder for the parent detail view
    path('parents/<str:username>/', views.parent_detail_view, name='parent_detail'),
    # Placeholder for editing a parent profile - needs a view function `edit_parent_profile`
    path('parents/<int:pk>/edit/', views.edit_parent_profile, name='edit_parent_profile'),


    # Note: Login, Logout, Password Change/Reset are typically handled at the project level
    # using django.contrib.auth.urls
]