"""
Signals para sincronizar conductores con sus habilitaciones.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Conductor, HabilitacionConductor
from apps.autorizaciones.models import Autorizacion
from utils.constants import EstadoHabilitacion


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


@receiver(pre_save, sender=Conductor)
def guardar_estado_anterior_conductor(sender, instance, **kwargs):
    """Guarda el estado anterior del conductor para comparar después."""
    if instance.pk:
        try:
            conductor_actual = Conductor.objects.get(pk=instance.pk)
            instance._estado_anterior = conductor_actual.estado
            instance._empresa_anterior = conductor_actual.empresa_id
        except Conductor.DoesNotExist:
            instance._estado_anterior = None
            instance._empresa_anterior = None
    else:
        instance._estado_anterior = None
        instance._empresa_anterior = None


@receiver(post_save, sender=Conductor)
def sincronizar_habilitacion_conductor(sender, instance, created, **kwargs):
    """
    Sincroniza la habilitación del conductor cuando se crea o actualiza.
    
    - Si el conductor está ACTIVO y tiene empresa, crear/actualizar habilitación
    - Si el conductor pasa a INACTIVO, dar de baja las habilitaciones
    """
    # No hacer nada si los signals están desactivados (ej: procesando trámite)
    if _signals_disabled:
        return
    
    hoy = timezone.now().date()
    estado_anterior = getattr(instance, '_estado_anterior', None)
    empresa_anterior = getattr(instance, '_empresa_anterior', None)
    
    # Caso 1: Conductor ACTIVO con empresa
    if instance.estado == 'ACTIVO' and instance.empresa:
        # Si se especificó una autorización en el formulario (vía atributo temporal)
        autorizacion_id = getattr(instance, '_autorizacion_id', None)
        
        if autorizacion_id:
            # Solo crear/actualizar para esta autorización específica
            autorizaciones = Autorizacion.objects.filter(id=autorizacion_id)
        else:
            # Comportamiento por defecto: todas las vigentes de la empresa
            autorizaciones = Autorizacion.objects.filter(
                empresa=instance.empresa,
                estado='VIGENTE'
            )
        
        # Si cambia de empresa, dar de baja las habilitaciones anteriores
        if empresa_anterior and empresa_anterior != instance.empresa_id:
            HabilitacionConductor.objects.filter(
                conductor=instance,
                empresa_id=empresa_anterior,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=hoy,
                motivo='Cambio de empresa'
            )
        
        # Crear habilitaciones para cada autorización vigente de la empresa
        for autorizacion in autorizaciones:
            habilitacion_existente = HabilitacionConductor.objects.filter(
                conductor=instance,
                empresa=instance.empresa,
                autorizacion=autorizacion,
                estado=EstadoHabilitacion.VIGENTE
            ).exists()
            
            if not habilitacion_existente:
                HabilitacionConductor.objects.create(
                    conductor=instance,
                    empresa=instance.empresa,
                    autorizacion=autorizacion,
                    fecha_inicio=hoy,
                    estado=EstadoHabilitacion.VIGENTE,
                    motivo='Habilitación automática por registro directo'
                )
    
    # Caso 2: Conductor pasa a INACTIVO
    elif instance.estado == 'INACTIVO':
        if estado_anterior == 'ACTIVO':
            # Dar de baja todas las habilitaciones vigentes
            HabilitacionConductor.objects.filter(
                conductor=instance,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=hoy,
                motivo='Conductor pasó a estado INACTIVO'
            )
    
    # Caso 3: Conductor ACTIVO pero sin empresa (quitar habilitaciones)
    elif instance.estado == 'ACTIVO' and not instance.empresa:
        if empresa_anterior:
            HabilitacionConductor.objects.filter(
                conductor=instance,
                empresa_id=empresa_anterior,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=hoy,
                motivo='Empresa removida del conductor'
            )
