"""
Data migration para insertar los tipos de vehículo iniciales.
"""

from django.db import migrations


def insertar_tipos_vehiculo(apps, schema_editor):
    """Inserta los tipos de vehículo predefinidos."""
    TipoVehiculo = apps.get_model('configuracion', 'TipoVehiculo')
    
    tipos = [
        {
            'codigo': 'AUTO',
            'nombre': 'Auto',
            'descripcion': 'Vehículo tipo automóvil',
            'capacidad_minima': 1,
            'capacidad_maxima': 5,
            'activo': True,
        },
        {
            'codigo': 'MINIVAN',
            'nombre': 'Minivan',
            'descripcion': 'Vehículo tipo minivan',
            'capacidad_minima': 6,
            'capacidad_maxima': 11,
            'activo': True,
        },
        {
            'codigo': 'VAN',
            'nombre': 'Van',
            'descripcion': 'Vehículo tipo van/furgoneta',
            'capacidad_minima': 12,
            'capacidad_maxima': 16,
            'activo': True,
        },
        {
            'codigo': 'MINIBUS',
            'nombre': 'Minibús',
            'descripcion': 'Vehículo tipo minibús',
            'capacidad_minima': 17,
            'capacidad_maxima': 25,
            'activo': True,
        },
        {
            'codigo': 'BUS',
            'nombre': 'Bus',
            'descripcion': 'Vehículo tipo bus',
            'capacidad_minima': 26,
            'capacidad_maxima': 60,
            'activo': True,
        },
        {
            'codigo': 'MULTIPROPOSITO',
            'nombre': 'Multipropósito',
            'descripcion': 'Vehículo multipropósito',
            'capacidad_minima': 1,
            'capacidad_maxima': 20,
            'activo': True,
        },
    ]
    
    for tipo in tipos:
        TipoVehiculo.objects.get_or_create(
            codigo=tipo['codigo'],
            defaults=tipo
        )


def eliminar_tipos_vehiculo(apps, schema_editor):
    """Elimina los tipos de vehículo predefinidos (para rollback)."""
    TipoVehiculo = apps.get_model('configuracion', 'TipoVehiculo')
    TipoVehiculo.objects.filter(
        codigo__in=['AUTO', 'MINIVAN', 'VAN', 'MINIBUS', 'BUS', 'MULTIPROPOSITO']
    ).delete()


class Migration(migrations.Migration):
    """Data migration para tipos de vehículo iniciales."""
    
    dependencies = [
        ('configuracion', '0003_data_tipos_servicio'),
    ]
    
    operations = [
        migrations.RunPython(
            insertar_tipos_vehiculo,
            eliminar_tipos_vehiculo
        ),
    ]
