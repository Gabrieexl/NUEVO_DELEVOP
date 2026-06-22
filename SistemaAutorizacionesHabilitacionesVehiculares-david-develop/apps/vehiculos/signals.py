"""
Signals para sincronizar vehículos con sus habilitaciones.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Vehiculo, HabilitacionVehicular
from utils.constants import EstadoVehiculo, EstadoHabilitacion


# Variable para desactivar signals temporalmente (usado durante procesamiento de trámites)
_signals_disabled = False


def disable_signals():
    """Desactiva los signals de sincronización."""
    global _signals_disabled
    _signals_disabled = True


def enable_signals():
    """Activa los signals de sincronización."""
    global _signals_disabled
    _signals_disabled = False


@receiver(pre_save, sender=Vehiculo)
def guardar_estado_anterior(sender, instance, **kwargs):
    """Guarda el estado anterior del vehículo para comparar después."""
    if instance.pk:
        try:
            instance._estado_anterior = Vehiculo.objects.get(pk=instance.pk).estado
            instance._autorizacion_anterior = Vehiculo.objects.get(pk=instance.pk).autorizacion_principal_id
        except Vehiculo.DoesNotExist:
            instance._estado_anterior = None
            instance._autorizacion_anterior = None
    else:
        instance._estado_anterior = None
        instance._autorizacion_anterior = None


@receiver(post_save, sender=Vehiculo)
def sincronizar_habilitacion_vehicular(sender, instance, created, **kwargs):
    if _signals_disabled:
        return

    hoy = timezone.now().date()
    estado_anterior = getattr(instance, '_estado_anterior', None)
    autorizacion_anterior = getattr(instance, '_autorizacion_anterior', None)

    # --- LA FECHA MAESTRA ---
    fecha_base = instance.fecha_resolucion if instance.fecha_resolucion else hoy

    # =========================================================
    # 1. SINCRONIZACIÓN CONTINUA (AL EDITAR)
    # =========================================================
    # Si solo editan la fecha de un vehículo ya HABILITADO, actualiza su "DESDE"
    if instance.estado == EstadoVehiculo.HABILITADO and instance.autorizacion_principal:
        HabilitacionVehicular.objects.filter(
            vehiculo=instance,
            autorizacion=instance.autorizacion_principal,
            estado=EstadoHabilitacion.VIGENTE
        ).update(fecha_inicio=fecha_base)

    # Si solo editan la fecha de un vehículo ya en BAJA, actualiza el "HASTA"
    elif instance.estado == EstadoVehiculo.BAJA:
        ultima_baja = HabilitacionVehicular.objects.filter(
            vehiculo=instance,
            estado=EstadoHabilitacion.BAJA
        ).order_by('-id').first()

        if ultima_baja:
            ultima_baja.fecha_fin = fecha_base
            if instance.numero_resolucion:
                ultima_baja.motivo = f'Baja por Resolución N° {instance.numero_resolucion}'
            ultima_baja.save()

    # =========================================================
    # 2. TRANSICIONES DE ESTADO
    # =========================================================
    if instance.estado == EstadoVehiculo.HABILITADO and instance.autorizacion_principal:
        habilitacion_existente = HabilitacionVehicular.objects.filter(
            vehiculo=instance,
            autorizacion=instance.autorizacion_principal,
            estado=EstadoHabilitacion.VIGENTE
        ).first()

        # Si NO hay habilitación vigente, es un ALTA NUEVA
        if not habilitacion_existente:
            # Si cambió de autorización
            if autorizacion_anterior and autorizacion_anterior != instance.autorizacion_principal_id:
                HabilitacionVehicular.objects.filter(
                    vehiculo=instance,
                    autorizacion_id=autorizacion_anterior,
                    estado=EstadoHabilitacion.VIGENTE
                ).update(
                    estado=EstadoHabilitacion.BAJA,
                    fecha_fin=fecha_base,
                    motivo='Cambio de autorización'
                )

            HabilitacionVehicular.objects.create(
                vehiculo=instance,
                autorizacion=instance.autorizacion_principal,
                fecha_inicio=fecha_base,
                estado=EstadoHabilitacion.VIGENTE,
                motivo='Habilitación por registro en sistema'
            )

    # Cuando pasa a BAJA o NO HABILITADO
    elif instance.estado in [EstadoVehiculo.BAJA, EstadoVehiculo.NO_HABILITADO]:
        if estado_anterior == EstadoVehiculo.HABILITADO:
            motivo_baja = (
                f'Baja por Resolución N° {instance.numero_resolucion}'
                if instance.numero_resolucion
                else f'Vehículo pasó a estado {instance.get_estado_display()}'
            )

            HabilitacionVehicular.objects.filter(
                vehiculo=instance,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=fecha_base,
                motivo=motivo_baja
            )