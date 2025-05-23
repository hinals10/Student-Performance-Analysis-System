from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Course, Semester, Subject, Batch, StudentEnrollment, Assignment, AssignmentResponse, Test, TestQuestion, TestResponse

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'role', 'is_staff')
    list_filter = ('role',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)
admin.site.register(Course)
admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(Batch)
admin.site.register(StudentEnrollment)
admin.site.register(Assignment)
admin.site.register(AssignmentResponse)
admin.site.register(Test)
admin.site.register(TestQuestion)
admin.site.register(TestResponse)