"""
Modelos de configuración del sistema.
Rutas, frecuencias, tipos de servicio, tipos de vehículo y otros parámetros configurables.
"""

from django.db import models
from django.conf import settings

from utils.mixins import AuditMixin
from utils.constants import DepartamentosPeru


class TipoServicio(AuditMixin):
    """
    Modelo para tipos de servicio de transporte.
    Permite al usuario agregar o eliminar tipos de servicio.
    """
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único del tipo de servicio (ej: REGULAR, ESPECIAL)'
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre descriptivo del tipo de servicio'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del tipo de servicio'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el tipo de servicio está disponible para selección'
    )
    
    class Meta:
        verbose_name = 'Tipo de Servicio'
        verbose_name_plural = 'Tipos de Servicio'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class CategoriaVehiculo(AuditMixin):
    """
    Modelo para categorías de vehículo (M1, M2, M3, etc.).
    """
    
    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Código',
        help_text='Código de la categoría (ej: M1, M2, M3)'
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre descriptivo de la categoría'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    capacidad_minima = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Capacidad Mínima'
    )

    capacidad_maxima = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Capacidad Máxima'
    )

    peso_bruto_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso Bruto Máximo (kg)'
    )
    
    class Meta:
        verbose_name = 'Categoría de Vehículo'
        verbose_name_plural = 'Categorías de Vehículo'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Carroceria(AuditMixin):
    """
    Modelo para tipos de carrocería de vehículo.
    """
    
    categoria = models.ForeignKey(
        CategoriaVehiculo,
        on_delete=models.CASCADE,
        related_name='carrocerias',
        verbose_name='Categoría'
    )
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código',
        help_text='Código único de la carrocería (ej: SEDAN, OMNIBUS)'
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre descriptivo de la carrocería'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    capacidad_minima = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Capacidad Mínima'
    )

    capacidad_maxima = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Capacidad Máxima'
    )
    
    class Meta:
        verbose_name = 'Carrocería'
        verbose_name_plural = 'Carrocerías'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.categoria.codigo})"


class Ruta(AuditMixin):
    """
    Modelo para rutas de transporte.
    Define origen, destino y puntos intermedios.
    """
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código de Ruta',
        help_text='Código único identificador de la ruta (ej: R001, MDD-PEM-001)'
    )
    
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de Ruta',
        help_text='Nombre descriptivo de la ruta'
    )
    
    origen = models.CharField(
        max_length=100,
        verbose_name='Origen',
        help_text='Ciudad/localidad de origen'
    )
    
    destino = models.CharField(
        max_length=100,
        verbose_name='Destino',
        help_text='Ciudad/localidad de destino'
    )
    
    puntos_intermedios = models.TextField(
        blank=True,
        verbose_name='Puntos Intermedios',
        help_text='Puntos intermedios de la ruta, separados por coma'
    )
    
    distancia_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Distancia (km)',
        help_text='Distancia aproximada en kilómetros'
    )
    
    tiempo_estimado_minutos = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tiempo Estimado (minutos)',
        help_text='Tiempo estimado de viaje en minutos'
    )
    
    ambito = models.CharField(
        max_length=100,
        choices=DepartamentosPeru.CHOICES,
        default=DepartamentosPeru.MADRE_DE_DIOS,
        verbose_name='Ámbito',
        help_text='Ámbito territorial de la ruta'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si la ruta está disponible para asignación'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'
        ordering = ['codigo']
    
    def __str__(self):
        return f'{self.codigo} - {self.nombre}'
    
    @property
    def ruta_completa(self):
        """Retorna la descripcion completa de la ruta."""
        if self.puntos_intermedios:
            return f'{self.origen} -> {self.puntos_intermedios} -> {self.destino}'
        return f'{self.origen} -> {self.destino}'
    
    @property
    def tiempo_estimado_display(self):
        """Muestra tiempo en formato legible."""
        if not self.tiempo_estimado_minutos:
            return '-'
        horas = self.tiempo_estimado_minutos // 60
        minutos = self.tiempo_estimado_minutos % 60
        if horas > 0:
            return f'{horas}h {minutos}min'
        return f'{minutos}min'


class Frecuencia(AuditMixin):
    """
    Modelo para frecuencias de servicio.
    Define los horarios y días de operación.
    """
    
    DIAS_SEMANA = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
        ('SA', 'Sábado'),
        ('DO', 'Domingo'),
    ]
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código de Frecuencia',
        help_text='Código único identificador (ej: F001, DIARIO-AM)'
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre descriptivo de la frecuencia'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de la frecuencia'
    )
    
    hora_salida = models.TimeField(
        verbose_name='Hora de Salida'
    )
    
    hora_llegada_estimada = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Llegada Estimada'
    )
    
    dias_operacion = models.CharField(
        max_length=50,
        default='LU,MA,MI,JU,VI,SA,DO',
        verbose_name='Días de Operación',
        help_text='Días de la semana separados por coma (ej: LU,MA,MI,JU,VI)'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si la frecuencia está disponible para asignación'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Frecuencia'
        verbose_name_plural = 'Frecuencias'
        ordering = ['hora_salida']
    
    def __str__(self):
        return f'{self.codigo} - {self.nombre} ({self.hora_salida.strftime("%H:%M")})'
    
    @property
    def dias_operacion_lista(self):
        """Retorna lista de días de operación."""
        return self.dias_operacion.split(',') if self.dias_operacion else []
    
    @property
    def dias_operacion_display(self):
        """Retorna los días de operación en formato legible."""
        dias_map = dict(self.DIAS_SEMANA)
        dias = self.dias_operacion_lista
        return ', '.join([dias_map.get(d, d) for d in dias])
