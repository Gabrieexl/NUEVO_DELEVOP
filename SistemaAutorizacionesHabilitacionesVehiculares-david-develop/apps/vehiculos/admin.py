"""
Admin para vehículos.
"""

from django.contrib import admin
from .models import Vehiculo, HabilitacionVehicular


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'placa', 'marca', 'modelo', 'empresa_propietaria',
        'categoria', 'carroceria', 'capacidad_sentados', 'estado'
    )
    list_filter = ('estado', 'categoria', 'carroceria', 'marca')
    search_fields = ('placa', 'marca', 'modelo', 'empresa_propietaria__razon_social')
    ordering = ('placa',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'creado_por')
    autocomplete_fields = ['empresa_propietaria', 'autorizacion_principal']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('placa', 'empresa_propietaria', 'estado')
        }),
        ('Características del Vehículo', {
            'fields': ('marca', 'modelo', 'anio_fabricacion', 'color', 
                      'categoria', 'carroceria', 'capacidad_sentados', 'peso_bruto')
        }),
        ('Identificación', {
            'fields': ('numero_serie', 'numero_motor', 'numero_tiv')
        }),
        ('Documentos', {
            'fields': ('fecha_venc_soat', 'fecha_venc_citv')
        }),
        ('Autorización', {
            'fields': ('autorizacion_principal', 'vehiculo_sustituido')
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


@admin.register(HabilitacionVehicular)
class HabilitacionVehicularAdmin(admin.ModelAdmin):
    list_display = (
        'vehiculo', 'autorizacion', 'fecha_inicio', 
        'fecha_fin', 'estado'
    )
    list_filter = ('estado',)
    search_fields = ('vehiculo__placa', 'autorizacion__numero_resolucion')
    ordering = ('-fecha_inicio',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'creado_por')
    autocomplete_fields = ['vehiculo', 'autorizacion', 'tramite_origen']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
