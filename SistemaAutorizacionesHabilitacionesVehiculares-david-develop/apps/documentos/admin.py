"""
Admin para documentos.
"""

from django.contrib import admin
from .models import DocumentoAdjunto


@admin.register(DocumentoAdjunto)
class DocumentoAdjuntoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'tipo_documento', 'tramite', 
        'verificado', 'fecha_subida', 'subido_por'
    )
    list_filter = ('tipo_documento', 'verificado')
    search_fields = ('nombre', 'tramite__numero_expediente', 'descripcion')
    ordering = ('-fecha_subida',)
    readonly_fields = ('fecha_subida', 'subido_por', 'fecha_verificacion', 'verificado_por')
    autocomplete_fields = ['tramite', 'vehiculo', 'conductor']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('tramite', 'tipo_documento', 'nombre', 'descripcion', 'archivo')
        }),
        ('Asociaciones', {
            'fields': ('vehiculo', 'conductor'),
            'classes': ('collapse',)
        }),
        ('Verificación', {
            'fields': ('verificado', 'observaciones', 'fecha_verificacion', 'verificado_por')
        }),
        ('Auditoría', {
            'fields': ('subido_por', 'fecha_subida'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.subido_por = request.user
        super().save_model(request, obj, form, change)
