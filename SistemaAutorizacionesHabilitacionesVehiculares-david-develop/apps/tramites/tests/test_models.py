"""
Tests del modelo Tramite y transiciones FSM.
"""

import pytest
from datetime import date
from django.core.exceptions import ValidationError
from django_fsm import TransitionNotAllowed

from apps.tramites.models import Tramite, HistorialTramite
from apps.usuarios.tests.factories import (
    UsuarioFactory,
    MesaPartesUsuarioFactory,
    EspecialistaUsuarioFactory,
    LegalUsuarioFactory,
    DirectorUsuarioFactory,
)
from utils.constants import EstadoTramite, Roles, TipoTramite
from .factories import (
    TramiteFactory,
    TramiteAutorizacionInicialFactory,
    TramiteAutorizacionRutaFactory,
    TramiteIncrementoFlotaFactory,
    TramiteEnEvaluacionFactory,
    TramiteAprobadoFactory,
    HistorialTramiteFactory,
)


@pytest.mark.django_db
class TestTramiteModel:
    """Tests para el modelo Tramite."""
    
    def test_crear_tramite(self):
        """Test: Crear un trámite básico."""
        tramite = TramiteFactory()
        assert tramite.pk is not None
        assert tramite.numero_expediente is not None
    
    def test_numero_expediente_formato(self):
        """Test: Número de expediente tiene formato correcto."""
        tramite = TramiteFactory()
        # Formato esperado: EXP-{AÑO}-{SECUENCIAL:05d}
        assert tramite.numero_expediente.startswith('EXP-')
        assert str(date.today().year) in tramite.numero_expediente
    
    def test_numero_expediente_unique(self):
        """Test: Número de expediente es único."""
        tramite1 = TramiteFactory()
        tramite2 = TramiteFactory()
        assert tramite1.numero_expediente != tramite2.numero_expediente
    
    def test_tramite_str(self):
        """Test: Representación string del trámite."""
        tramite = TramiteFactory()
        string = str(tramite)
        assert tramite.numero_expediente in string
    
    def test_estado_recibido_por_defecto(self):
        """Test: Estado por defecto es RECIBIDO."""
        tramite = TramiteFactory()
        assert tramite.estado == 'RECIBIDO'
    
    def test_timestamps_automaticos(self):
        """Test: Timestamps se crean automáticamente."""
        tramite = TramiteFactory()
        assert tramite.fecha_creacion is not None
        assert tramite.fecha_actualizacion is not None


@pytest.mark.django_db
class TestTramiteTipos:
    """Tests para los diferentes tipos de trámite."""
    
    def test_tramite_autorizacion_inicial(self):
        """Test: Trámite de autorización inicial."""
        tramite = TramiteAutorizacionInicialFactory()
        assert tramite.tipo_tramite == 'AUTORIZACION_INICIAL'
    
    def test_tramite_incremento_flota(self):
        """Test: Trámite de incremento de flota."""
        tramite = TramiteIncrementoFlotaFactory()
        assert tramite.tipo_tramite == 'INCREMENTO_FLOTA'
        assert tramite.autorizacion is not None
    
    def test_tramite_en_evaluacion(self):
        """Test: Trámite en evaluación técnica."""
        tramite = TramiteEnEvaluacionFactory(tipo_tramite=TipoTramite.SUSTITUCION_VEHICULO)
        assert tramite.estado == 'EN_EVAL_TECNICA'


