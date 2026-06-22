"""
Admin para conductores.
"""

from django.contrib import admin
from .models import Conductor, HabilitacionConductor


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = (
        'dni', 'nombre_completo', 'licencia_numero', 
        'licencia_categoria', 'licencia_fecha_vencimiento', 'estado'
    )
    list_filter = ('estado', 'licencia_categoria')
    search_fields = ('dni', 'nombres', 'apellido_paterno', 'apellido_materno', 'licencia_numero')
    ordering = ('apellido_paterno', 'apellido_materno', 'nombres')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'creado_por')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('dni', 'nombres', 'apellido_paterno', 'apellido_materno', 
                      'fecha_nacimiento', 'estado')
        }),
        ('Contacto', {
            'fields': ('direccion', 'telefono', 'email')
        }),
        ('Licencia de Conducir', {
            'fields': ('licencia_numero', 'licencia_categoria', 
                      'licencia_fecha_emision', 'licencia_fecha_vencimiento')
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


@admin.register(HabilitacionConductor)
class HabilitacionConductorAdmin(admin.ModelAdmin):
    list_display = (
        'conductor', 'empresa', 'autorizacion',
        'fecha_inicio', 'fecha_fin', 'estado'
    )
    list_filter = ('estado',)
    search_fields = (
        'conductor__dni', 'conductor__nombres', 
        'empresa__razon_social', 'autorizacion__numero_resolucion'
    )
    ordering = ('-fecha_inicio',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'creado_por')
    autocomplete_fields = ['conductor', 'empresa', 'autorizacion', 'tramite_origen']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
