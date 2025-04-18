from django.contrib import admin
from django.utils.html import format_html
from .models import Student, ParentProfile, DisciplineReport
admin.site.site_header  = "SMS Discipline Department"
admin.site.site_title   = "Discipline Department"
admin.site.index_title  = "Welcome, Staff!"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'enrollment_number', 'grade', 'gender', 'enrollment_date', 'enrolled_by', 'created_at')
    list_filter = ('grade', 'gender', 'enrollment_date', 'enrolled_by')
    search_fields = ('name', 'enrollment_number')
    readonly_fields = ('enrollment_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Student Information', {
            'fields': ('name', 'grade', 'gender', 'enrollment_number')
        }),
        ('Enrollment Details', {
            'fields': ('enrollment_date', 'enrolled_by')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        # Optimize query by prefetching related enrolled_by users
        return super().get_queryset(request).select_related('enrolled_by')


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'parent_role', 'phone', 'student_name', 'added_by', 'created_at')
    list_filter = ('parent_role', 'added_by', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name','full_name', 'phone', 'student__name')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['user', 'student', 'added_by']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user','full_name', 'parent_role', 'phone', 'email')
        }),
        ('Student Link', {
            'fields': ('student', 'added_by')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
        
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student'
    
    def get_queryset(self, request):
        # Optimize query by prefetching related objects
        return super().get_queryset(request).select_related('user', 'student', 'added_by')


@admin.register(DisciplineReport)
class DisciplineReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'student_name', 'date', 'severity_colored', 'status', 'added_by', 'created_at')
    list_filter = ('status', 'severity', 'date', 'added_by', 'is_deleted')
    search_fields = ('title', 'student__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['student', 'added_by']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'student', 'date', 'severity', 'status')
        }),
        ('Details', {
            'fields': ('description', 'comment', 'added_by')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student'
    
    def severity_colored(self, obj):
        colors = {
            'minor': 'green',
            'moderate': 'orange',
            'serious': 'red',
            'critical': 'darkred'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.severity, 'black'),
            obj.get_severity_display()
        )
    severity_colored.short_description = 'Severity'
    
    def get_queryset(self, request):
        # By default, don't show deleted reports in the list
        queryset = super().get_queryset(request).select_related('student', 'added_by')
        if not request.GET.get('is_deleted__exact'):
            queryset = queryset.filter(is_deleted=False)
        return queryset
    
    def has_delete_permission(self, request, obj=None):
        # Instead of permanent deletion, we use soft delete
        return False
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    actions = ['mark_as_deleted', 'mark_as_resolved', 'mark_as_in_progress']
    
    def mark_as_deleted(self, request, queryset):
        queryset.update(is_deleted=True)
    mark_as_deleted.short_description = "Mark selected reports as deleted"
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_as_resolved.short_description = "Mark selected reports as resolved"
    
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    mark_as_in_progress.short_description = "Mark selected reports as in progress"