"""
Tests del modelo Vehiculo y HabilitacionVehicular.
"""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.configuracion.models import Carroceria
from .factories import (
    VehiculoFactory,
    VehiculoHabilitadoFactory,
    VehiculoBajaFactory,
    HabilitacionVehicularFactory,
    HabilitacionVehicularBajaFactory,
)


@pytest.mark.django_db
class TestVehiculoModel:
    """Tests para el modelo Vehiculo."""
    
    def test_crear_vehiculo(self):
        """Test: Crear un vehículo básico."""
        vehiculo = VehiculoFactory()
        assert vehiculo.pk is not None
        assert vehiculo.placa is not None
    
    def test_vehiculo_str(self):
        """Test: Representación string del vehículo."""
        vehiculo = VehiculoFactory(placa='XYZ-123')
        assert 'XYZ123' in str(vehiculo)
    
    def test_placa_unique(self):
        """Test: Placa debe ser única."""
        VehiculoFactory(placa='ABC-001')
        with pytest.raises(Exception):
            VehiculoFactory(placa='ABC-001')
    
    def test_placa_formato(self):
        """Test: Placa se guarda correctamente."""
        vehiculo = VehiculoFactory(placa='ABC-123')
        vehiculo.refresh_from_db()
        assert vehiculo.placa is not None
        assert len(vehiculo.placa) > 0
    
    def test_estado_propuesto_por_defecto(self):
        """Test: Estado por defecto es PROPUESTO."""
        vehiculo = VehiculoFactory()
        assert vehiculo.estado == 'PROPUESTO'
    
    def test_vehiculo_habilitado(self):
        """Test: Crear vehículo habilitado."""
        vehiculo = VehiculoHabilitadoFactory()
        assert vehiculo.estado == 'HABILITADO'
    
    def test_vehiculo_baja(self):
        """Test: Crear vehículo en baja."""
        vehiculo = VehiculoBajaFactory()
        assert vehiculo.estado == 'BAJA'
    
    def test_timestamps_automaticos(self):
        """Test: Timestamps se crean automáticamente."""
        vehiculo = VehiculoFactory()
        assert vehiculo.fecha_creacion is not None
        assert vehiculo.fecha_actualizacion is not None
    
    def test_relacion_empresa(self):
        """Test: Relación con empresa funciona."""
        vehiculo = VehiculoFactory()
        assert vehiculo.empresa_propietaria is not None
    
    def test_anio_fabricacion_valido(self):
        """Test: Año de fabricación debe ser válido."""
        vehiculo = VehiculoFactory(anio_fabricacion=2020)
        assert vehiculo.anio_fabricacion == 2020


@pytest.mark.django_db
class TestHabilitacionVehicularModel:
    """Tests para el modelo HabilitacionVehicular."""
    
    def test_crear_habilitacion(self):
        """Test: Crear una habilitación vehicular."""
        habilitacion = HabilitacionVehicularFactory()
        assert habilitacion.pk is not None
        assert habilitacion.vehiculo is not None
        assert habilitacion.autorizacion is not None
    
    def test_habilitacion_str(self):
        """Test: Representación string de la habilitación."""
        habilitacion = HabilitacionVehicularFactory()
        string = str(habilitacion)
        assert habilitacion.vehiculo.placa in string
    
    def test_estado_vigente_por_defecto(self):
        """Test: Estado por defecto es VIGENTE."""
        habilitacion = HabilitacionVehicularFactory()
        assert habilitacion.estado == 'VIGENTE'
    
    def test_habilitacion_baja(self):
        """Test: Crear habilitación en baja."""
        habilitacion = HabilitacionVehicularBajaFactory()
        assert habilitacion.estado == 'BAJA'
        assert habilitacion.fecha_fin is not None
    
    def test_relacionamiento_correcto(self):
        """Test: Habilitación relaciona vehículo con autorización."""
        habilitacion = HabilitacionVehicularFactory()
        assert habilitacion.vehiculo.estado == 'HABILITADO'
        assert habilitacion.autorizacion.estado == 'VIGENTE'


@pytest.mark.django_db
class TestVehiculoQueryset:
    """Tests para el queryset de vehículos."""
    
    def test_filtrar_habilitados(self):
        """Test: Filtrar vehículos habilitados."""
        VehiculoHabilitadoFactory.create_batch(3)
        VehiculoFactory.create_batch(2)
        
        habilitados = Vehiculo.objects.filter(estado='HABILITADO')
        assert habilitados.count() == 3
    
    def test_filtrar_por_empresa(self):
        """Test: Filtrar vehículos por empresa."""
        vehiculo = VehiculoFactory()
        VehiculoFactory.create_batch(2)
        
        result = Vehiculo.objects.filter(empresa_propietaria=vehiculo.empresa_propietaria)
        assert result.count() == 1
    
    def test_filtrar_por_tipo(self):
        """Test: Filtrar vehículos por tipo."""
        from apps.configuracion.models import CategoriaVehiculo
        cat_m2, _ = CategoriaVehiculo.objects.get_or_create(codigo="M2", defaults={"nombre": "Categoría M2"})
        cat_m3, _ = CategoriaVehiculo.objects.get_or_create(codigo="M3", defaults={"nombre": "Categoría M3"})
        
        tipo_minivan, _ = Carroceria.objects.get_or_create(
            codigo='MINIVAN',
            defaults={'nombre': 'Minivan', 'descripcion': 'Vehículo tipo minivan', 'categoria': cat_m2}
        )
        tipo_bus, _ = Carroceria.objects.get_or_create(
            codigo='BUS',
            defaults={'nombre': 'Bus', 'descripcion': 'Vehículo tipo bus', 'categoria': cat_m3}
        )
        VehiculoFactory.create_batch(3, carroceria=tipo_minivan)
        VehiculoFactory.create_batch(2, carroceria=tipo_bus)
        
        minivans = Vehiculo.objects.filter(carroceria=tipo_minivan)
        assert minivans.count() == 3

def test_placa_unique_si_no_esta_baja(self):
    """Test: Placa debe ser única mientras exista un vehículo no dado de baja."""
    VehiculoFactory(placa='ABC-001', estado='HABILITADO')
    with pytest.raises(Exception):
        VehiculoFactory(placa='ABC-001', estado='PROPUESTO')

def test_placa_puede_reutilizarse_si_vehiculo_esta_baja(self):
    """Test: Placa puede reutilizarse si el registro anterior está en BAJA."""
    VehiculoFactory(placa='ABC-001', estado='BAJA')
    nuevo_vehiculo = VehiculoFactory(placa='ABC-001', estado='PROPUESTO')

    assert nuevo_vehiculo.pk is not None
    assert Vehiculo.objects.filter(placa='ABC001').count() == 2