@pytest.mark.django_db
class TestTramiteFSMTransiciones:
    """Tests para las transiciones FSM del trámite."""
    
    def test_transicion_recibido_a_evaluacion(self):
        """Test: Transición de RECIBIDO a EN_EVAL_TECNICA."""
        tramite = TramiteFactory()
        usuario = EspecialistaUsuarioFactory()
        
        # Verificar estado inicial
        assert tramite.estado == 'RECIBIDO'
        
        # Realizar transición
        tramite.enviar_a_evaluacion_tecnica(usuario=usuario)
        tramite.save()
        
        assert tramite.estado == 'EN_EVAL_TECNICA'
    
    def test_transicion_evaluacion_a_legal(self):
        """Test: Transición de EN_EVAL_TECNICA a EN_REVISION_LEGAL."""
        tramite = TramiteEnEvaluacionFactory()
        usuario = LegalUsuarioFactory()
        
        tramite.aprobar_tecnico(usuario=usuario)
        tramite.save()
        
        assert tramite.estado == 'EN_REVISION_LEGAL'

    def test_flujo_autorizacion_inicial_pasa_por_direcciones_y_retorna_a_direccion_general(self):
        """Test: Autorizacion Inicial sigue el flujo completo antes de aprobar."""
        tramite = TramiteAutorizacionInicialFactory(estado=EstadoTramite.EN_EVAL_TECNICA)
        especialista = EspecialistaUsuarioFactory()
        director_admin = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
        director_general = DirectorUsuarioFactory()
        legal = LegalUsuarioFactory()

        with pytest.raises(ValueError):
            tramite.aprobar_tecnico(usuario=especialista)

        tramite.enviar_a_direccion_administrativa(usuario=especialista)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA

        tramite.enviar_a_direccion_general(usuario=director_admin)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_DIRECCION_GENERAL

        with pytest.raises(ValueError):
            tramite.aprobar(numero_resolucion='RES-AI-001', usuario=director_general)

        tramite.enviar_a_revision_legal_desde_direccion_general(usuario=director_general)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_REVISION_LEGAL

        with pytest.raises(ValueError):
            tramite.aprobar_legal(usuario=legal)

        tramite.derivar_legal_a_direccion_general_autorizacion_inicial(usuario=legal)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_DIRECCION_GENERAL
        assert tramite.retorno_legal_a_direccion_general() is True

        tramite.aprobar(numero_resolucion='RES-AI-001', usuario=director_general)
        tramite.save()
        assert tramite.estado == EstadoTramite.APROBADO

    def test_subsanacion_observacion_legal_autorizacion_inicial_retorna_a_legal(self):
        """Test: Una observacion legal de Autorizacion Inicial retorna a Asesoria Legal al subsanar."""
        tramite = TramiteAutorizacionInicialFactory(estado=EstadoTramite.EN_REVISION_LEGAL)
        legal = LegalUsuarioFactory()
        mesa = MesaPartesUsuarioFactory()

        tramite.observar_legal(observaciones='Falta sustento legal', usuario=legal)
        tramite.save()
        assert tramite.estado == EstadoTramite.OBSERVADO
        assert tramite.ultima_observacion_desde_legal() is True

        tramite.subsanar_observacion_legal_autorizacion_inicial(usuario=mesa)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_REVISION_LEGAL

    def test_flujo_autorizacion_ruta_pasa_por_direcciones_y_legal(self):
        """Test: Autorizacion de Ruta sigue el flujo indicado y aprueba en Direccion General."""
        tramite = TramiteAutorizacionRutaFactory(estado=EstadoTramite.EN_EVAL_TECNICA)
        especialista = EspecialistaUsuarioFactory()
        director_admin = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
        director_general = DirectorUsuarioFactory()
        legal = LegalUsuarioFactory()

        with pytest.raises(ValueError):
            tramite.aprobar_tecnico(usuario=especialista)

        tramite.enviar_a_direccion_administrativa(usuario=especialista)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA

        tramite.enviar_a_direccion_general(usuario=director_admin)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_DIRECCION_GENERAL

        with pytest.raises(ValueError):
            tramite.aprobar(numero_resolucion='RES-RUTA-001', usuario=director_general)

        tramite.enviar_a_revision_legal_desde_direccion_general(usuario=director_general)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_REVISION_LEGAL

        with pytest.raises(ValueError):
            tramite.aprobar_legal(usuario=legal)

        tramite.derivar_legal_a_direccion_general_autorizacion_inicial(usuario=legal)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_DIRECCION_GENERAL
        assert tramite.retorno_legal_a_direccion_general() is True

        tramite.aprobar(numero_resolucion='RES-RUTA-001', usuario=director_general)
        tramite.save()
        assert tramite.estado == EstadoTramite.APROBADO
    
    def test_flujo_incremento_flota_pasa_por_direcciones_antes_de_legal(self):
        """Test: Incremento de Flota sigue el flujo especifico hasta Control de Calidad."""
        tramite = TramiteIncrementoFlotaFactory(estado='EN_EVAL_TECNICA')
        especialista = EspecialistaUsuarioFactory()
        director_admin = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
        director_general = DirectorUsuarioFactory()
        legal = LegalUsuarioFactory()

        with pytest.raises(ValueError):
            tramite.aprobar_tecnico(usuario=especialista)

        tramite.enviar_a_direccion_administrativa(usuario=especialista)
        tramite.save()
        assert tramite.estado == 'EN_DIRECCION_ADMINISTRATIVA'

        tramite.enviar_a_direccion_general(usuario=director_admin)
        tramite.save()
        assert tramite.estado == 'EN_DIRECCION_GENERAL'

        tramite.enviar_a_revision_legal_desde_direccion_general(usuario=director_general)
        tramite.save()
        assert tramite.estado == 'EN_REVISION_LEGAL'

        tramite.aprobar_legal(usuario=legal)
        tramite.save()
        assert tramite.estado == 'PENDIENTE_FIRMA'

        tramite.aprobar(numero_resolucion='RES-IF-001', usuario=director_general)
        tramite.save()
        assert tramite.estado == 'APROBADO'

    def test_flujo_renovacion_tuc_pasa_por_control_director_admin_y_tecnico(self):
        """Test: Renovacion de TUC sigue el flujo operativo sin resolucion."""
        tramite = TramiteFactory(tipo_tramite='RENOVACION_TUC')
        mesa = MesaPartesUsuarioFactory()
        control_calidad = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
        director_admin = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
        especialista = EspecialistaUsuarioFactory()

        with pytest.raises(ValueError):
            tramite.enviar_a_evaluacion_tecnica(usuario=mesa)

        tramite.enviar_a_control_calidad_renovacion_tuc(usuario=mesa)
        tramite.save()
        assert tramite.estado == 'PENDIENTE_FIRMA'

        tramite.observar_control_calidad_renovacion_tuc(
            observaciones='Falta documento',
            usuario=control_calidad,
        )
        tramite.save()
        assert tramite.estado == 'OBSERVADO'

        tramite.subsanar_observacion_control_calidad_renovacion_tuc(usuario=mesa)
        tramite.save()
        assert tramite.estado == 'PENDIENTE_FIRMA'

        with pytest.raises(ValueError):
            tramite.aprobar(numero_resolucion='RES-RTUC-001', usuario=director_admin)

        tramite.enviar_a_direccion_administrativa_renovacion_tuc(usuario=control_calidad)
        tramite.save()
        assert tramite.estado == 'EN_DIRECCION_ADMINISTRATIVA'

        tramite.firmar_y_derivar_a_tecnico_renovacion_tuc(usuario=director_admin)
        tramite.save()
        assert tramite.estado == 'EN_EVAL_TECNICA'

        with pytest.raises(ValueError):
            tramite.aprobar_tecnico_sin_revision_legal(usuario=especialista)

        tramite.enviar_a_control_calidad_final_renovacion_tuc(usuario=especialista)
        tramite.save()
        assert tramite.estado == 'APROBADO'

    def test_flujo_baja_vehiculo_pasa_por_control_calidad_antes_de_evaluacion(self):
        """Test: Baja de Vehiculo pasa por Control de Calidad antes de Evaluacion Tecnica."""
        tramite = TramiteFactory(tipo_tramite=TipoTramite.BAJA_VEHICULO)
        mesa = MesaPartesUsuarioFactory()
        control_calidad = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
        especialista = EspecialistaUsuarioFactory()

        with pytest.raises(ValueError):
            tramite.enviar_a_evaluacion_tecnica(usuario=mesa)

        tramite.enviar_a_control_calidad_baja_vehiculo(usuario=mesa)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD

        tramite.observar_control_calidad_baja_vehiculo(
            observaciones='Falta documento',
            usuario=control_calidad,
        )
        tramite.save()
        assert tramite.estado == EstadoTramite.OBSERVADO

        tramite.subsanar_observacion_control_calidad_baja_vehiculo(usuario=mesa)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_CONTROL_CALIDAD

        tramite.derivar_baja_vehiculo_a_evaluacion_tecnica(usuario=control_calidad)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_EVAL_TECNICA

        tramite.aprobar_tecnico(usuario=especialista)
        tramite.save()
        assert tramite.estado == EstadoTramite.EN_REVISION_LEGAL

    def test_transicion_legal_a_firma(self):
        """Test: Transición de EN_REVISION_LEGAL a PENDIENTE_FIRMA."""
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.SUSTITUCION_VEHICULO,
            estado='EN_REVISION_LEGAL',
        )
        usuario = DirectorUsuarioFactory()
        
        tramite.aprobar_legal(usuario=usuario)
        tramite.save()
        
        assert tramite.estado == 'PENDIENTE_FIRMA'
    
    def test_transicion_aprobar(self):
        """Test: Transición a APROBADO."""
        tramite = TramiteFactory(estado='PENDIENTE_FIRMA')
        usuario = DirectorUsuarioFactory()
        
        tramite.aprobar(usuario=usuario)
        tramite.save()
        
        assert tramite.estado == 'APROBADO'
    
    def test_transicion_denegar(self):
        """Test: Transición a DENEGADO."""
        tramite = TramiteFactory(estado='PENDIENTE_FIRMA')
        usuario = DirectorUsuarioFactory()
        
        tramite.denegar(usuario=usuario)
        tramite.save()
        
        assert tramite.estado == 'DENEGADO'
    
    def test_transicion_observar_desde_evaluacion(self):
        """Test: Transición a OBSERVADO desde evaluación técnica."""
        tramite = TramiteEnEvaluacionFactory()
        usuario = EspecialistaUsuarioFactory()
        
        tramite.observar_tecnico(observaciones='Falta documentación', usuario=usuario)
        tramite.save()
        
        assert tramite.estado == 'OBSERVADO'
    
    def test_transicion_invalida(self):
        """Test: No se puede transicionar directamente de RECIBIDO a APROBADO."""
        tramite = TramiteFactory()
        usuario = DirectorUsuarioFactory()
        
        with pytest.raises(TransitionNotAllowed):
            tramite.aprobar(usuario=usuario)


