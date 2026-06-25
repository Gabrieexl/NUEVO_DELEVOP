from django.contrib import admin
from .models import Acta


@admin.register(Acta)
class ActaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha', 'placa', 'adminNombre', 'modalidad', 'estado', 'cantidad_infracciones')
    list_filter = ('estado', 'modalidad', 'tipoIntervencion', 'fecha')
    search_fields = ('numero', 'placa', 'adminNombre', 'adminDocNum', 'condVolNombre', 'lugar')
    date_hierarchy = 'fecha'
    readonly_fields = ('creadoEn', 'actualizadoEn')
    fieldsets = (
        ('Acta', {
            'fields': ('numero', 'fecha', 'hora', 'tipoIntervencion', 'lugar', 'estado'),
        }),
        ('Administrado', {
            'fields': ('adminTipo', 'adminDocTipo', 'adminDocNum', 'adminNombre', 'habilitacion'),
        }),
        ('Vehículo', {
            'fields': ('placa', 'modalidad', 'otroServicio', 'origen', 'destino'),
        }),
        ('Conductores', {
            'fields': (
                ('condVolNombre', 'condVolTipoId', 'condVolNum', 'condVolClase'),
                ('condAltNombre', 'condAltTipoId', 'condAltNum', 'condAltClase'),
            ),
        }),
        ('Resultado', {
            'fields': ('hechos', 'infracciones', 'incumplimientos', 'manifestacion', 'medida'),
        }),
        ('Archivo y firmas', {
            'fields': (
                'archivo',
                ('inspectorNombre', 'inspectorDni'),
                ('intervenidoNombre', 'intervenidoDni'),
                ('pnpNombre', 'pnpCip'),
            ),
        }),
        ('Trazabilidad', {
            'fields': ('creadoPor', 'creadoEn', 'actualizadoEn'),
        }),
    )
