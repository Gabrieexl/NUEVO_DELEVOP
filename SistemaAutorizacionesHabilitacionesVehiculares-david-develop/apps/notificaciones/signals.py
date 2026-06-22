"""
Signals para notificaciones automáticas en cambios de estado de trámites.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_fsm.signals import post_transition

logger = logging.getLogger(__name__)


# Signal para cambios de estado FSM en Tramite
@receiver(post_transition)
def tramite_estado_changed(sender, instance, name, source, target, **kwargs):
    """
    Signal que se dispara cuando un trámite cambia de estado usando FSM.
    
    Args:
        sender: Clase del modelo
        instance: Instancia del trámite
        name: Nombre de la transición
        source: Estado origen
        target: Estado destino
    """
    # Solo procesar si es un Tramite
    from apps.tramites.models import Tramite
    
    if not isinstance(instance, Tramite):
        return
    
    try:
        from .services import NotificacionService
        
        # Obtener comentario si existe en la instancia
        comentario = getattr(instance, '_comentario_transicion', '')
        
        # Obtener el usuario que realizó la acción
        method_kwargs = kwargs.get('method_kwargs', {})
        usuario_accion = method_kwargs.get('usuario')
        
        NotificacionService.notificar_cambio_estado_tramite(
            tramite=instance,
            estado_anterior=source,
            estado_nuevo=target,
            comentario=comentario,
            usuario_accion=usuario_accion
        )
        
        logger.info(
            f"Notificacion enviada para tramite {instance.numero_expediente}: "
            f"{source} -> {target}"
        )
        
    except Exception as e:
        logger.error(f"Error al enviar notificación de cambio de estado: {e}")


# Signal para crear configuración de notificaciones al crear usuario
@receiver(post_save, sender='usuarios.Usuario')
def crear_config_notificaciones_usuario(sender, instance, created, **kwargs):
    """
    Crea automáticamente la configuración de notificaciones cuando se crea un usuario.
    """
    if created:
        try:
            from .models import ConfiguracionNotificacion
            
            ConfiguracionNotificacion.objects.get_or_create(
                usuario=instance,
                defaults={
                    'email_tramite_cambio_estado': True,
                    'email_tramite_observado': True,
                    'email_tramite_aprobado': True,
                    'email_vencimientos': True,
                    'email_plazo_subsanacion': True,
                    'app_tramite_cambio_estado': True,
                    'app_vencimientos': True,
                    'dias_alerta_vencimiento': 30,
                }
            )
            logger.info(f"Config. notificaciones creada para usuario: {instance.username}")
            
        except Exception as e:
            logger.error(f"Error al crear config. notificaciones: {e}")
