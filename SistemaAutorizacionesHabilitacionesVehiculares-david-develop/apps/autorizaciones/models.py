"""
Modelos de autorizaciones de transporte.
"""

from django.db import models
from django.conf import settings

from utils.mixins import AuditMixin
from utils.constants import EstadoAutorizacion, DepartamentosPeru


class Autorizacion(AuditMixin):
    """
    Modelo para autorizaciones de servicio de transporte.
    """
    
    empresa = models.ForeignKey(
        'empresas.EmpresaTransporte',
        on_delete=models.PROTECT,
        related_name='autorizaciones',
        verbose_name='Empresa'
    )
    
    numero_resolucion = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de Resolución'
    )
    
    fecha_resolucion = models.DateField(
        verbose_name='Fecha de Resolución'
    )
    
    archivo_resolucion = models.FileField(
        upload_to='resoluciones/autorizaciones/',
        null=True,
        blank=True,
        verbose_name='Archivo de Resolución',
        help_text='Documento PDF de la resolución'
    )
    
    fecha_inicio_vigencia = models.DateField(
        verbose_name='Fecha Inicio de Vigencia'
    )
    
    fecha_fin_vigencia = models.DateField(
        verbose_name='Fecha Fin de Vigencia'
    )
    
    ambito = models.CharField(
        max_length=20,
        choices=DepartamentosPeru.CHOICES,
        default=DepartamentosPeru.MADRE_DE_DIOS,
        verbose_name='Ámbito Regional',
        help_text='Departamento/Región donde opera la autorización'
    )
    
    tipo_servicio = models.ForeignKey(
        'configuracion.TipoServicio',
        on_delete=models.PROTECT,
        related_name='autorizaciones',
        verbose_name='Tipo de Servicio',
        null=True,
        blank=True
    )
    
    modalidad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Modalidad',
        help_text='Modalidad del servicio (ej: Transporte regular de personas)'
    )
    
    # Relación con rutas configuradas
    rutas = models.ManyToManyField(
        'configuracion.Ruta',
        blank=True,
        related_name='autorizaciones',
        verbose_name='Rutas Autorizadas',
        help_text='Rutas asignadas a esta autorización'
    )
    
    # Relación con frecuencias configuradas
    frecuencias_asignadas = models.ManyToManyField(
        'configuracion.Frecuencia',
        blank=True,
        related_name='autorizaciones',
        verbose_name='Frecuencias Asignadas',
        help_text='Frecuencias de servicio asignadas'
    )
    
    # Campos de texto para descripción adicional (mantener por compatibilidad)
    descripcion_rutas = models.TextField(
        blank=True,
        verbose_name='Descripción de Rutas',
        help_text='Detalle adicional de las rutas autorizadas'
    )
    
    frecuencias = models.TextField(
        blank=True,
        verbose_name='Frecuencias (texto)',
        help_text='Descripción adicional de frecuencias y horarios'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoAutorizacion.CHOICES,
        default=EstadoAutorizacion.VIGENTE,
        verbose_name='Estado'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Autorización'
        verbose_name_plural = 'Autorizaciones'
        ordering = ['-fecha_resolucion']
    
    def __str__(self):
        return f'{self.numero_resolucion} - {self.empresa.nombre_corto}'
    
    @property
    def esta_vigente(self):
        """Verifica si la autorización está vigente."""
        from django.utils import timezone
        hoy = timezone.now().date()
        return (
            self.estado == EstadoAutorizacion.VIGENTE and
            self.fecha_inicio_vigencia <= hoy <= self.fecha_fin_vigencia
        )
    
    @property
    def dias_para_vencer(self):
        """Calcula los días restantes para el vencimiento."""
        from django.utils import timezone
        hoy = timezone.now().date()
        delta = self.fecha_fin_vigencia - hoy
        return delta.days


class HistorialAutorizacion(models.Model):
    """
    Historial de cambios en autorizaciones.
    """
    
    autorizacion = models.ForeignKey(
        Autorizacion,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Autorización'
    )
    
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario'
    )
    
    campo_modificado = models.CharField(
        max_length=100,
        verbose_name='Campo Modificado'
    )
    
    valor_anterior = models.TextField(
        blank=True,
        verbose_name='Valor Anterior'
    )
    
    valor_nuevo = models.TextField(
        blank=True,
        verbose_name='Valor Nuevo'
    )
    
    motivo = models.TextField(
        blank=True,
        verbose_name='Motivo del Cambio'
    )
    
    class Meta:
        verbose_name = 'Historial de Autorización'
        verbose_name_plural = 'Historial de Autorizaciones'
        ordering = ['-fecha']
    
    def __str__(self):
        return f'{self.autorizacion} - {self.campo_modificado} ({self.fecha})'
