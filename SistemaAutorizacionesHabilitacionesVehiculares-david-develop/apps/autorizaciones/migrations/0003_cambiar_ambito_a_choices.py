# Generated migration to change ambito field

from django.db import migrations, models


def convertir_ambito_existente(apps, schema_editor):
    """Convierte los valores existentes de ámbito al nuevo formato."""
    Autorizacion = apps.get_model('autorizaciones', 'Autorizacion')
    
    # Mapeo de valores existentes a nuevos valores
    mapeo = {
        'Regional Madre de Dios': 'MADRE_DE_DIOS',
        'Madre de Dios': 'MADRE_DE_DIOS',
        'MADRE_DE_DIOS': 'MADRE_DE_DIOS',
        'Regional Cusco': 'CUSCO',
        'Cusco': 'CUSCO',
        'CUSCO': 'CUSCO',
    }
    
    for autorizacion in Autorizacion.objects.all():
        nuevo_valor = mapeo.get(autorizacion.ambito, 'MADRE_DE_DIOS')
        autorizacion.ambito = nuevo_valor
        autorizacion.save()


def revertir_ambito(apps, schema_editor):
    """Revierte los valores al formato anterior."""
    Autorizacion = apps.get_model('autorizaciones', 'Autorizacion')
    
    mapeo = {
        'MADRE_DE_DIOS': 'Regional Madre de Dios',
        'CUSCO': 'Regional Cusco',
    }
    
    for autorizacion in Autorizacion.objects.all():
        nuevo_valor = mapeo.get(autorizacion.ambito, 'Regional Madre de Dios')
        autorizacion.ambito = nuevo_valor
        autorizacion.save()


class Migration(migrations.Migration):

    dependencies = [
        ('autorizaciones', '0002_autorizacion_frecuencias_asignadas_and_more'),
    ]

    operations = [
        # Primero, convertir datos existentes
        migrations.RunPython(convertir_ambito_existente, revertir_ambito),
        
        # Luego, cambiar el campo
        migrations.AlterField(
            model_name='autorizacion',
            name='ambito',
            field=models.CharField(
                choices=[
                    ('AMAZONAS', 'Amazonas'),
                    ('ANCASH', 'Áncash'),
                    ('APURIMAC', 'Apurímac'),
                    ('AREQUIPA', 'Arequipa'),
                    ('AYACUCHO', 'Ayacucho'),
                    ('CAJAMARCA', 'Cajamarca'),
                    ('CALLAO', 'Callao'),
                    ('CUSCO', 'Cusco'),
                    ('HUANCAVELICA', 'Huancavelica'),
                    ('HUANUCO', 'Huánuco'),
                    ('ICA', 'Ica'),
                    ('JUNIN', 'Junín'),
                    ('LA_LIBERTAD', 'La Libertad'),
                    ('LAMBAYEQUE', 'Lambayeque'),
                    ('LIMA', 'Lima'),
                    ('LORETO', 'Loreto'),
                    ('MADRE_DE_DIOS', 'Madre de Dios'),
                    ('MOQUEGUA', 'Moquegua'),
                    ('PASCO', 'Pasco'),
                    ('PIURA', 'Piura'),
                    ('PUNO', 'Puno'),
                    ('SAN_MARTIN', 'San Martín'),
                    ('TACNA', 'Tacna'),
                    ('TUMBES', 'Tumbes'),
                    ('UCAYALI', 'Ucayali'),
                ],
                default='MADRE_DE_DIOS',
                help_text='Departamento/Región donde opera la autorización',
                max_length=20,
                verbose_name='Ámbito Regional'
            ),
        ),
    ]
