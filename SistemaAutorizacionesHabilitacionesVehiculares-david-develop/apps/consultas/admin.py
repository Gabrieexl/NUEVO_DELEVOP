"""
Admin para consultas.
"""

from django.contrib import admin
from .models import APIKey, RegistroConsulta


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'entidad', 'activa', 
        'consultas_hoy', 'total_consultas',
        'fecha_expiracion', 'ultimo_uso'
    )
    list_filter = ('activa', 'fecha_expiracion')
    search_fields = ('nombre', 'entidad', 'email_contacto')
    readonly_fields = ('clave', 'fecha_creacion', 'ultimo_uso', 'total_consultas', 'consultas_hoy')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información', {
            'fields': ('nombre', 'entidad', 'email_contacto')
        }),
        ('Clave', {
            'fields': ('clave',),
            'description': 'La clave se genera automáticamente al guardar'
        }),
        ('Estado', {
            'fields': ('activa', 'fecha_expiracion')
        }),
        ('Límites', {
            'fields': ('limite_diario',)
        }),
        ('Estadísticas', {
            'fields': ('consultas_hoy', 'total_consultas', 'ultimo_uso'),
            'classes': ('collapse',)
        }),
    )
    
    def has_change_permission(self, request, obj=None):
        # Permitir editar pero no cambiar la clave
        return True


@admin.register(RegistroConsulta)
class RegistroConsultaAdmin(admin.ModelAdmin):
    list_display = (
        'placa_consultada', 'api_key', 'ip_origen',
        'resultado_exitoso', 'tiempo_respuesta_ms', 'fecha_consulta'
    )
    list_filter = ('resultado_exitoso', 'fecha_consulta')
    search_fields = ('placa_consultada', 'ip_origen', 'api_key__nombre')
    ordering = ('-fecha_consulta',)
    readonly_fields = (
        'api_key', 'placa_consultada', 'ip_origen', 'user_agent',
        'fecha_consulta', 'resultado_exitoso', 'mensaje_error', 'tiempo_respuesta_ms'
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
