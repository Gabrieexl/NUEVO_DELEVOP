# Generated migration for splitting director roles

from django.db import migrations


def migrate_director_roles(apps, schema_editor):
    """Migrar usuarios DIRECTOR → DIRECTOR_GENERAL"""
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(rol='DIRECTOR').update(rol='DIRECTOR_GENERAL')


def reverse_migration(apps, schema_editor):
    """Revertir si es necesario"""
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(rol__in=['DIRECTOR_GENERAL', 'DIRECTOR_ADMINISTRATIVO']).update(rol='DIRECTOR')


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_alter_usuario_rol'),
    ]

    operations = [
        migrations.RunPython(migrate_director_roles, reverse_migration),
    ]
