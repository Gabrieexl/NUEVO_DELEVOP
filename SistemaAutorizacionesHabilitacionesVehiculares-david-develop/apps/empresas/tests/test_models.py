"""
Tests del modelo EmpresaTransporte.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.empresas.models import EmpresaTransporte
from .factories import EmpresaTransporteFactory, EmpresaTransporteInactivaFactory


@pytest.mark.django_db
class TestEmpresaTransporteModel:
    """Tests para el modelo EmpresaTransporte."""
    
    def test_crear_empresa(self):
        """Test: Crear una empresa básica."""
        empresa = EmpresaTransporteFactory()
        assert empresa.pk is not None
        assert len(empresa.ruc) == 11
    
    def test_empresa_str(self):
        """Test: Representación string de la empresa."""
        empresa = EmpresaTransporteFactory(
            razon_social='Transportes DRTC S.A.C.',
            ruc='20123456789'
        )
        assert 'Transportes DRTC S.A.C.' in str(empresa)
    
    def test_ruc_unique(self):
        """Test: RUC debe ser único."""
        empresa1 = EmpresaTransporteFactory(ruc='20123456789')
        with pytest.raises(Exception):  # IntegrityError
            EmpresaTransporteFactory(ruc='20123456789')
    
    def test_ruc_valido(self):
        """Test: RUC debe tener 11 dígitos."""
        with pytest.raises(ValidationError):
            empresa = EmpresaTransporte(
                ruc='123',  # RUC inválido
                razon_social='Test',
                domicilio_fiscal='Test',
                representante_legal='Test',
                dni_representante='12345678',
            )
            empresa.full_clean()
    
    def test_empresa_activa_por_defecto(self):
        """Test: Estado por defecto es ACTIVA."""
        empresa = EmpresaTransporteFactory()
        assert empresa.estado == 'ACTIVA'
    
    def test_empresa_inactiva(self):
        """Test: Crear empresa inactiva."""
        empresa = EmpresaTransporteInactivaFactory()
        assert empresa.estado == 'INACTIVA'
    
    def test_timestamps_automaticos(self):
        """Test: Timestamps se crean automáticamente."""
        empresa = EmpresaTransporteFactory()
        assert empresa.fecha_creacion is not None
        assert empresa.fecha_actualizacion is not None
    
    def test_dni_representante_valido(self):
        """Test: DNI representante debe tener 8 dígitos."""
        with pytest.raises(ValidationError):
            empresa = EmpresaTransporte(
                ruc='20123456789',
                razon_social='Test',
                domicilio_fiscal='Test',
                representante_legal='Test',
                dni_representante='123',  # DNI inválido
            )
            empresa.full_clean()


@pytest.mark.django_db
class TestEmpresaTransporteQueryset:
    """Tests para el queryset de empresas."""
    
    def test_filtrar_activas(self):
        """Test: Filtrar empresas activas."""
        EmpresaTransporteFactory.create_batch(3)
        EmpresaTransporteInactivaFactory.create_batch(2)
        
        activas = EmpresaTransporte.objects.filter(estado='ACTIVA')
        assert activas.count() == 3
    
    def test_filtrar_inactivas(self):
        """Test: Filtrar empresas inactivas."""
        EmpresaTransporteFactory.create_batch(3)
        EmpresaTransporteInactivaFactory.create_batch(2)
        
        inactivas = EmpresaTransporte.objects.filter(estado='INACTIVA')
        assert inactivas.count() == 2
