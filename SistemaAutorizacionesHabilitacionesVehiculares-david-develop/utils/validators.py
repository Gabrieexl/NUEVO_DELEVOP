"""
Validadores personalizados para documentos peruanos.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from utils.constants import ANIO_MINIMO_FABRICACION_VEHICULO, ANIO_MINIMO_NACIMIENTO_CONDUCTOR



def validar_ruc(value):
    """
    Valida que el RUC tenga 11 dígitos y comience con 10, 15, 17 o 20.
    
    - 10: Persona natural con negocio
    - 15: Otros contribuyentes
    - 17: Sociedad conyugal
    - 20: Persona jurídica
    """
    if not re.match(r'^\d{11}$', value):
        raise ValidationError(
            _('El RUC debe tener exactamente 11 dígitos numéricos.'),
            code='ruc_invalido'
        )
    
    prefijos_validos = ('10', '15', '17', '20')
    if not value.startswith(prefijos_validos):
        raise ValidationError(
            _('El RUC debe comenzar con 10, 15, 17 o 20.'),
            code='ruc_prefijo_invalido'
        )


def validar_dni(value):
    """
    Valida que el DNI tenga exactamente 8 dígitos numéricos.
    """
    if not re.match(r'^\d{8}$', value):
        raise ValidationError(
            _('El DNI debe tener exactamente 8 dígitos numéricos.'),
            code='dni_invalido'
        )


def validar_placa_vehicular(value):
    """
    Valida el formato de placa vehicular peruana.
    
    Formatos válidos:
    - ABC-123 (placa antigua)
    - ABC-1234 (placa nueva, no implementada en Perú aún)
    - A1B-234 (placa de motos)
    """
    # Normalizar: quitar guiones y convertir a mayúsculas
    placa_limpia = value.upper().replace('-', '').replace(' ', '')
    
    # Patrón para placas peruanas (3 letras/números + 3-4 dígitos)
    patron = r'^[A-Z0-9]{3}\d{3,4}$'
    
    if not re.match(patron, placa_limpia):
        raise ValidationError(
            _('Formato de placa inválido. Use el formato ABC-123 o similar.'),
            code='placa_invalida'
        )


def validar_licencia_conducir(value):
    """
    Valida el formato de número de licencia de conducir.
    Generalmente es el DNI del conductor o un código específico.
    """
    # Puede ser DNI (8 dígitos) o formato especial (letra + números)
    if not re.match(r'^[A-Z]?\d{7,9}$', value.upper()):
        raise ValidationError(
            _('Formato de licencia de conducir inválido.'),
            code='licencia_invalida'
        )


def validar_telefono_peru(value):
    """
    Valida números de teléfono peruanos.
    
    Formatos válidos:
    - 9XXXXXXXX (celular, 9 dígitos empezando con 9)
    - 01XXXXXXX (fijo Lima, con código de área)
    - XXXXXXXX (fijo sin código, 7-8 dígitos)
    """
    # Limpiar espacios, guiones y paréntesis
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', value)
    
    # Patrón para celulares y fijos
    if not re.match(r'^(9\d{8}|0\d{8,9}|\d{7,8})$', telefono_limpio):
        raise ValidationError(
            _('Formato de teléfono inválido.'),
            code='telefono_invalido'
        )


def validar_solo_pdf(value):
    """
    Valida que el archivo sea un PDF.
    """
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError(
            _('Solo se permiten archivos PDF.'),
            code='tipo_archivo_invalido'
        )


class ValidarTamanioArchivo:
    """
    Validador de tamaño de archivo serializable para migraciones.
    
    Args:
        max_size_mb: Tamaño máximo en megabytes.
    """
    def __init__(self, max_size_mb=10):
        self.max_size_mb = max_size_mb
    
    def __call__(self, value):
        max_bytes = self.max_size_mb * 1024 * 1024
        if value.size > max_bytes:
            raise ValidationError(
                _('El archivo no debe superar los %(max_size)s MB.'),
                code='archivo_muy_grande',
                params={'max_size': self.max_size_mb}
            )
    
    def __eq__(self, other):
        return isinstance(other, ValidarTamanioArchivo) and self.max_size_mb == other.max_size_mb
    
    def deconstruct(self):
        return (
            'utils.validators.ValidarTamanioArchivo',
            [self.max_size_mb],
            {}
        )


# Alias para compatibilidad
def validar_tamanio_archivo(max_size_mb=10):
    """
    Retorna un validador que verifica el tamaño máximo del archivo.
    DEPRECATED: Usar ValidarTamanioArchivo directamente.
    """
    return ValidarTamanioArchivo(max_size_mb)

def validar_anio_nacimiento_conductor(value):
    """Valida que la fecha de nacimiento del conductor sea desde 1930 en adelante."""
    if value.year < ANIO_MINIMO_NACIMIENTO_CONDUCTOR:
        raise ValidationError(
            _('La fecha de nacimiento debe ser desde %(anio)s en adelante.'),
            code='fecha_nacimiento_invalida',
            params={'anio': ANIO_MINIMO_NACIMIENTO_CONDUCTOR}
        )


def validar_anio_fabricacion_vehiculo(value):
    """Valida que el año de fabricación del vehículo sea desde 1995 en adelante."""
    if value < ANIO_MINIMO_FABRICACION_VEHICULO:
        raise ValidationError(
            _('El año de fabricación debe ser %(anio)s o mayor.'),
            code='anio_fabricacion_invalido',
            params={'anio': ANIO_MINIMO_FABRICACION_VEHICULO}
        )