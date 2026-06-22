"""
Mixins reutilizables para modelos y vistas.
"""

from django.db import models
from django.conf import settings


class TimestampMixin(models.Model):
    """
    Mixin que agrega campos de fecha de creación y actualización.
    """
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )
    
    class Meta:
        abstract = True


class AuditMixin(TimestampMixin):
    """
    Mixin que agrega campos de auditoría (usuario creador + timestamps).
    """
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_creados',
        verbose_name='Creado por',
        null=True,
        blank=True,
    )
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin para soft delete (eliminación lógica).
    """
    eliminado = models.BooleanField(default=False, verbose_name='Eliminado')
    fecha_eliminacion = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Fecha de eliminación'
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Realiza soft delete en lugar de eliminar físicamente."""
        from django.utils import timezone
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()
    
    def hard_delete(self):
        """Elimina físicamente el registro."""
        super().delete()
