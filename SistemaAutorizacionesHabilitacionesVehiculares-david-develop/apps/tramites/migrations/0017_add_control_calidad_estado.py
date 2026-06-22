import django_fsm
from django.db import migrations, models


ESTADO_TRAMITE_CHOICES = [
    ('RECIBIDO', 'Recibido'),
    ('EN_CONTROL_CALIDAD', 'En Control de Calidad'),
    ('EN_EVAL_TECNICA', 'En Evaluación Técnica'),
    ('EN_DIRECCION_ADMINISTRATIVA', 'En Dirección Administrativa'),
    ('EN_DIRECCION_GENERAL', 'En Dirección General'),
    ('OBSERVADO', 'Observado'),
    ('EN_REVISION_LEGAL', 'En Revisión Legal'),
    ('PENDIENTE_FIRMA', 'Pendiente de Firma'),
    ('APROBADO', 'Aprobado'),
    ('DENEGADO', 'Denegado'),
    ('CERRADO', 'Cerrado'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('tramites', '0016_alter_expedientehojaruta_estado_tramite_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expedientehojaruta',
            name='estado_tramite',
            field=models.CharField(choices=ESTADO_TRAMITE_CHOICES, max_length=30, verbose_name='Estado del Trámite al Registrar'),
        ),
        migrations.AlterField(
            model_name='historialtramite',
            name='estado_anterior',
            field=models.CharField(choices=ESTADO_TRAMITE_CHOICES, max_length=30, verbose_name='Estado Anterior'),
        ),
        migrations.AlterField(
            model_name='historialtramite',
            name='estado_nuevo',
            field=models.CharField(choices=ESTADO_TRAMITE_CHOICES, max_length=30, verbose_name='Estado Nuevo'),
        ),
        migrations.AlterField(
            model_name='tramite',
            name='estado',
            field=django_fsm.FSMField(choices=ESTADO_TRAMITE_CHOICES, default='RECIBIDO', max_length=50, protected=True, verbose_name='Estado'),
        ),
    ]
