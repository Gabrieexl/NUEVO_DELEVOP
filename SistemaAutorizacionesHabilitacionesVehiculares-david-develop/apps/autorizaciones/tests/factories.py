"""
Factories para tests de autorizaciones.
"""

import factory
from datetime import date, timedelta

from apps.autorizaciones.models import Autorizacion
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.usuarios.tests.factories import UsuarioFactory
from apps.configuracion.models import TipoServicio


class AutorizacionFactory(factory.django.DjangoModelFactory):
    """Factory para crear autorizaciones de prueba."""
    
    class Meta:
        model = Autorizacion
    
    empresa = factory.SubFactory(EmpresaTransporteFactory)
    numero_resolucion = factory.Sequence(lambda n: f'{n:03d}-2025-GR-MDD')
    fecha_resolucion = factory.LazyFunction(date.today)
    fecha_inicio_vigencia = factory.LazyFunction(date.today)
    fecha_fin_vigencia = factory.LazyFunction(
        lambda: date.today() + timedelta(days=365*5)  # 5 años
    )
    ambito = 'MADRE_DE_DIOS'  # Usar el valor correcto del choice
    tipo_servicio = factory.LazyAttribute(
        lambda o: TipoServicio.objects.get_or_create(
            codigo='REGULAR',
            defaults={'nombre': 'Regular', 'descripcion': 'Servicio regular'}
        )[0]
    )
    estado = 'VIGENTE'
    descripcion_rutas = factory.Faker('text', max_nb_chars=200, locale='es')
    frecuencias = 'Diario: 6:00, 10:00, 14:00, 18:00'
    creado_por = factory.SubFactory(UsuarioFactory)


class AutorizacionVencidaFactory(AutorizacionFactory):
    """Factory para crear autorizaciones vencidas."""
    estado = 'VENCIDA'
    fecha_inicio_vigencia = factory.LazyFunction(
        lambda: date.today() - timedelta(days=365*6)
    )
    fecha_fin_vigencia = factory.LazyFunction(
        lambda: date.today() - timedelta(days=1)
    )


class AutorizacionSuspendidaFactory(AutorizacionFactory):
    """Factory para crear autorizaciones suspendidas."""
    estado = 'SUSPENDIDA'


class AutorizacionCanceladaFactory(AutorizacionFactory):
    """Factory para crear autorizaciones canceladas."""
    estado = 'CANCELADA'
