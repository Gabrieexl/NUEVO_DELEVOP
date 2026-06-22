"""
Modelos de vehículos y habilitaciones vehiculares.
"""

from django.db import models
from django.conf import settings
from django.db.models import Q
from utils.mixins import AuditMixin
from utils.constants import EstadoVehiculo, EstadoHabilitacion
from utils.validators import validar_placa_vehicular
from utils.validators import validar_placa_vehicular, validar_anio_fabricacion_vehiculo

class Vehiculo(AuditMixin):
    """
    Modelo para vehículos de transporte.
    """
    
    placa = models.CharField(
        max_length=10,
        validators=[validar_placa_vehicular],
        verbose_name='Placa',
        help_text='Placa del vehículo (ej: ABC-123)'
    )
    
    empresa_propietaria = models.ForeignKey(
        'empresas.EmpresaTransporte',
        on_delete=models.PROTECT,
        related_name='vehiculos',
        verbose_name='Empresa Propietaria'
    )
    
    marca = models.CharField(
        max_length=50,
        verbose_name='Marca'
    )
    
    modelo = models.CharField(
        max_length=50,
        verbose_name='Modelo'
    )

    anio_fabricacion = models.PositiveIntegerField(
    validators=[validar_anio_fabricacion_vehiculo],
    verbose_name='Año de Fabricación'
    )
    
    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Color'
    )
    
    # Datos de resolución
    numero_resolucion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Resolución',
        help_text='Resolución de habilitación'
    )
    
    fecha_resolucion = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Resolución'
    )
    
    archivo_resolucion = models.FileField(
        upload_to='resoluciones/vehiculos/',
        null=True,
        blank=True,
        verbose_name='Archivo de Resolución'
    )
    
    numero_serie = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Serie/Chasis'
    )
    
    numero_motor = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Motor'
    )
    
    capacidad_sentados = models.PositiveIntegerField(
        verbose_name='Capacidad de Pasajeros Sentados'
    )
    
    peso_bruto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso Bruto (kg)',
        help_text='Peso bruto vehicular en kilogramos'
    )
    
    categoria = models.ForeignKey(
        'configuracion.CategoriaVehiculo',
        on_delete=models.PROTECT,
        related_name='vehiculos',
        verbose_name='Categoría',
        null=True,
        blank=True
    )
    
    carroceria = models.ForeignKey(
        'configuracion.Carroceria',
        on_delete=models.PROTECT,
        related_name='vehiculos',
        verbose_name='Carrocería',
        null=True,
        blank=True
    )
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoVehiculo.CHOICES,
        default=EstadoVehiculo.PROPUESTO,
        verbose_name='Estado'
    )
    
    # Documentos administrativos
    numero_tiv = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número TIV',
        help_text='Tarjeta de Identificación Vehicular'
    )
    
    fecha_venc_soat = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Vencimiento SOAT'
    )
    
    fecha_venc_citv = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Vencimiento CITV',
        help_text='Certificado de Inspección Técnica Vehicular'
    )
    
    # Relación con autorización principal
    autorizacion_principal = models.ForeignKey(
        'autorizaciones.Autorizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos_principales',
        verbose_name='Autorización Principal'
    )
    
    # Para sustituciones
    vehiculo_sustituido = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos_sustitutos',
        verbose_name='Vehículo Sustituido'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['placa']
        constraints = [  ###
            models.UniqueConstraint( ###
                fields=['placa'], ###
                condition=~Q(estado=EstadoVehiculo.BAJA), ###
                name='uq_placa_unica_si_no_esta_baja' ###
            )
        ]

    def save(self, *args, **kwargs):
        # Normalizar placa antes de guardar
        if self.placa:
            self.placa = self.placa.upper().replace('-', '').replace(' ', '')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.placa} - {self.marca} {self.modelo}'
    
    @property
    def esta_habilitado(self):
        """Verifica si el vehículo está habilitado."""
        return self.estado == EstadoVehiculo.HABILITADO
    
    @property
    def habilitacion_vigente(self):
        """Retorna la habilitación vehicular vigente si existe."""
        return self.habilitaciones.filter(
            estado=EstadoHabilitacion.VIGENTE
        ).first()

    @property
    def numero_tuc_vigente(self):
        """Retorna el número de TUC de la habilitación vigente."""
        hv = self.habilitacion_vigente
        return hv.numero_tuc if hv else None


class HabilitacionVehicular(AuditMixin):
    """
    Registro histórico de habilitaciones de vehículos.
    """
    
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name='habilitaciones',
        verbose_name='Vehículo'
    )
    
    autorizacion = models.ForeignKey(
        'autorizaciones.Autorizacion',
        on_delete=models.PROTECT,
        related_name='habilitaciones_vehiculares',
        verbose_name='Autorización'
    )
    
    numero_habilitacion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número de Habilitación'
    )
    
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fin'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoHabilitacion.CHOICES,
        default=EstadoHabilitacion.VIGENTE,
        verbose_name='Estado'
    )
    
    motivo = models.TextField(
        blank=True,
        verbose_name='Motivo',
        help_text='Motivo de la habilitación o cambio de estado'
    )
    
    # Campos TUC (Tarjeta Única de Circulación)
    numero_tuc = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Número TUC',
        help_text='Tarjeta Única de Circulación'
    )
    
    fecha_autorizacion_transportista = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Autorización Transportista',
        help_text='Fecha de inicio de autorización como transportista'
    )
    
    fecha_expiracion_transportista = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Expiración Transportista',
        help_text='Fecha de vencimiento de autorización como transportista'
    )
    
    fecha_expedicion_tuc = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Expedición TUC',
        help_text='Fecha en que se expidió la TUC'
    )
    
    tramite_origen = models.ForeignKey(
        'tramites.Tramite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='habilitaciones_vehiculares',
        verbose_name='Trámite de Origen'
    )
    
    class Meta:
        verbose_name = 'Habilitación Vehicular'
        verbose_name_plural = 'Habilitaciones Vehiculares'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f'{self.vehiculo.placa} - {self.autorizacion.numero_resolucion} ({self.estado})'
    
    @property
    def esta_vigente(self):
        """Verifica si la habilitación está vigente."""
        from django.utils import timezone
        hoy = timezone.now().date()
        if self.estado != EstadoHabilitacion.VIGENTE:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        return True
