"""
Servicio de notificaciones.
Centraliza la lógica de envío de notificaciones in-app y por email.
"""

import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from post_office import mail
from post_office.models import Email

from utils.constants import Roles, TipoTramite
from .models import (
    Notificacion,
    HistorialEmailEnviado,
    TipoNotificacion,
    PrioridadNotificacion,
    ConfiguracionNotificacion
)

logger = logging.getLogger(__name__)


class NotificacionService:
    """
    Servicio para gestionar notificaciones in-app y por email.
    """
    
    @staticmethod
    def crear_notificacion_inapp(
        usuario,
        tipo: str,
        titulo: str,
        mensaje: str,
        prioridad: str = PrioridadNotificacion.MEDIA,
        url: str = '',
        tramite_id: int = None,
        empresa_id: int = None,
        vehiculo_id: int = None,
        conductor_id: int = None
    ) -> Optional[Notificacion]:
        """
        Crea una notificación in-app para un usuario.
        
        Args:
            usuario: Usuario destinatario
            tipo: Tipo de notificación (TipoNotificacion)
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            prioridad: Prioridad (PrioridadNotificacion)
            url: URL para redirigir al hacer clic
            tramite_id: ID del trámite relacionado
            empresa_id: ID de la empresa relacionada
            vehiculo_id: ID del vehículo relacionado
            conductor_id: ID del conductor relacionado
            
        Returns:
            Notificacion creada o None si hay error
        """
        try:
            # Verificar configuración del usuario
            config = ConfiguracionNotificacion.objects.filter(usuario=usuario).first()
            
            # Si el usuario tiene configuración, verificar si quiere notificaciones in-app
            if config:
                if tipo.startswith('tramite_') and not config.app_tramite_cambio_estado:
                    return None
                if tipo.startswith('venc_') and not config.app_vencimientos:
                    return None
            
            notificacion = Notificacion.objects.create(
                usuario=usuario,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                prioridad=prioridad,
                url=url,
                tramite_id=tramite_id,
                empresa_id=empresa_id,
                vehiculo_id=vehiculo_id,
                conductor_id=conductor_id
            )
            
            logger.info(f"Notificación in-app creada: {titulo} para {usuario.username}")
            return notificacion
            
        except Exception as e:
            logger.error(f"Error al crear notificación in-app: {e}")
            return None
    
    @staticmethod
    def enviar_email(
        email_destino: str,
        asunto: str,
        template: str,
        context: Dict[str, Any],
        tipo: str = TipoNotificacion.SISTEMA,
        nombre_destino: str = '',
        usuario=None,
        tramite_id: int = None,
        empresa_id: int = None,
        prioridad: str = 'medium'
    ) -> Optional[HistorialEmailEnviado]:
        """
        Encola un email para envío usando django-post_office.
        
        Args:
            email_destino: Email del destinatario
            asunto: Asunto del email
            template: Nombre de la plantilla de email
            context: Contexto para renderizar la plantilla
            tipo: Tipo de notificación
            nombre_destino: Nombre del destinatario
            usuario: Usuario relacionado (opcional)
            tramite_id: ID del trámite relacionado
            empresa_id: ID de la empresa relacionada
            prioridad: Prioridad del email ('low', 'medium', 'high', 'now')
            
        Returns:
            HistorialEmailEnviado creado o None si hay error
        """
        # Email notifications disabled by user request
        logger.info(f"Email notification skipped (disabled): {asunto} -> {email_destino}")
        return None
        
        try:
            # Verificar configuración del usuario si existe
            if usuario:
                config = ConfiguracionNotificacion.objects.filter(usuario=usuario).first()
                if config:
                    if tipo.startswith('tramite_observado') and not config.email_tramite_observado:
                        return None
                    if tipo.startswith('tramite_aprobado') or tipo.startswith('tramite_denegado'):
                        if not config.email_tramite_aprobado:
                            return None
                    if tipo.startswith('venc_') and not config.email_vencimientos:
                        return None
                    if tipo == TipoNotificacion.PLAZO_SUBSANACION and not config.email_plazo_subsanacion:
                        return None
            
            # Agregar datos comunes al contexto
            context.update({
                'nombre_sistema': 'Sistema de Autorizaciones y Habilitaciones Vehiculares',
                'institucion': 'Direccion Regional de Transportes y Comunicaciones',
                'anio_actual': timezone.now().year,
                'sitio_web': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'drtc.gob.pe',
            })
            
            # Crear registro en historial
            historial = HistorialEmailEnviado.objects.create(
                email_destino=email_destino,
                nombre_destino=nombre_destino,
                usuario=usuario,
                tipo=tipo,
                asunto=asunto,
                tramite_id=tramite_id,
                empresa_id=empresa_id,
                enviado=False
            )
            
            # Renderizar plantilla HTML desde archivo
            from django.template.loader import render_to_string
            html_content = render_to_string(f'{template}.html', context)
            
            # Encolar email con post_office usando HTML directo
            email = mail.send(
                recipients=[email_destino],
                sender=settings.DEFAULT_FROM_EMAIL,
                subject=asunto,
                html_message=html_content,
                priority=prioridad,
            )
            
            # Actualizar historial con referencia al email de post_office
            if email:
                if isinstance(email, Email):
                    historial.post_office_email_id = email.id
                elif isinstance(email, list) and len(email) > 0:
                    historial.post_office_email_id = email[0].id if hasattr(email[0], 'id') else None
                historial.save(update_fields=['post_office_email_id'])
            
            logger.info(f"Email encolado: {asunto} -> {email_destino}")
            return historial
            
        except Exception as e:
            logger.error(f"Error al encolar email: {e}")
            if 'historial' in locals():
                historial.error = str(e)
                historial.save(update_fields=['error'])
            return None
    
    @staticmethod
    def enviar_email_simple(
        email_destino: str,
        asunto: str,
        mensaje_html: str,
        mensaje_texto: str = '',
        tipo: str = TipoNotificacion.SISTEMA,
        nombre_destino: str = '',
        usuario=None,
        tramite_id: int = None,
        empresa_id: int = None,
        prioridad: str = 'medium'
    ) -> Optional[HistorialEmailEnviado]:
        """
        Envía un email simple sin usar plantilla predefinida.
        
        Args:
            email_destino: Email del destinatario
            asunto: Asunto del email
            mensaje_html: Contenido HTML del email
            mensaje_texto: Contenido texto plano (opcional)
            tipo: Tipo de notificación
            nombre_destino: Nombre del destinatario
            usuario: Usuario relacionado
            tramite_id: ID del trámite relacionado
            empresa_id: ID de la empresa relacionada
            prioridad: Prioridad del email
            
        Returns:
            HistorialEmailEnviado o None
        """
        # Email notifications disabled by user request
        logger.info(f"Email simple notification skipped (disabled): {asunto} -> {email_destino}")
        return None

        try:
            # Crear registro en historial
            historial = HistorialEmailEnviado.objects.create(
                email_destino=email_destino,
                nombre_destino=nombre_destino,
                usuario=usuario,
                tipo=tipo,
                asunto=asunto,
                tramite_id=tramite_id,
                empresa_id=empresa_id,
                enviado=False
            )
            
            # Encolar email
            email = mail.send(
                recipients=[email_destino],
                sender=settings.DEFAULT_FROM_EMAIL,
                subject=asunto,
                html_message=mensaje_html,
                message=mensaje_texto or mensaje_html,
                priority=prioridad,
            )
            
            if email:
                if isinstance(email, Email):
                    historial.post_office_email_id = email.id
                elif isinstance(email, list) and len(email) > 0:
                    historial.post_office_email_id = email[0].id if hasattr(email[0], 'id') else None
                historial.save(update_fields=['post_office_email_id'])
            
            logger.info(f"Email simple encolado: {asunto} -> {email_destino}")
            return historial
            
        except Exception as e:
            logger.error(f"Error al encolar email simple: {e}")
            return None
    
    @staticmethod
    def notificar_cambio_estado_tramite(
        tramite,
        estado_anterior: str,
        estado_nuevo: str,
        comentario: str = '',
        usuario_accion=None
    ):
        """
        Notifica el cambio de estado de un trámite.
        Envía notificaciones a usuarios internos y al solicitante según corresponda.
        
        Args:
            tramite: Instancia del Trámite
            estado_anterior: Estado anterior del trámite
            estado_nuevo: Nuevo estado del trámite
            comentario: Comentario opcional
            usuario_accion: Usuario que realizó la acción (para excluirlo)
        """
        from apps.usuarios.models import Usuario
        from apps.tramites.models import EstadoTramite
        
        # Mapeo de estados a tipos de notificación
        tipo_por_estado = {
            EstadoTramite.RECIBIDO: TipoNotificacion.TRAMITE_RECIBIDO,
            EstadoTramite.EN_CONTROL_CALIDAD: TipoNotificacion.TRAMITE_EN_EVALUACION,
            EstadoTramite.EN_EVAL_TECNICA: TipoNotificacion.TRAMITE_EN_EVALUACION,
            EstadoTramite.OBSERVADO: TipoNotificacion.TRAMITE_OBSERVADO,
            EstadoTramite.EN_DIRECCION_ADMINISTRATIVA: TipoNotificacion.TRAMITE_PENDIENTE_FIRMA,
            EstadoTramite.EN_DIRECCION_GENERAL: TipoNotificacion.TRAMITE_PENDIENTE_FIRMA,
            EstadoTramite.EN_REVISION_LEGAL: TipoNotificacion.TRAMITE_EN_LEGAL,
            EstadoTramite.PENDIENTE_FIRMA: TipoNotificacion.TRAMITE_PENDIENTE_FIRMA,
            EstadoTramite.APROBADO: TipoNotificacion.TRAMITE_APROBADO,
            EstadoTramite.DENEGADO: TipoNotificacion.TRAMITE_DENEGADO,
        }
        
        tipo_notificacion = tipo_por_estado.get(estado_nuevo, TipoNotificacion.SISTEMA)
        
        # Determinar prioridad
        prioridad = PrioridadNotificacion.MEDIA
        if estado_nuevo in [EstadoTramite.OBSERVADO, EstadoTramite.DENEGADO]:
            prioridad = PrioridadNotificacion.ALTA
        elif estado_nuevo == EstadoTramite.APROBADO:
            prioridad = PrioridadNotificacion.ALTA
        
        # URL del trámite
        try:
            url_tramite = reverse('tramites:tramite_detail', kwargs={'pk': tramite.pk})
        except:
            url_tramite = f'/tramites/{tramite.pk}/'
        
        # Título y mensaje
        titulo = f"Tramite {tramite.numero_expediente} - {tramite.get_estado_display()}"
        mensaje = f"El tramite {tramite.numero_expediente} ha cambiado de estado: {estado_anterior} -> {estado_nuevo}"
        if comentario:
            mensaje += f"\n\nComentario: {comentario}"
        
        # 1. Notificar a usuarios internos según el nuevo estado
        usuarios_destino = []
        
        if estado_nuevo == EstadoTramite.RECIBIDO:
            # Notificar a mesa de partes
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.MESA_PARTES,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.EN_CONTROL_CALIDAD:
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.CONTROL_CALIDAD,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.EN_EVAL_TECNICA:
            # Notificar a especialistas técnicos
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.ESPECIALISTA_TECNICO,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.EN_REVISION_LEGAL:
            # Notificar a asesores legales
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.ASESORIA_LEGAL,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA:
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.DIRECTOR_ADMINISTRATIVO,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.EN_DIRECCION_GENERAL:
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.DIRECTOR_GENERAL,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.PENDIENTE_FIRMA:
            if tramite.tipo_tramite == TipoTramite.RENOVACION_TUC:
                usuarios_destino = list(Usuario.objects.filter(
                    rol=Roles.CONTROL_CALIDAD,
                    is_active=True
                ))
            elif tramite.tipo_tramite == TipoTramite.BAJA_VEHICULO:
                usuarios_destino = list(Usuario.objects.filter(
                    rol=Roles.DIRECTOR_GENERAL,
                    is_active=True
                ))
            else:
                # Notificar a directores
                usuarios_destino = list(Usuario.objects.filter(
                    rol__in=[Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO],
                    is_active=True
                ))
        elif estado_nuevo == EstadoTramite.OBSERVADO:
            # Notificar a mesa de partes para que contacten al administrado
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.MESA_PARTES,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.APROBADO and tramite.tipo_tramite in [
            TipoTramite.AUTORIZACION_INICIAL,
            TipoTramite.INCREMENTO_FLOTA,
            TipoTramite.RENOVACION_TUC,
        ]:
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.CONTROL_CALIDAD,
                is_active=True
            ))
        elif estado_nuevo in [EstadoTramite.APROBADO, EstadoTramite.DENEGADO]:
            # Notificar a mesa de partes para entrega de resolución
            usuarios_destino = list(Usuario.objects.filter(
                rol=Roles.MESA_PARTES,
                is_active=True
            ))
        elif estado_nuevo == EstadoTramite.CERRADO:
            # Notificar al creador que el trámite ha finalizado completamente
            if tramite.creado_por and tramite.creado_por.is_active:
                usuarios_destino = [tramite.creado_por]
        
        # Siempre notificar al creador del trámite si no está ya en la lista
        if tramite.creado_por and tramite.creado_por.is_active:
            if tramite.creado_por not in usuarios_destino:
                usuarios_destino.append(tramite.creado_por)
        
        # Si el trámite tiene un usuario asignado, notificarle también
        if tramite.usuario_actual and tramite.usuario_actual.is_active:
            if tramite.usuario_actual not in usuarios_destino:
                usuarios_destino.append(tramite.usuario_actual)
        
        # Crear notificaciones in-app para usuarios internos
        for usuario in usuarios_destino:
            # No notificar al usuario que realizó la acción
            if usuario_accion and usuario.id == usuario_accion.id:
                continue
                
            NotificacionService.crear_notificacion_inapp(
                usuario=usuario,
                tipo=tipo_notificacion,
                titulo=titulo,
                mensaje=mensaje,
                prioridad=prioridad,
                url=url_tramite,
                tramite_id=tramite.pk,
                empresa_id=tramite.empresa_id
            )
        
        # 2. Notificar al solicitante externo (Email deshabilitado por ahora)
        # Se mantiene la lógica pero no se envía email real por el cambio en enviar_email
        if estado_nuevo in [EstadoTramite.OBSERVADO, EstadoTramite.APROBADO, EstadoTramite.DENEGADO]:
            email_solicitante = tramite.solicitante_email
            if not email_solicitante and tramite.empresa:
                email_solicitante = tramite.empresa.email
            
            if email_solicitante:
                nombre_solicitante = tramite.solicitante_nombres or ''
                if not nombre_solicitante and tramite.empresa:
                    nombre_solicitante = tramite.empresa.razon_social
                
                # Determinar plantilla según estado
                if estado_nuevo == EstadoTramite.OBSERVADO:
                    template = 'emails/tramite_observado'
                elif estado_nuevo == EstadoTramite.APROBADO:
                    template = 'emails/tramite_aprobado'
                else:  # DENEGADO
                    template = 'emails/tramite_denegado'
                
                context = {
                    'nombre_solicitante': nombre_solicitante,
                    'numero_expediente': tramite.numero_expediente,
                    'tipo_tramite': tramite.get_tipo_tramite_display(),
                    'estado': tramite.get_estado_display(),
                    'fecha': timezone.now().strftime('%d/%m/%Y %H:%M'),
                    'comentario': comentario,
                    'tramite': tramite,
                }
                
                # Si hay plazo de subsanación, incluirlo
                if estado_nuevo == EstadoTramite.OBSERVADO and tramite.plazo_subsanacion:
                    context['plazo_subsanacion'] = tramite.plazo_subsanacion.strftime('%d/%m/%Y')
                
                NotificacionService.enviar_email(
                    email_destino=email_solicitante,
                    asunto=f"DRTC - {titulo}",
                    template=template,
                    context=context,
                    tipo=tipo_notificacion,
                    nombre_destino=nombre_solicitante,
                    tramite_id=tramite.pk,
                    empresa_id=tramite.empresa_id,
                    prioridad='high' if estado_nuevo in [EstadoTramite.APROBADO, EstadoTramite.DENEGADO] else 'medium'
                )
    
    @staticmethod
    def obtener_notificaciones_no_leidas(usuario, limite: int = 10) -> List[Notificacion]:
        """
        Obtiene las últimas notificaciones no leídas de un usuario.
        
        Args:
            usuario: Usuario
            limite: Número máximo de notificaciones a retornar
            
        Returns:
            Lista de notificaciones no leídas
        """
        return Notificacion.objects.filter(
            usuario=usuario,
            leida=False
        ).order_by('-fecha_creacion')[:limite]
    
    @staticmethod
    def contar_no_leidas(usuario) -> int:
        """
        Cuenta las notificaciones no leídas de un usuario.
        
        Args:
            usuario: Usuario
            
        Returns:
            Número de notificaciones no leídas
        """
        return Notificacion.objects.filter(
            usuario=usuario,
            leida=False
        ).count()
    
    @staticmethod
    def marcar_todas_leidas(usuario) -> int:
        """
        Marca todas las notificaciones de un usuario como leídas.
        
        Args:
            usuario: Usuario
            
        Returns:
            Número de notificaciones marcadas
        """
        return Notificacion.objects.filter(
            usuario=usuario,
            leida=False
        ).update(leida=True, fecha_lectura=timezone.now())
