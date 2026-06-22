"""
Factories para tests de vehículos.
"""

import factory
from datetime import date, timedelta

from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.usuarios.tests.factories import UsuarioFactory
from apps.configuracion.models import Carroceria, CategoriaVehiculo


class VehiculoFactory(factory.django.DjangoModelFactory):
    """Factory para crear vehículos de prueba."""
    
    class Meta:
        model = Vehiculo
    
    placa = factory.Sequence(lambda n: f'ABC-{n:03d}')
    empresa_propietaria = factory.SubFactory(EmpresaTransporteFactory)
    marca = factory.Faker('random_element', elements=['Toyota', 'Hyundai', 'Kia', 'Mercedes'])
    modelo = factory.Faker('random_element', elements=['Hiace', 'H1', 'Carnival', 'Sprinter'])
    anio_fabricacion = factory.Faker('random_int', min=2015, max=2024)
    capacidad_sentados = factory.Faker('random_int', min=8, max=16)
    carroceria = factory.LazyAttribute(
        lambda o: Carroceria.objects.get_or_create(
            codigo='MINIVAN',
            defaults={
                'nombre': 'Minivan', 
                'descripcion': 'Vehículo tipo minivan',
                'categoria': CategoriaVehiculo.objects.get_or_create(
                    codigo='M2',
                    defaults={'nombre': 'Categoría M2'}
                )[0]
            }
        )[0]
    )
    estado = 'PROPUESTO'
    numero_tiv = factory.Sequence(lambda n: f'TIV-{n:06d}')
    fecha_venc_soat = factory.LazyFunction(
        lambda: date.today() + timedelta(days=365)
    )
    fecha_venc_citv = factory.LazyFunction(
        lambda: date.today() + timedelta(days=180)
    )
    creado_por = factory.SubFactory(UsuarioFactory)


class VehiculoHabilitadoFactory(VehiculoFactory):
    """Factory para crear vehículos habilitados."""
    estado = 'HABILITADO'


class VehiculoBajaFactory(VehiculoFactory):
    """Factory para crear vehículos dados de baja."""
    estado = 'BAJA'


class HabilitacionVehicularFactory(factory.django.DjangoModelFactory):
    """Factory para crear habilitaciones vehiculares."""
    
    class Meta:
        model = HabilitacionVehicular
    
    vehiculo = factory.SubFactory(VehiculoHabilitadoFactory)
    autorizacion = factory.SubFactory(AutorizacionFactory)
    fecha_inicio = factory.LazyFunction(date.today)
    fecha_fin = None
    estado = 'VIGENTE'
    motivo = 'Habilitación inicial'
    creado_por = factory.SubFactory(UsuarioFactory)


class HabilitacionVehicularBajaFactory(HabilitacionVehicularFactory):
    """Factory para crear habilitaciones dadas de baja."""
    estado = 'BAJA'
    fecha_fin = factory.LazyFunction(date.today)
    motivo = 'Baja por solicitud'
