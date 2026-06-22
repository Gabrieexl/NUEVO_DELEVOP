"""
Modelos de empresas de transporte.
"""

from django.db import models
from django.conf import settings

from utils.mixins import AuditMixin
from utils.constants import EstadoEmpresa
from utils.validators import validar_ruc, validar_dni


class EmpresaTransporte(AuditMixin):
    """
    Modelo para empresas de transporte terrestre.
    """
    
    ruc = models.CharField(
        max_length=11,
        unique=True,
        validators=[validar_ruc],
        verbose_name='RUC',
        help_text='Registro Único de Contribuyentes (11 dígitos)'
    )
    
    razon_social = models.CharField(
        max_length=255,
        verbose_name='Razón Social'
    )
    
    nombre_comercial = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre Comercial'
    )
    
    domicilio_fiscal = models.TextField(
        verbose_name='Domicilio Fiscal'
    )
    
    departamento = models.CharField(
        max_length=50,
        default='Madre de Dios',
        verbose_name='Departamento'
    )
    
    provincia = models.CharField(
        max_length=50,
        verbose_name='Provincia'
    )
    
    distrito = models.CharField(
        max_length=50,
        verbose_name='Distrito'
    )
    
    representante_legal = models.CharField(
        max_length=255,
        verbose_name='Representante Legal'
    )
    
    dni_representante = models.CharField(
        max_length=8,
        validators=[validar_dni],
        verbose_name='DNI del Representante'
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
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoEmpresa.CHOICES,
        default=EstadoEmpresa.ACTIVA,
        verbose_name='Estado'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = 'Empresa de Transporte'
        verbose_name_plural = 'Empresas de Transporte'
        ordering = ['razon_social']
    
    def __str__(self):
        return f'{self.razon_social} ({self.ruc})'
    
    @property
    def nombre_corto(self):
        """Retorna el nombre comercial o la razón social."""
        return self.nombre_comercial or self.razon_social
    
    @property
    def esta_activa(self):
        """Verifica si la empresa está activa."""
        return self.estado == EstadoEmpresa.ACTIVA
