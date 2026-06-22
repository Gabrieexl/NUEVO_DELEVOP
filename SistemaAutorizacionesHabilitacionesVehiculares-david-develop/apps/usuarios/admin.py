"""
Configuración del admin para usuarios.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin personalizado para el modelo Usuario."""
    
    list_display = (
        'username', 'dni', 'email', 'get_full_name', 
        'rol', 'area', 'is_active', 'date_joined'
    )
    list_filter = ('rol', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'dni', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información DRTC', {
            'fields': ('dni', 'rol', 'telefono', 'area', 'cargo')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información DRTC', {
            'fields': ('dni', 'rol', 'telefono', 'area', 'cargo')
        }),
    )
