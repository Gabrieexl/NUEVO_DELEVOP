# Generated manually to keep vehicle category data aligned with production.

from django.db import migrations


CATEGORIAS_PRODUCCION = {
    'M1': 'Categoría M1',
    'M2': 'Categoría M2',
    'M3': 'Categoría M3',
}


def normalizar_categorias_produccion(apps, schema_editor):
    CategoriaVehiculo = apps.get_model('configuracion', 'CategoriaVehiculo')

    for codigo, nombre in CATEGORIAS_PRODUCCION.items():
        categoria, creada = CategoriaVehiculo.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': '',
                'activo': True,
            },
        )
        if not creada and categoria.nombre != nombre:
            categoria.nombre = nombre
            categoria.save(update_fields=['nombre'])


class Migration(migrations.Migration):

    dependencies = [
        ('configuracion', '0008_alter_ruta_ambito'),
    ]

    operations = [
        migrations.RunPython(
            normalizar_categorias_produccion,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