@pytest.mark.django_db
class TestHistorialTramite:
    """Tests para el modelo HistorialTramite."""
    
    def test_crear_historial(self):
        """Test: Crear registro de historial."""
        historial = HistorialTramiteFactory()
        assert historial.pk is not None
        assert historial.tramite is not None
    
    def test_historial_str(self):
        """Test: Representación string del historial."""
        historial = HistorialTramiteFactory()
        string = str(historial)
        assert historial.tramite.numero_expediente in string or 'RECIBIDO' in string
    
    def test_historial_fecha_automatica(self):
        """Test: Fecha se crea automáticamente."""
        historial = HistorialTramiteFactory()
        assert historial.fecha is not None
    
    def test_historial_estados_diferentes(self):
        """Test: Estados anterior y nuevo son diferentes."""
        historial = HistorialTramiteFactory(
            estado_anterior='RECIBIDO',
            estado_nuevo='EN_EVAL_TECNICA'
        )
        assert historial.estado_anterior != historial.estado_nuevo


@pytest.mark.django_db
class TestTramiteQueryset:
    """Tests para el queryset de trámites."""
    
    def test_filtrar_por_estado(self):
        """Test: Filtrar trámites por estado."""
        TramiteFactory.create_batch(3)  # RECIBIDO
        TramiteEnEvaluacionFactory.create_batch(2)  # EN_EVAL_TECNICA
        
        recibidos = Tramite.objects.filter(estado='RECIBIDO')
        assert recibidos.count() == 3
    
    def test_filtrar_por_tipo(self):
        """Test: Filtrar trámites por tipo."""
        TramiteAutorizacionInicialFactory.create_batch(3)
        TramiteIncrementoFlotaFactory.create_batch(2)
        
        autorizaciones = Tramite.objects.filter(tipo_tramite='AUTORIZACION_INICIAL')
        assert autorizaciones.count() == 3
    
    def test_filtrar_por_empresa(self):
        """Test: Filtrar trámites por empresa."""
        tramite = TramiteFactory()
        TramiteFactory.create_batch(2)
        
        result = Tramite.objects.filter(empresa=tramite.empresa)
        assert result.count() == 1
