"""
Data migration para insertar los tipos de servicio iniciales.
"""

from django.db import migrations


def insertar_tipos_servicio(apps, schema_editor):
    """Inserta los tipos de servicio predefinidos."""
    TipoServicio = apps.get_model('configuracion', 'TipoServicio')
    
    tipos = [
        {
            'codigo': 'REGULAR',
            'nombre': 'Regular',
            'descripcion': 'Servicio de transporte público regular de personas',
            'activo': True,
        },
        {
            'codigo': 'ESPECIAL',
            'nombre': 'Especial',
            'descripcion': 'Servicio de transporte especial (turístico, escolar, etc.)',
            'activo': True,
        },
        {
            'codigo': 'TURISTICO',
            'nombre': 'Turístico',
            'descripcion': 'Servicio de transporte turístico',
            'activo': True,
        },
        {
            'codigo': 'TRABAJADORES',
            'nombre': 'Trabajadores',
            'descripcion': 'Servicio de transporte de trabajadores de empresas',
            'activo': True,
        },
    ]
    
    for tipo in tipos:
        TipoServicio.objects.get_or_create(
            codigo=tipo['codigo'],
            defaults=tipo
        )


def eliminar_tipos_servicio(apps, schema_editor):
    """Elimina los tipos de servicio predefinidos (para rollback)."""
    TipoServicio = apps.get_model('configuracion', 'TipoServicio')
    TipoServicio.objects.filter(
        codigo__in=['REGULAR', 'ESPECIAL', 'TURISTICO', 'TRABAJADORES']
    ).delete()


class Migration(migrations.Migration):
    """Data migration para tipos de servicio iniciales."""
    
    dependencies = [
        ('configuracion', '0002_add_tiposervicio_tipovehiculo'),
    ]
    
    operations = [
        migrations.RunPython(
            insertar_tipos_servicio,
            eliminar_tipos_servicio
        ),
    ]
