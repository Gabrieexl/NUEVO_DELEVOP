"""
Factories para tests de empresas.
"""

import factory
from django.contrib.auth import get_user_model

from apps.empresas.models import EmpresaTransporte
from apps.usuarios.tests.factories import UsuarioFactory


class EmpresaTransporteFactory(factory.django.DjangoModelFactory):
    """Factory para crear empresas de transporte de prueba."""
    
    class Meta:
        model = EmpresaTransporte
    
    ruc = factory.Sequence(lambda n: f'2010000000{n % 10}')
    razon_social = factory.Faker('company', locale='es')
    nombre_comercial = factory.Faker('company_suffix', locale='es')
    domicilio_fiscal = factory.Faker('address', locale='es')
    representante_legal = factory.Faker('name', locale='es')
    dni_representante = factory.Sequence(lambda n: f'{40000000 + n}')
    telefono = factory.Faker('phone_number', locale='es')
    email = factory.LazyAttribute(lambda obj: f'contacto{obj.ruc}@empresa.com')
    estado = 'ACTIVA'
    creado_por = factory.SubFactory(UsuarioFactory)


class EmpresaTransporteInactivaFactory(EmpresaTransporteFactory):
    """Factory para crear empresas inactivas."""
    estado = 'INACTIVA'
