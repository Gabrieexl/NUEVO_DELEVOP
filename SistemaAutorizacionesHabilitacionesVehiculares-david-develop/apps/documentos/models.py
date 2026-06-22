"""
Modelos para documentos adjuntos.
"""

import os
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from utils.constants import TipoDocumento
from utils.validators import validar_solo_pdf, ValidarTamanioArchivo


def documento_upload_path(instance, filename):
    """
    Genera la ruta de upload para documentos.
    Formato: documentos/{tramite_id}/{tipo_documento}/{filename}
    """
    tramite_id = instance.tramite.numero_expediente if instance.tramite else 'sin_tramite'
    # Sanitizar el nombre del expediente para usarlo como carpeta
    tramite_id = tramite_id.replace('/', '-').replace('\\', '-')
    return f'documentos/{tramite_id}/{instance.tipo_documento}/{filename}'


class DocumentoAdjunto(models.Model):
    """
    Modelo para documentos adjuntos a trámites.
    Solo acepta archivos PDF.
    """
    
    tramite = models.ForeignKey(
        'tramites.Tramite',
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Trámite'
    )
    
    tipo_documento = models.CharField(
        max_length=30,
        choices=TipoDocumento.CHOICES,
        verbose_name='Tipo de Documento'
    )
    
    nombre = models.CharField(
        max_length=255,
        verbose_name='Nombre del Documento'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    archivo = models.FileField(
        upload_to=documento_upload_path,
        validators=[validar_solo_pdf, ValidarTamanioArchivo(10)],
        verbose_name='Archivo PDF'
    )
    
    # Relaciones opcionales para asociar a entidades específicas
    vehiculo = models.ForeignKey(
        'vehiculos.Vehiculo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
        verbose_name='Vehículo Asociado'
    )
    
    conductor = models.ForeignKey(
        'conductores.Conductor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
        verbose_name='Conductor Asociado'
    )
    
    # Metadatos
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_subidos',
        verbose_name='Subido por'
    )
    
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Subida'
    )
    
    verificado = models.BooleanField(
        default=False,
        verbose_name='Verificado',
        help_text='Indica si el documento ha sido verificado'
    )
    
    fecha_verificacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Verificación'
    )
    
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_verificados',
        verbose_name='Verificado por'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Documento Adjunto'
        verbose_name_plural = 'Documentos Adjuntos'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_documento_display()})'
    
    @property
    def extension(self):
        """Retorna la extensión del archivo."""
        return os.path.splitext(self.archivo.name)[1].lower()
    
    @property
    def tamanio_mb(self):
        """Retorna el tamaño del archivo en MB."""
        if self.archivo:
            return round(self.archivo.size / (1024 * 1024), 2)
        return 0
    
    def clean(self):
        """Validaciones adicionales."""
        super().clean()
        # Validar que sea PDF
        if self.archivo:
            ext = os.path.splitext(self.archivo.name)[1].lower()
            if ext != '.pdf':
                raise ValidationError({
                    'archivo': 'Solo se permiten archivos PDF.'
                })
    
    def marcar_verificado(self, usuario):
        """Marca el documento como verificado."""
        from django.utils import timezone
        self.verificado = True
        self.fecha_verificacion = timezone.now()
        self.verificado_por = usuario
        self.save()
