from django.contrib import admin
from .models import Ruta, Frecuencia, TipoServicio, Carroceria, CategoriaVehiculo


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activo', 'fecha_creacion']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['nombre']


@admin.register(CategoriaVehiculo)
class CategoriaVehiculoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'capacidad_minima', 'capacidad_maxima', 'peso_bruto_maximo', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']


@admin.register(Carroceria)
class CarroceriaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'capacidad_minima', 'capacidad_maxima', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'categoria']
    search_fields = ['codigo', 'nombre']
    ordering = ['categoria', 'nombre']


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'origen', 'destino', 'distancia_km', 'activo']
    list_filter = ['activo', 'ambito']
    search_fields = ['codigo', 'nombre', 'origen', 'destino']
    ordering = ['codigo']


@admin.register(Frecuencia)
class FrecuenciaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'hora_salida', 'dias_operacion', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['hora_salida']
