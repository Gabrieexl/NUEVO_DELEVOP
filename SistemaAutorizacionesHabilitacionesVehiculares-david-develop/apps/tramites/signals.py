"""
Signals para registrar cambios de estado en trámites.
"""

from django.dispatch import receiver
from django_fsm.signals import post_transition

from .models import Tramite, HistorialTramite


@receiver(post_transition, sender=Tramite)
def registrar_transicion_tramite(sender, instance, name, source, target, **kwargs):
    """
    Registra automáticamente cada transición de estado en el historial.
    """
    # Obtener el usuario del método de transición si está disponible
    method_kwargs = kwargs.get('method_kwargs', {})
    usuario = method_kwargs.get('usuario')
    
    # Obtener comentario si existe en la instancia
    comentario = getattr(instance, '_comentario_transicion', f'Transición: {name}')
    
    # Crear registro en historial
    HistorialTramite.objects.create(
        tramite=instance,
        estado_anterior=source,
        estado_nuevo=target,
        usuario=usuario,
        accion=name,
        comentario=comentario
    )
