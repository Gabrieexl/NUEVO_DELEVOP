"""
Admin para autorizaciones.
"""

from django.contrib import admin
from .models import Autorizacion, HistorialAutorizacion


@admin.register(Autorizacion)
class AutorizacionAdmin(admin.ModelAdmin):
    list_display = (
        'numero_resolucion', 'empresa', 'tipo_servicio',
        'fecha_inicio_vigencia', 'fecha_fin_vigencia', 'estado'
    )
    list_filter = ('estado', 'tipo_servicio', 'ambito')
    search_fields = ('numero_resolucion', 'empresa__razon_social', 'empresa__ruc')
    ordering = ('-fecha_resolucion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'creado_por')
    autocomplete_fields = ['empresa']
    date_hierarchy = 'fecha_resolucion'
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('empresa', 'numero_resolucion', 'fecha_resolucion', 'estado')
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio_vigencia', 'fecha_fin_vigencia')
        }),
        ('Servicio', {
            'fields': ('ambito', 'tipo_servicio', 'modalidad')
        }),
        ('Rutas y Frecuencias', {
            'fields': ('descripcion_rutas', 'frecuencias')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
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


@admin.register(HistorialAutorizacion)
class HistorialAutorizacionAdmin(admin.ModelAdmin):
    list_display = ('autorizacion', 'campo_modificado', 'usuario', 'fecha')
    list_filter = ('campo_modificado',)
    search_fields = ('autorizacion__numero_resolucion',)
    ordering = ('-fecha',)
    readonly_fields = ('autorizacion', 'fecha', 'usuario', 'campo_modificado', 
                       'valor_anterior', 'valor_nuevo', 'motivo')
