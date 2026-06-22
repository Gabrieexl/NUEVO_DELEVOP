"""
Comando de gestión para verificar y actualizar automáticamente
el estado de las autorizaciones según sus fechas de vigencia.

Uso:
    python manage.py verificar_autorizaciones

Programar en Windows Task Scheduler o Linux cron para ejecutarse diariamente.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.autorizaciones.models import Autorizacion
from utils.constants import EstadoAutorizacion


class Command(BaseCommand):
    help = 'Verifica autorizaciones vencidas y actualiza su estado (y el de sus vehículos en cascada)'

    def handle(self, *args, **options):
        hoy = timezone.now().date()
        actualizadas = 0
        errores = 0

        self.stdout.write(f'[{hoy}] Verificando autorizaciones...')

        # Buscar autorizaciones VIGENTES cuya fecha_fin_vigencia ya pasó
        autorizaciones_vencidas = Autorizacion.objects.filter(
            estado=EstadoAutorizacion.VIGENTE,
            fecha_fin_vigencia__lt=hoy
        )

        total = autorizaciones_vencidas.count()
        self.stdout.write(f'  Autorizaciones vencidas encontradas: {total}')

        for autorizacion in autorizaciones_vencidas:
            try:
                # Guardar estado anterior manualmente (el pre_save no se llama con .save() interno)
                autorizacion._estado_anterior = EstadoAutorizacion.VIGENTE
                autorizacion.estado = EstadoAutorizacion.VENCIDA
                autorizacion.save()  # Esto dispara el signal post_save → cascada a vehículos
                actualizadas += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ [{autorizacion.empresa.nombre_corto}] '
                        f'{autorizacion.numero_resolucion} → VENCIDA '
                        f'(venció el {autorizacion.fecha_fin_vigencia})'
                    )
                )
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error en {autorizacion.numero_resolucion}: {e}'
                    )
                )

        self.stdout.write('')
        self.stdout.write(f'Resultado: {actualizadas} actualizadas, {errores} errores.')

        if actualizadas > 0:
            self.stdout.write(
                self.style.WARNING(
                    'Los vehículos habilitados de esas autorizaciones '
                    'pasaron automáticamente a NO HABILITADO.'
                )
            )
