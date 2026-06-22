"""
Admin para trámites.
"""

from django.contrib import admin
from django_fsm_log.admin import StateLogInline

from .models import Tramite, HistorialTramite


class HistorialTramiteInline(admin.TabularInline):
    model = HistorialTramite
    extra = 0
    readonly_fields = ('fecha', 'estado_anterior', 'estado_nuevo', 'usuario', 'accion', 'comentario')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Tramite)
class TramiteAdmin(admin.ModelAdmin):
    list_display = (
        'numero_expediente', 'tipo_tramite', 'empresa',
        'estado', 'fecha_creacion', 'usuario_actual'
    )
    list_filter = ('estado', 'tipo_tramite')
    search_fields = (
        'numero_expediente', 'empresa__razon_social', 
        'empresa__ruc', 'descripcion_solicitud'
    )
    ordering = ('-fecha_creacion',)
    readonly_fields = (
        'numero_expediente', 'fecha_creacion', 'fecha_actualizacion', 
        'creado_por', 'estado'
    )
    autocomplete_fields = ['empresa', 'autorizacion', 'usuario_actual']
    date_hierarchy = 'fecha_creacion'
    inlines = [HistorialTramiteInline]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('numero_expediente', 'tipo_tramite', 'estado', 'empresa', 'autorizacion')
        }),
        ('Solicitud', {
            'fields': ('descripcion_solicitud', 'fecha_presentacion')
        }),
        ('Evaluación', {
            'fields': ('observaciones_tecnicas', 'observaciones_legales', 'plazo_subsanacion')
        }),
        ('Resolución', {
            'fields': ('numero_resolucion', 'fecha_resolucion')
        }),
        ('Asignación', {
            'fields': ('usuario_actual',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistorialTramite)
class HistorialTramiteAdmin(admin.ModelAdmin):
    list_display = ('tramite', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha', 'accion')
    list_filter = ('estado_nuevo',)
    search_fields = ('tramite__numero_expediente',)
    ordering = ('-fecha',)
    readonly_fields = ('tramite', 'fecha', 'estado_anterior', 'estado_nuevo', 
                       'usuario', 'accion', 'comentario')
