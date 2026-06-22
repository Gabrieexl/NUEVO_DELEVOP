"""
Factories para tests de conductores.
"""

import factory
from datetime import date, timedelta

from apps.conductores.models import Conductor, HabilitacionConductor
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.usuarios.tests.factories import UsuarioFactory


class ConductorFactory(factory.django.DjangoModelFactory):
    """Factory para crear conductores de prueba."""
    
    class Meta:
        model = Conductor
    
    empresa = factory.SubFactory(EmpresaTransporteFactory)
    dni = factory.Sequence(lambda n: f'{50000000 + n}')
    nombres = factory.Faker('first_name', locale='es')
    apellido_paterno = factory.Faker('last_name', locale='es')
    apellido_materno = factory.Faker('last_name', locale='es')
    fecha_nacimiento = factory.Faker('date_of_birth', minimum_age=25, maximum_age=60)
    licencia_numero = factory.Sequence(lambda n: f'Q{n:08d}')
    licencia_categoria = 'AIIB'
    licencia_fecha_emision = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365)
    )
    licencia_fecha_vencimiento = factory.LazyFunction(
        lambda: date.today() + timedelta(days=365*4)
    )
    estado = 'ACTIVO'
    creado_por = factory.SubFactory(UsuarioFactory)


class ConductorInactivoFactory(ConductorFactory):
    """Factory para crear conductores inactivos."""
    estado = 'INACTIVO'


class ConductorLicenciaVencidaFactory(ConductorFactory):
    """Factory para crear conductores con licencia vencida."""
    licencia_fecha_emision = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365*6)
    )
    licencia_fecha_vencimiento = factory.LazyFunction(
        lambda: date.today() - timedelta(days=1)
    )


class HabilitacionConductorFactory(factory.django.DjangoModelFactory):
    """Factory para crear habilitaciones de conductores."""
    
    class Meta:
        model = HabilitacionConductor
    
    conductor = factory.SubFactory(ConductorFactory)
    empresa = factory.SubFactory(EmpresaTransporteFactory)
    autorizacion = factory.SubFactory(AutorizacionFactory)
    fecha_inicio = factory.LazyFunction(date.today)
    fecha_fin = None
    estado = 'VIGENTE'
    motivo = 'Habilitación inicial'
    creado_por = factory.SubFactory(UsuarioFactory)


class HabilitacionConductorBajaFactory(HabilitacionConductorFactory):
    """Factory para crear habilitaciones dadas de baja."""
    estado = 'BAJA'
    fecha_fin = factory.LazyFunction(date.today)
    motivo = 'Baja por solicitud'
