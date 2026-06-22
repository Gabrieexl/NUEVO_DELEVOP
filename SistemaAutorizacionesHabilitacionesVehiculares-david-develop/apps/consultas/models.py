"""
Modelos para consultas externas.
"""

import secrets
from django.db import models
from django.utils import timezone


class APIKey(models.Model):
    """
    API Key para acceso externo a consultas.
    """
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre identificador (ej: SUTRAN, PNP)"
    )
    clave = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="Clave de API generada automáticamente"
    )
    entidad = models.CharField(
        max_length=200,
        help_text="Entidad a la que pertenece la clave"
    )
    email_contacto = models.EmailField(
        blank=True,
        help_text="Email de contacto de la entidad"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Indica si la clave está activa"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de expiración (dejar vacío para no expirar)"
    )
    ultimo_uso = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se usó la clave"
    )
    total_consultas = models.PositiveIntegerField(
        default=0,
        help_text="Total de consultas realizadas"
    )
    limite_diario = models.PositiveIntegerField(
        default=1000,
        help_text="Límite de consultas por día (0 = sin límite)"
    )
    consultas_hoy = models.PositiveIntegerField(
        default=0,
        help_text="Consultas realizadas hoy"
    )
    fecha_reset_diario = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha del último reset del contador diario"
    )
    
    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.entidad}"
    
    def save(self, *args, **kwargs):
        if not self.clave:
            self.clave = self.generar_clave()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generar_clave():
        """Genera una clave API segura."""
        return secrets.token_hex(32)
    
    def esta_vigente(self):
        """Verifica si la clave está vigente."""
        if not self.activa:
            return False
        if self.fecha_expiracion and self.fecha_expiracion < timezone.now().date():
            return False
        return True
    
    def puede_consultar(self):
        """Verifica si puede realizar una consulta (límite diario)."""
        if not self.esta_vigente():
            return False
        
        # Reset contador si cambió el día
        hoy = timezone.now().date()
        if self.fecha_reset_diario != hoy:
            self.consultas_hoy = 0
            self.fecha_reset_diario = hoy
            self.save(update_fields=['consultas_hoy', 'fecha_reset_diario'])
        
        # Si límite es 0, sin límite
        if self.limite_diario == 0:
            return True
        
        return self.consultas_hoy < self.limite_diario
    
    def registrar_consulta(self):
        """Registra una consulta realizada."""
        hoy = timezone.now().date()
        
        if self.fecha_reset_diario != hoy:
            self.consultas_hoy = 1
            self.fecha_reset_diario = hoy
        else:
            self.consultas_hoy += 1
        
        self.total_consultas += 1
        self.ultimo_uso = timezone.now()
        self.save(update_fields=[
            'consultas_hoy', 'fecha_reset_diario', 
            'total_consultas', 'ultimo_uso'
        ])


class RegistroConsulta(models.Model):
    """
    Registro de consultas realizadas para auditoría.
    """
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros'
    )
    placa_consultada = models.CharField(max_length=10)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    resultado_exitoso = models.BooleanField(default=True)
    mensaje_error = models.TextField(blank=True)
    tiempo_respuesta_ms = models.PositiveIntegerField(
        default=0,
        help_text="Tiempo de respuesta en milisegundos"
    )
    
    class Meta:
        verbose_name = "Registro de Consulta"
        verbose_name_plural = "Registros de Consultas"
        ordering = ['-fecha_consulta']
    
    def __str__(self):
        return f"Consulta {self.placa_consultada} - {self.fecha_consulta}"
