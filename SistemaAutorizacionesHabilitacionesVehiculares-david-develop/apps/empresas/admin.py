"""
Admin para empresas de transporte.
"""

from django.contrib import admin
from .models import EmpresaTransporte


@admin.register(EmpresaTransporte)
class EmpresaTransporteAdmin(admin.ModelAdmin):
    list_display = (
        'ruc', 'razon_social', 'representante_legal', 
        'estado', 'fecha_creacion'
    )
    list_filter = ('estado', 'departamento', 'provincia')
    search_fields = ('ruc', 'razon_social', 'nombre_comercial', 'representante_legal')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'creado_por')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('ruc', 'razon_social', 'nombre_comercial', 'estado')
        }),
        ('Ubicación', {
            'fields': ('domicilio_fiscal', 'departamento', 'provincia', 'distrito')
        }),
        ('Representante Legal', {
            'fields': ('representante_legal', 'dni_representante')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email')
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
        if not change:  # Solo al crear
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
