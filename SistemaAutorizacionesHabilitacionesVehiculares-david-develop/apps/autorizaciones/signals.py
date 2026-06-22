"""
Signals para manejar cambios de estado en Autorizaciones
y propagar los efectos a los vehículos.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Autorizacion
from utils.constants import EstadoAutorizacion, EstadoVehiculo, EstadoHabilitacion, TagsBajaAutomatica

def _agregar_tag(texto, tag):
    texto = (texto or "").strip()
    if tag in texto:
        return texto
    return f"{texto}\n{tag}".strip()


def _remover_tag(texto, tag):
    lineas = [linea.strip() for linea in (texto or "").splitlines() if linea.strip()]
    return "\n".join(linea for linea in lineas if linea != tag).strip()


@receiver(pre_save, sender=Autorizacion)
def guardar_estado_anterior_autorizacion(sender, instance, **kwargs):
    """Guarda el estado anterior de la autorización antes de guardar."""
    if instance.pk:
        try:
            anterior = Autorizacion.objects.get(pk=instance.pk)
            instance._estado_anterior = anterior.estado
        except Autorizacion.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Autorizacion)
def propagar_cambio_autorizacion(sender, instance, created, **kwargs):
    """
    Cuando cambia el estado de una autorización, actualiza el estado
    de los vehículos asociados según la lógica de cascada.
    """
    from apps.vehiculos.models import Vehiculo, HabilitacionVehicular

    hoy = timezone.now().date()
    estado_anterior = getattr(instance, '_estado_anterior', None)
    estado_nuevo = instance.estado

    # Si no hubo cambio de estado real, no hacer nada
    if estado_anterior == estado_nuevo:
        return

    # =========================================================
    # CASO 1: Autorización pasa a VENCIDA o SUSPENDIDA
    #         → Los HABILITADOS pasan a NO_HABILITADO (reversible con tag)
    # =========================================================
    if estado_nuevo in [EstadoAutorizacion.VENCIDA, EstadoAutorizacion.SUSPENDIDA]:
        if estado_nuevo == EstadoAutorizacion.VENCIDA:
            tag = TagsBajaAutomatica.NO_HABILITADO_POR_AUTORIZACION_VENCIDA
            motivo_hab = f'Auto: Autorización vencida ({instance.numero_resolucion})'
        else:
            tag = TagsBajaAutomatica.NO_HABILITADO_POR_AUTORIZACION_SUSPENDIDA
            motivo_hab = f'Auto: Autorización suspendida ({instance.numero_resolucion})'

        vehiculos_habilitados = Vehiculo.objects.filter(
            autorizacion_principal=instance,
            estado=EstadoVehiculo.HABILITADO
        )
        for vehiculo in vehiculos_habilitados:
            HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                autorizacion=instance,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=hoy,
                motivo=motivo_hab
            )
            obs_nueva = _agregar_tag(vehiculo.observaciones, tag)
            # Usamos update directo para no disparar el signal de Vehiculo
            Vehiculo.objects.filter(pk=vehiculo.pk).update(
                estado=EstadoVehiculo.NO_HABILITADO,
                observaciones=obs_nueva
            )

    # =========================================================
    # CASO 2: Autorización pasa a CANCELADA
    #         → Los HABILITADOS pasan a BAJA (permanente, sin tag)
    # =========================================================
    elif estado_nuevo == EstadoAutorizacion.CANCELADA:
        tag = TagsBajaAutomatica.BAJA_POR_CANCELACION_AUTORIZACION
        vehiculos_habilitados = Vehiculo.objects.filter(
            autorizacion_principal=instance,
            estado=EstadoVehiculo.HABILITADO
        )
        motivo_hab = f'Auto: Autorización cancelada ({instance.numero_resolucion})'
        for vehiculo in vehiculos_habilitados:
            HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                autorizacion=instance,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=hoy,
                motivo=motivo_hab
            )
            obs_nueva = _agregar_tag(vehiculo.observaciones, tag)
            Vehiculo.objects.filter(pk=vehiculo.pk).update(
                estado=EstadoVehiculo.BAJA,
                observaciones=obs_nueva
            )

    # =========================================================
    # CASO 3 y 4: Autorización vuelve a VIGENTE
    #         → Rehabilitar según el tag del estado anterior
    # =========================================================
    elif estado_nuevo == EstadoAutorizacion.VIGENTE:
        if estado_anterior == EstadoAutorizacion.VENCIDA:
            tag_buscar = TagsBajaAutomatica.NO_HABILITADO_POR_AUTORIZACION_VENCIDA
            estado_buscar = EstadoVehiculo.NO_HABILITADO
        elif estado_anterior == EstadoAutorizacion.SUSPENDIDA:
            tag_buscar = TagsBajaAutomatica.NO_HABILITADO_POR_AUTORIZACION_SUSPENDIDA
            estado_buscar = EstadoVehiculo.NO_HABILITADO
        else:
            return

        vehiculos_a_rehabilitar = Vehiculo.objects.filter(
            autorizacion_principal=instance,
            estado=estado_buscar,
            observaciones__contains=tag_buscar
        )
        for vehiculo in vehiculos_a_rehabilitar:
            HabilitacionVehicular.objects.create(
                vehiculo=vehiculo,
                autorizacion=instance,
                fecha_inicio=hoy,
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Auto: Rehabilitación por reactivación de autorización ({instance.numero_resolucion})'
            )
            obs_limpias = _remover_tag(vehiculo.observaciones, tag_buscar)
            Vehiculo.objects.filter(pk=vehiculo.pk).update(
                estado=EstadoVehiculo.HABILITADO,
                observaciones=obs_limpias
            )