from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_staff', 'is_superuser']
    # Reorganizing fieldsets to ensure email is included
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional Info', {'fields': ('user_type',)}),
    )
    # Ensures email is displayed in the form during user creation
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )

admin.site.register(CustomUser,CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(DoctorAvailability)
admin.site.register(Appointment)
admin.site.register(Bill)
admin.site.register(MedicalRecord)

