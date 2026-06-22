from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("vehiculos", "0008_alter_vehiculo_anio_fabricacion"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE vehiculos_vehiculo DROP CONSTRAINT IF EXISTS vehiculos_vehiculo_placa_key;",
            reverse_sql="ALTER TABLE vehiculos_vehiculo ADD CONSTRAINT vehiculos_vehiculo_placa_key UNIQUE (placa);",
        ),
    ]