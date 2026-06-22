"""
Admin para el módulo de notificaciones.
"""

from django.contrib import admin
from .models import Notificacion, ConfiguracionNotificacion, HistorialEmailEnviado


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'tipo', 'prioridad', 'leida', 'fecha_creacion']
    list_filter = ['tipo', 'prioridad', 'leida', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje', 'usuario__username', 'usuario__email']
    readonly_fields = ['fecha_creacion', 'fecha_lectura']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Destinatario', {
            'fields': ('usuario',)
        }),
        ('Contenido', {
            'fields': ('tipo', 'titulo', 'mensaje', 'prioridad', 'url')
        }),
        ('Referencias', {
            'fields': ('tramite_id', 'empresa_id', 'vehiculo_id', 'conductor_id'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_lectura', 'fecha_creacion')
        }),
    )
    
    actions = ['marcar_como_leidas', 'marcar_como_no_leidas']
    
    @admin.action(description='Marcar seleccionadas como leídas')
    def marcar_como_leidas(self, request, queryset):
        from django.utils import timezone
        queryset.update(leida=True, fecha_lectura=timezone.now())
    
    @admin.action(description='Marcar seleccionadas como no leídas')
    def marcar_como_no_leidas(self, request, queryset):
        queryset.update(leida=False, fecha_lectura=None)


@admin.register(ConfiguracionNotificacion)
class ConfiguracionNotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'email_tramite_cambio_estado', 'email_vencimientos', 'dias_alerta_vencimiento']
    list_filter = ['email_tramite_cambio_estado', 'email_vencimientos']
    search_fields = ['usuario__username', 'usuario__email']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Notificaciones por Email', {
            'fields': (
                'email_tramite_cambio_estado',
                'email_tramite_observado',
                'email_tramite_aprobado',
                'email_vencimientos',
                'email_plazo_subsanacion',
            )
        }),
        ('Notificaciones In-App', {
            'fields': (
                'app_tramite_cambio_estado',
                'app_vencimientos',
            )
        }),
        ('Configuración de Alertas', {
            'fields': ('dias_alerta_vencimiento',)
        }),
    )


@admin.register(HistorialEmailEnviado)
class HistorialEmailEnviadoAdmin(admin.ModelAdmin):
    list_display = ['asunto', 'email_destino', 'tipo', 'enviado', 'fecha_creacion', 'intentos']
    list_filter = ['tipo', 'enviado', 'fecha_creacion']
    search_fields = ['asunto', 'email_destino', 'nombre_destino']
    readonly_fields = ['fecha_creacion', 'fecha_envio', 'post_office_email_id']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Destinatario', {
            'fields': ('email_destino', 'nombre_destino', 'usuario')
        }),
        ('Contenido', {
            'fields': ('tipo', 'asunto')
        }),
        ('Referencias', {
            'fields': ('tramite_id', 'empresa_id'),
            'classes': ('collapse',)
        }),
        ('Estado de Envío', {
            'fields': ('enviado', 'fecha_envio', 'error', 'intentos', 'post_office_email_id')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion',)
        }),
    )
