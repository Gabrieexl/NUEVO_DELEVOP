"""
Signals para manejar cambios de estado en EmpresaTransporte
y propagar los efectos a sus autorizaciones y vehículos.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import EmpresaTransporte
from utils.constants import (
    EstadoEmpresa, EstadoAutorizacion, EstadoVehiculo,
    EstadoHabilitacion, TagsBajaAutomatica
)

def _agregar_tag(texto, tag):
    texto = (texto or "").strip()
    if tag in texto:
        return texto
    return f"{texto}\n{tag}".strip()


def _remover_tag(texto, tag):
    lineas = [linea.strip() for linea in (texto or "").splitlines() if linea.strip()]
    return "\n".join(linea for linea in lineas if linea != tag).strip()


@receiver(pre_save, sender=EmpresaTransporte)
def guardar_estado_anterior_empresa(sender, instance, **kwargs):
    """Guarda el estado anterior de la empresa antes de guardar."""
    if instance.pk:
        try:
            anterior = EmpresaTransporte.objects.get(pk=instance.pk)
            instance._estado_anterior = anterior.estado
        except EmpresaTransporte.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=EmpresaTransporte)
def propagar_cambio_empresa(sender, instance, created, **kwargs):
    """
    Cuando la empresa cambia de estado, propaga el efecto en cascada
    a sus autorizaciones y vehículos.
    """
    from apps.autorizaciones.models import Autorizacion
    from apps.vehiculos.models import Vehiculo, HabilitacionVehicular

    hoy = timezone.now().date()
    estado_anterior = getattr(instance, '_estado_anterior', None)
    estado_nuevo = instance.estado

    if estado_anterior == estado_nuevo:
        return

    # =========================================================
    # CASO 1: Empresa pasa a INACTIVA
    #         → Sus autorizaciones VIGENTES se suspenden (con tag)
    #         → Sus vehículos HABILITADOS pasan a NO_HABILITADO (con tag)
    # =========================================================
    if estado_nuevo == EstadoEmpresa.INACTIVA:
        tag_aut = TagsBajaAutomatica.AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA
        tag_veh = TagsBajaAutomatica.NO_HABILITADO_POR_EMPRESA_INACTIVA

        autorizaciones_vigentes = Autorizacion.objects.filter(
            empresa=instance,
            estado=EstadoAutorizacion.VIGENTE
        )
        for autorizacion in autorizaciones_vigentes:
            obs_aut = _agregar_tag(autorizacion.observaciones, tag_aut)
            # Usamos update para NO disparar el signal de Autorizacion
            # (ya que el signal de empresa maneja los vehículos directamente)
            Autorizacion.objects.filter(pk=autorizacion.pk).update(
                estado=EstadoAutorizacion.SUSPENDIDA,
                observaciones=obs_aut
            )

        # Vehículos HABILITADOS de la empresa → NO_HABILITADO con tag
        motivo = 'Auto: Empresa pasó a estado INACTIVA'
        vehiculos_habilitados = Vehiculo.objects.filter(
            empresa_propietaria=instance,
            estado=EstadoVehiculo.HABILITADO
        )
        for vehiculo in vehiculos_habilitados:
            HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=hoy,
                motivo=motivo
            )
            obs_veh = _agregar_tag(vehiculo.observaciones, tag_veh)
            Vehiculo.objects.filter(pk=vehiculo.pk).update(
                estado=EstadoVehiculo.NO_HABILITADO,
                observaciones=obs_veh
            )

    # =========================================================
    # CASO 2: Empresa vuelve a ACTIVA
    #         → Sus autorizaciones con tag → vuelven a VIGENTE (si no vencieron)
    #         → Sus vehículos con tag → vuelven a HABILITADO
    #            (solo si su autorización quedó vigente)
    # =========================================================
    elif estado_nuevo == EstadoEmpresa.ACTIVA:
        tag_aut = TagsBajaAutomatica.AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA
        tag_veh = TagsBajaAutomatica.NO_HABILITADO_POR_EMPRESA_INACTIVA

        autorizaciones_a_restaurar = Autorizacion.objects.filter(
            empresa=instance,
            estado=EstadoAutorizacion.SUSPENDIDA,
            observaciones__contains=tag_aut
        )
        for autorizacion in autorizaciones_a_restaurar:
            # Solo restaurar si todavía hay vigencia
            if autorizacion.fecha_fin_vigencia >= hoy:
                obs_limpias = _remover_tag(autorizacion.observaciones, tag_aut)
                Autorizacion.objects.filter(pk=autorizacion.pk).update(
                    estado=EstadoAutorizacion.VIGENTE,
                    observaciones=obs_limpias
                )

                # Rehabilitar vehículos de esa autorización que tengan el tag
                vehiculos_a_rehabilitar = Vehiculo.objects.filter(
                    empresa_propietaria=instance,
                    autorizacion_principal=autorizacion,
                    estado=EstadoVehiculo.NO_HABILITADO,
                    observaciones__contains=tag_veh
                )
                for vehiculo in vehiculos_a_rehabilitar:
                    HabilitacionVehicular.objects.create(
                        vehiculo=vehiculo,
                        autorizacion=autorizacion,
                        fecha_inicio=hoy,
                        estado=EstadoHabilitacion.VIGENTE,
                        motivo='Auto: Rehabilitación por reactivación de empresa'
                    )
                    obs_limpias_veh = _remover_tag(vehiculo.observaciones, tag_veh)
                    Vehiculo.objects.filter(pk=vehiculo.pk).update(
                        estado=EstadoVehiculo.HABILITADO,
                        observaciones=obs_limpias_veh
                    )