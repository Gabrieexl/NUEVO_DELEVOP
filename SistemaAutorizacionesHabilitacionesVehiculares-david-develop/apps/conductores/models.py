"""
Modelos de conductores y habilitaciones de conductores.
"""

from django.db import models
from django.conf import settings

from utils.mixins import AuditMixin
from utils.constants import EstadoConductor, CategoriaLicencia, EstadoHabilitacion
from utils.validators import validar_dni
from utils.validators import validar_dni, validar_anio_nacimiento_conductor


class Conductor(AuditMixin):
    """
    Modelo para conductores de transporte.
    """
    
    empresa = models.ForeignKey(
        'empresas.EmpresaTransporte',
        on_delete=models.PROTECT,
        related_name='conductores',
        verbose_name='Empresa',
        help_text='Empresa de transporte a la que pertenece el conductor'
    )
    
    dni = models.CharField(
        max_length=8,
        unique=True,
        validators=[validar_dni],
        verbose_name='DNI'
    )
    
    nombres = models.CharField(
        max_length=100,
        verbose_name='Nombres'
    )
    
    apellido_paterno = models.CharField(
        max_length=50,
        verbose_name='Apellido Paterno'
    )
    
    apellido_materno = models.CharField(
        max_length=50,
        verbose_name='Apellido Materno'
    )
    
    fecha_nacimiento = models.DateField(
    validators=[validar_anio_nacimiento_conductor],
    verbose_name='Fecha de Nacimiento'
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
        upload_to='resoluciones/conductores/',
        null=True,
        blank=True,
        verbose_name='Archivo de Resolución'
    )
    
    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name='Correo Electrónico'
    )
    
    # Datos de licencia de conducir
    licencia_numero = models.CharField(
        max_length=20,
        verbose_name='Número de Licencia'
    )
    
    licencia_categoria = models.CharField(
        max_length=10,
        choices=CategoriaLicencia.CHOICES,
        verbose_name='Categoría de Licencia'
    )
    
    licencia_fecha_emision = models.DateField(
        verbose_name='Fecha de Emisión de Licencia'
    )
    
    licencia_fecha_vencimiento = models.DateField(
        verbose_name='Fecha de Vencimiento de Licencia'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoConductor.CHOICES,
        default=EstadoConductor.ACTIVO,
        verbose_name='Estado'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Conductor'
        verbose_name_plural = 'Conductores'
        ordering = ['apellido_paterno', 'apellido_materno', 'nombres']
    
    def __str__(self):
        return f'{self.nombre_completo} ({self.dni})'
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del conductor."""
        return f'{self.nombres} {self.apellido_paterno} {self.apellido_materno}'
    
    @property
    def esta_activo(self):
        """Verifica si el conductor está activo."""
        return self.estado == EstadoConductor.ACTIVO
    
    @property
    def licencia_vigente(self):
        """Verifica si la licencia está vigente."""
        from django.utils import timezone
        hoy = timezone.now().date()
        return hoy <= self.licencia_fecha_vencimiento
    
    @property
    def licencia_vencida(self):
        """Verifica si la licencia está vencida."""
        return not self.licencia_vigente
    
    @property
    def edad(self):
        """Calcula la edad del conductor."""
        from django.utils import timezone
        hoy = timezone.now().date()
        return (
            hoy.year - self.fecha_nacimiento.year - 
            ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        )
    
    def tiene_habilitacion_vigente_otra_empresa(self, empresa_id):
        """
        Verifica si el conductor tiene una habilitación vigente en otra empresa.
        Retorna True si tiene habilitación vigente en una empresa diferente.
        """
        from utils.constants import EstadoHabilitacion
        return self.habilitaciones.filter(
            estado=EstadoHabilitacion.VIGENTE
        ).exclude(empresa_id=empresa_id).exists()
    
    @property
    def habilitacion_vigente(self):
        """Retorna la habilitación vigente del conductor si existe."""
        from utils.constants import EstadoHabilitacion
        return self.habilitaciones.filter(
            estado=EstadoHabilitacion.VIGENTE
        ).first()
    
    @property
    def empresa_habilitacion_vigente(self):
        """Retorna la empresa de la habilitación vigente si existe."""
        hab = self.habilitacion_vigente
        return hab.empresa if hab else None


class HabilitacionConductor(AuditMixin):
    """
    Registro histórico de habilitaciones de conductores.
    """
    
    conductor = models.ForeignKey(
        Conductor,
        on_delete=models.PROTECT,
        related_name='habilitaciones',
        verbose_name='Conductor'
    )
    
    empresa = models.ForeignKey(
        'empresas.EmpresaTransporte',
        on_delete=models.PROTECT,
        related_name='habilitaciones_conductores',
        verbose_name='Empresa'
    )
    
    autorizacion = models.ForeignKey(
        'autorizaciones.Autorizacion',
        on_delete=models.PROTECT,
        related_name='habilitaciones_conductores',
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
    
    tramite_origen = models.ForeignKey(
        'tramites.Tramite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='habilitaciones_conductores',
        verbose_name='Trámite de Origen'
    )
    
    class Meta:
        verbose_name = 'Habilitación de Conductor'
        verbose_name_plural = 'Habilitaciones de Conductores'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f'{self.conductor.nombre_completo} - {self.empresa.nombre_corto} ({self.estado})'
    
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
