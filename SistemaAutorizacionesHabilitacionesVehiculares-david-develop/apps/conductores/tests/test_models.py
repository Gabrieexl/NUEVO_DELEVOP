"""
Tests del modelo Conductor y HabilitacionConductor.
"""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from apps.conductores.models import Conductor, HabilitacionConductor
from .factories import (
    ConductorFactory,
    ConductorInactivoFactory,
    ConductorLicenciaVencidaFactory,
    HabilitacionConductorFactory,
    HabilitacionConductorBajaFactory,
)


@pytest.mark.django_db
class TestConductorModel:
    """Tests para el modelo Conductor."""
    
    def test_crear_conductor(self):
        """Test: Crear un conductor básico."""
        conductor = ConductorFactory()
        assert conductor.pk is not None
        assert conductor.dni is not None
        assert len(conductor.dni) == 8
    
    def test_conductor_str(self):
        """Test: Representación string del conductor."""
        conductor = ConductorFactory(
            nombres='Juan Carlos',
            apellido_paterno='Pérez',
            apellido_materno='García'
        )
        string = str(conductor)
        assert 'Juan Carlos' in string or 'Pérez' in string
    
    def test_dni_unique(self):
        """Test: DNI debe ser único."""
        ConductorFactory(dni='12345678')
        with pytest.raises(Exception):
            ConductorFactory(dni='12345678')
    
    def test_nombre_completo(self):
        """Test: Propiedad nombre_completo funciona."""
        conductor = ConductorFactory(
            nombres='María',
            apellido_paterno='López',
            apellido_materno='Fernández'
        )
        nombre = conductor.nombre_completo
        assert 'María' in nombre
        assert 'López' in nombre
    
    def test_estado_activo_por_defecto(self):
        """Test: Estado por defecto es ACTIVO."""
        conductor = ConductorFactory()
        assert conductor.estado == 'ACTIVO'
    
    def test_conductor_inactivo(self):
        """Test: Crear conductor inactivo."""
        conductor = ConductorInactivoFactory()
        assert conductor.estado == 'INACTIVO'
    
    def test_timestamps_automaticos(self):
        """Test: Timestamps se crean automáticamente."""
        conductor = ConductorFactory()
        assert conductor.fecha_creacion is not None
        assert conductor.fecha_actualizacion is not None
    
    def test_licencia_categoria_valida(self):
        """Test: Categoría de licencia válida."""
        conductor = ConductorFactory(licencia_categoria='AIIIB')
        assert conductor.licencia_categoria == 'AIIIB'
    
    def test_licencia_vencida_property(self):
        """Test: Propiedad licencia_vencida funciona."""
        conductor = ConductorLicenciaVencidaFactory()
        assert conductor.licencia_fecha_vencimiento < date.today()


@pytest.mark.django_db
class TestHabilitacionConductorModel:
    """Tests para el modelo HabilitacionConductor."""
    
    def test_crear_habilitacion(self):
        """Test: Crear una habilitación de conductor."""
        habilitacion = HabilitacionConductorFactory()
        assert habilitacion.pk is not None
        assert habilitacion.conductor is not None
        assert habilitacion.empresa is not None
        assert habilitacion.autorizacion is not None
    
    def test_habilitacion_str(self):
        """Test: Representación string de la habilitación."""
        habilitacion = HabilitacionConductorFactory()
        string = str(habilitacion)
        # Verificar que tiene una representación string válida
        assert len(string) > 0
        assert 'VIGENTE' in string or habilitacion.conductor.nombres in string
    
    def test_estado_vigente_por_defecto(self):
        """Test: Estado por defecto es VIGENTE."""
        habilitacion = HabilitacionConductorFactory()
        assert habilitacion.estado == 'VIGENTE'
    
    def test_habilitacion_baja(self):
        """Test: Crear habilitación en baja."""
        habilitacion = HabilitacionConductorBajaFactory()
        assert habilitacion.estado == 'BAJA'
        assert habilitacion.fecha_fin is not None
    
    def test_relacionamiento_correcto(self):
        """Test: Habilitación relaciona conductor con empresa y autorización."""
        habilitacion = HabilitacionConductorFactory()
        assert habilitacion.conductor.estado == 'ACTIVO'
        assert habilitacion.empresa.estado == 'ACTIVA'
        assert habilitacion.autorizacion.estado == 'VIGENTE'


@pytest.mark.django_db
class TestConductorQueryset:
    """Tests para el queryset de conductores."""
    
    def test_filtrar_activos(self):
        """Test: Filtrar conductores activos."""
        ConductorFactory.create_batch(3)
        ConductorInactivoFactory.create_batch(2)
        
        activos = Conductor.objects.filter(estado='ACTIVO')
        assert activos.count() == 3
    
    def test_filtrar_inactivos(self):
        """Test: Filtrar conductores inactivos."""
        ConductorFactory.create_batch(3)
        ConductorInactivoFactory.create_batch(2)
        
        inactivos = Conductor.objects.filter(estado='INACTIVO')
        assert inactivos.count() == 2
    
    def test_filtrar_por_categoria(self):
        """Test: Filtrar conductores por categoría de licencia."""
        ConductorFactory.create_batch(3, licencia_categoria='AII')
        ConductorFactory.create_batch(2, licencia_categoria='AIII')
        
        cat_aii = Conductor.objects.filter(licencia_categoria='AII')
        assert cat_aii.count() == 3
