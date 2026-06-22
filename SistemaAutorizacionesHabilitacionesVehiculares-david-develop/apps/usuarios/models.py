"""
Modelos de usuarios del sistema DRTC.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.constants import Roles
from utils.validators import validar_dni


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado para el sistema DRTC.
    Extiende AbstractUser agregando campos específicos del sistema.
    """
    
    dni = models.CharField(
        max_length=8,
        unique=True,
        validators=[validar_dni],
        verbose_name='DNI',
        help_text='Documento Nacional de Identidad (8 dígitos)'
    )
    
    rol = models.CharField(
        max_length=30,
        choices=Roles.CHOICES,
        default=Roles.CONSULTA_INTERNA,
        verbose_name='Rol',
        help_text='Rol del usuario en el sistema'
    )
    
    telefono = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='Teléfono'
    )
    
    area = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Área/Oficina',
        help_text='Área o oficina donde trabaja el usuario'
    )
    
    cargo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cargo',
        help_text='Cargo o puesto del usuario'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']
    
    def __str__(self):
        return f'{self.get_full_name()} ({self.dni})'
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username
    
    @property
    def es_admin(self):
        """Verifica si el usuario es administrador."""
        return self.rol == Roles.ADMIN_SISTEMA or self.is_superuser
    
    @property
    def es_mesa_partes(self):
        """Verifica si el usuario es de Mesa de Partes."""
        return self.rol == Roles.MESA_PARTES
    
    @property
    def es_especialista(self):
        """Verifica si el usuario es Especialista Técnico."""
        return self.rol == Roles.ESPECIALISTA_TECNICO
    
    @property
    def es_legal(self):
        """Verifica si el usuario es de Asesoría Legal."""
        return self.rol == Roles.ASESORIA_LEGAL
    
    @property
    def es_director(self):
        """Verifica si el usuario es Director (General o Administrativo)."""
        return self.rol in [Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO]
    
    @property
    def es_consulta_interna(self):
        """Verifica si el usuario es de Consulta Interna."""
        return self.rol == Roles.CONSULTA_INTERNA
    
    @property
    def es_consulta_inspector(self):
        """Verifica si el usuario es de Consulta Inspector."""
        return self.rol == Roles.CONSULTA_INSPECTOR
    
    @property
    def es_control_calidad(self):
        """Verifica si el usuario es de Control de Calidad."""
        return self.rol == Roles.CONTROL_CALIDAD
    
    @property
    def puede_crear_tramites(self):
        """Verifica si el usuario puede crear trámites."""
        return self.is_superuser or self.rol in [Roles.ADMIN_SISTEMA, Roles.MESA_PARTES]
    
    @property
    def puede_evaluar_tecnicamente(self):
        """Verifica si el usuario puede realizar evaluación técnica."""
        return self.is_superuser or self.rol in [Roles.ADMIN_SISTEMA, Roles.ESPECIALISTA_TECNICO]
    
    @property
    def puede_evaluar_legalmente(self):
        """Verifica si el usuario puede realizar evaluación legal."""
        return self.is_superuser or self.rol in [Roles.ADMIN_SISTEMA, Roles.ASESORIA_LEGAL]
    
    @property
    def puede_firmar(self):
        """Verifica si el usuario puede firmar/aprobar trámites."""
        return self.is_superuser or self.rol in [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO]
    
    @property
    def solo_lectura(self):
        """Verifica si el usuario tiene solo acceso de lectura."""
        return self.rol in [Roles.CONSULTA_INTERNA, Roles.CONSULTA_INSPECTOR]
