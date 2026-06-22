"""
Factories para tests de trámites.
"""

import factory
from datetime import date

from apps.tramites.models import Tramite, HistorialTramite
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.usuarios.tests.factories import UsuarioFactory, MesaPartesUsuarioFactory


class TramiteFactory(factory.django.DjangoModelFactory):
    """Factory para crear trámites de prueba."""
    
    class Meta:
        model = Tramite
    
    tipo_tramite = 'AUTORIZACION_INICIAL'
    estado = 'RECIBIDO'
    empresa = factory.SubFactory(EmpresaTransporteFactory)
    descripcion_solicitud = factory.Faker('text', max_nb_chars=300, locale='es')
    creado_por = factory.SubFactory(MesaPartesUsuarioFactory)


class TramiteAutorizacionInicialFactory(TramiteFactory):
    """Factory para trámites de autorización inicial."""
    tipo_tramite = 'AUTORIZACION_INICIAL'


class TramiteAutorizacionRutaFactory(TramiteFactory):
    """Factory para tramites de autorizacion de ruta."""
    tipo_tramite = 'AUTORIZACION_RUTA'


class TramiteIncrementoFlotaFactory(TramiteFactory):
    """Factory para trámites de incremento de flota."""
    tipo_tramite = 'INCREMENTO_FLOTA'
    autorizacion = factory.SubFactory(AutorizacionFactory)


class TramiteHabilitacionConductorFactory(TramiteFactory):
    """Factory para trámites de habilitación de conductor."""
    tipo_tramite = 'HABILITACION_CONDUCTOR'
    autorizacion = factory.SubFactory(AutorizacionFactory)


class TramiteSustitucionVehiculoFactory(TramiteFactory):
    """Factory para trámites de sustitución de vehículo."""
    tipo_tramite = 'SUSTITUCION_VEHICULO'
    autorizacion = factory.SubFactory(AutorizacionFactory)


class TramiteEnEvaluacionFactory(TramiteFactory):
    """Factory para trámites en evaluación técnica."""
    estado = 'EN_EVAL_TECNICA'


class TramiteAprobadoFactory(TramiteFactory):
    """Factory para trámites aprobados."""
    estado = 'APROBADO'


class HistorialTramiteFactory(factory.django.DjangoModelFactory):
    """Factory para crear historial de trámites."""
    
    class Meta:
        model = HistorialTramite
    
    tramite = factory.SubFactory(TramiteFactory)
    estado_anterior = 'RECIBIDO'
    estado_nuevo = 'EN_EVAL_TECNICA'
    usuario = factory.SubFactory(UsuarioFactory)
    comentario = 'Trámite derivado a evaluación técnica'
