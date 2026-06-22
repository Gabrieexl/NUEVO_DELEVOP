"""
Modelos para el sistema de notificaciones.
DRTC - Dirección Regional de Transportes y Comunicaciones
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class TipoNotificacion(models.TextChoices):
    """Tipos de notificación disponibles"""
    # Notificaciones de trámites
    TRAMITE_RECIBIDO = 'tramite_recibido', 'Trámite Recibido'
    TRAMITE_EN_EVALUACION = 'tramite_evaluacion', 'Trámite en Evaluación Técnica'
    TRAMITE_OBSERVADO = 'tramite_observado', 'Trámite Observado'
    TRAMITE_SUBSANADO = 'tramite_subsanado', 'Trámite Subsanado'
    TRAMITE_EN_LEGAL = 'tramite_legal', 'Trámite en Revisión Legal'
    TRAMITE_PENDIENTE_FIRMA = 'tramite_firma', 'Trámite Pendiente de Firma'
    TRAMITE_APROBADO = 'tramite_aprobado', 'Trámite Aprobado'
    TRAMITE_DENEGADO = 'tramite_denegado', 'Trámite Denegado'
    
    # Alertas de vencimiento
    VENC_AUTORIZACION = 'venc_autorizacion', 'Vencimiento de Autorización'
    VENC_SOAT = 'venc_soat', 'Vencimiento de SOAT'
    VENC_CITV = 'venc_citv', 'Vencimiento de CITV'
    VENC_LICENCIA = 'venc_licencia', 'Vencimiento de Licencia'
    VENC_HABILITACION = 'venc_habilitacion', 'Vencimiento de Habilitación'
    
    # Alertas de plazo
    PLAZO_SUBSANACION = 'plazo_subsanacion', 'Plazo de Subsanación Próximo a Vencer'
    
    # Otras
    SISTEMA = 'sistema', 'Notificación del Sistema'


class PrioridadNotificacion(models.TextChoices):
    """Prioridades de notificación"""
    BAJA = 'baja', 'Baja'
    MEDIA = 'media', 'Media'
    ALTA = 'alta', 'Alta'
    URGENTE = 'urgente', 'Urgente'


class Notificacion(models.Model):
    """
    Modelo para notificaciones in-app.
    Estas notificaciones se muestran en el sistema (campanita).
    """
    # Destinatario
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    
    # Contenido
    tipo = models.CharField(
        max_length=30,
        choices=TipoNotificacion.choices,
        default=TipoNotificacion.SISTEMA,
        verbose_name='Tipo'
    )
    titulo = models.CharField(max_length=200, verbose_name='Título')
    mensaje = models.TextField(verbose_name='Mensaje')
    prioridad = models.CharField(
        max_length=10,
        choices=PrioridadNotificacion.choices,
        default=PrioridadNotificacion.MEDIA,
        verbose_name='Prioridad'
    )
    
    # Enlaces relacionados
    url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='URL de acción',
        help_text='URL para redirigir al hacer clic en la notificación'
    )
    
    # Referencias a objetos relacionados (opcional)
    tramite_id = models.IntegerField(null=True, blank=True, verbose_name='ID de Trámite')
    empresa_id = models.IntegerField(null=True, blank=True, verbose_name='ID de Empresa')
    vehiculo_id = models.IntegerField(null=True, blank=True, verbose_name='ID de Vehículo')
    conductor_id = models.IntegerField(null=True, blank=True, verbose_name='ID de Conductor')
    
    # Estado
    leida = models.BooleanField(default=False, verbose_name='Leída')
    fecha_lectura = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de lectura')
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['tipo']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
    
    def marcar_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save(update_fields=['leida', 'fecha_lectura'])


class ConfiguracionNotificacion(models.Model):
    """
    Configuración de notificaciones por usuario.
    Permite a cada usuario personalizar qué notificaciones recibir.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='config_notificaciones',
        verbose_name='Usuario'
    )
    
    # Notificaciones por email
    email_tramite_cambio_estado = models.BooleanField(
        default=True,
        verbose_name='Email en cambio de estado de trámite'
    )
    email_tramite_observado = models.BooleanField(
        default=True,
        verbose_name='Email cuando trámite es observado'
    )
    email_tramite_aprobado = models.BooleanField(
        default=True,
        verbose_name='Email cuando trámite es aprobado/denegado'
    )
    email_vencimientos = models.BooleanField(
        default=True,
        verbose_name='Email de alertas de vencimiento'
    )
    email_plazo_subsanacion = models.BooleanField(
        default=True,
        verbose_name='Email de plazo de subsanación'
    )
    
    # Notificaciones in-app
    app_tramite_cambio_estado = models.BooleanField(
        default=True,
        verbose_name='Notificación in-app en cambio de estado'
    )
    app_vencimientos = models.BooleanField(
        default=True,
        verbose_name='Notificación in-app de vencimientos'
    )
    
    # Días de anticipación para alertas de vencimiento
    dias_alerta_vencimiento = models.PositiveIntegerField(
        default=30,
        verbose_name='Días de anticipación para alertas',
        help_text='Número de días antes del vencimiento para enviar alerta'
    )
    
    class Meta:
        verbose_name = 'Configuración de Notificación'
        verbose_name_plural = 'Configuraciones de Notificaciones'
    
    def __str__(self):
        return f"Config. notificaciones de {self.usuario.username}"


class HistorialEmailEnviado(models.Model):
    """
    Registro de emails enviados por el sistema.
    Complementa el registro de django-post_office con información adicional.
    """
    # Destinatario
    email_destino = models.EmailField(verbose_name='Email destino')
    nombre_destino = models.CharField(max_length=200, blank=True, verbose_name='Nombre destino')
    
    # Usuario relacionado (si aplica)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_recibidos',
        verbose_name='Usuario'
    )
    
    # Contenido
    tipo = models.CharField(
        max_length=30,
        choices=TipoNotificacion.choices,
        default=TipoNotificacion.SISTEMA,
        verbose_name='Tipo'
    )
    asunto = models.CharField(max_length=300, verbose_name='Asunto')
    
    # Referencias
    tramite_id = models.IntegerField(null=True, blank=True, verbose_name='ID de Trámite')
    empresa_id = models.IntegerField(null=True, blank=True, verbose_name='ID de Empresa')
    
    # Estado
    enviado = models.BooleanField(default=False, verbose_name='Enviado')
    fecha_envio = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de envío')
    error = models.TextField(blank=True, verbose_name='Error')
    intentos = models.PositiveIntegerField(default=0, verbose_name='Intentos')
    
    # Referencia al email en post_office (opcional)
    post_office_email_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID en Post Office'
    )
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    
    class Meta:
        verbose_name = 'Historial de Email Enviado'
        verbose_name_plural = 'Historial de Emails Enviados'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['email_destino']),
            models.Index(fields=['tipo']),
            models.Index(fields=['enviado']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        estado = "[OK]" if self.enviado else "[X]"
        return f"{estado} {self.asunto} -> {self.email_destino}"
