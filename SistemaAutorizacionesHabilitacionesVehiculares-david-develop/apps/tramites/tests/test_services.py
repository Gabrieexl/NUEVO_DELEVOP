import pytest
from datetime import date

from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.configuracion.models import Carroceria, CategoriaVehiculo, TipoServicio
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.notificaciones.models import Notificacion
from apps.notificaciones.services import NotificacionService
from apps.tramites.models import ConductorTramite, DatosTramite, VehiculoTramite
from apps.tramites.services import procesar_tramite_aprobado
from apps.tramites.tests.factories import TramiteFactory
from apps.usuarios.tests.factories import UsuarioFactory
from apps.vehiculos.models import Vehiculo
from utils.constants import EstadoConductor, EstadoHabilitacion, EstadoTramite, Roles, TipoTramite


@pytest.mark.django_db
class TestProcesarIncrementoFlota:
    def test_cierre_agrega_conductores_del_tramite_a_la_empresa_como_activos(self):
        empresa = EmpresaTransporteFactory()
        autorizacion = AutorizacionFactory(empresa=empresa)
        usuario = UsuarioFactory()
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.INCREMENTO_FLOTA,
            estado=EstadoTramite.CERRADO,
            empresa=empresa,
            autorizacion=autorizacion,
            numero_resolucion='RES-IF-TEST',
            fecha_resolucion=date.today(),
        )
        DatosTramite.objects.create(tramite=tramite, datos_json={'vehiculo': {}})
        categoria, _ = CategoriaVehiculo.objects.get_or_create(
            codigo='M1',
            defaults={'nombre': 'Categoría M1'},
        )
        carroceria, _ = Carroceria.objects.get_or_create(
            categoria=categoria,
            codigo='CONV',
            defaults={'nombre': 'Convertible'},
        )
        VehiculoTramite.objects.create(
            tramite=tramite,
            placa_nueva='ABC-123',
            marca='TOYOTA',
            modelo='HIACE',
            anio_fabricacion=2026,
            categoria=categoria,
            carroceria=carroceria,
            capacidad_pasajeros=7,
            peso_bruto='76546',
            fecha_venc_soat=date(2028, 2, 20),
        )
        conductor_tramite = ConductorTramite.objects.create(
            tramite=tramite,
            dni='12345678',
            nombres='JUAN',
            apellido_paterno='PEREZ',
            apellido_materno='RAMOS',
            fecha_nacimiento=date(1990, 1, 1),
            licencia_numero='Q12345678',
            licencia_categoria='AII-B',
            licencia_fecha_emision=date(2024, 1, 1),
            licencia_fecha_vencimiento=date(2029, 1, 1),
        )

        resultado = procesar_tramite_aprobado(tramite, usuario)

        assert resultado['exito'] is True, resultado['mensaje']
        conductor = Conductor.objects.get(dni='12345678')
        assert conductor.empresa == empresa
        assert conductor.estado == EstadoConductor.ACTIVO
        conductor_tramite.refresh_from_db()
        assert conductor_tramite.conductor_creado == conductor
        assert conductor_tramite.estado_proceso == 'APROBADO'
        assert HabilitacionConductor.objects.filter(
            conductor=conductor,
            empresa=empresa,
            autorizacion=autorizacion,
            estado=EstadoHabilitacion.VIGENTE,
            tramite_origen=tramite,
        ).exists()
        assert Vehiculo.objects.filter(placa='ABC123', empresa_propietaria=empresa).exists()


@pytest.mark.django_db
class TestProcesarAutorizacionInicial:
    def test_cierre_crea_vehiculo_final_con_categoria_del_tramite(self):
        empresa = EmpresaTransporteFactory()
        usuario = UsuarioFactory()
        TipoServicio.objects.get_or_create(
            codigo='REGULAR',
            defaults={'nombre': 'Regular'},
        )
        categoria, _ = CategoriaVehiculo.objects.get_or_create(
            codigo='M2',
            defaults={'nombre': 'Categoría M2'},
        )
        if categoria.nombre != 'Categoría M2':
            categoria.nombre = 'Categoría M2'
            categoria.save(update_fields=['nombre'])
        carroceria, _ = Carroceria.objects.get_or_create(
            categoria=categoria,
            codigo='MICRO',
            defaults={'nombre': 'Microbus'},
        )
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
            estado=EstadoTramite.CERRADO,
            empresa=empresa,
            numero_resolucion='RES-AI-TEST',
            fecha_resolucion=date.today(),
        )
        DatosTramite.objects.create(
            tramite=tramite,
            datos_json={
                'autorizacion': {
                    'tipo_servicio': 'REGULAR',
                    'fecha_inicio_vigencia': date.today().isoformat(),
                    'fecha_fin_vigencia': date(date.today().year + 4, 12, 31).isoformat(),
                    'ambito': 'MADRE_DE_DIOS',
                    'modalidad': 'Transporte regular',
                    'rutas': [],
                    'frecuencias': [],
                    'descripcion_rutas': '',
                    'observaciones': '',
                }
            },
        )
        VehiculoTramite.objects.create(
            tramite=tramite,
            placa_nueva='AI1234',
            marca='RENAULT',
            modelo='MASTER',
            anio_fabricacion=2026,
            categoria=categoria,
            carroceria=carroceria,
            capacidad_pasajeros=16,
            peso_bruto='3500',
            fecha_venc_soat=date(2027, 6, 19),
        )

        resultado = procesar_tramite_aprobado(tramite, usuario)

        assert resultado['exito'] is True, resultado['mensaje']
        vehiculo = Vehiculo.objects.get(placa='AI1234', empresa_propietaria=empresa)
        assert vehiculo.categoria == categoria
        assert vehiculo.categoria.nombre == 'Categoría M2'


@pytest.mark.django_db
class TestNotificacionesIncrementoFlota:
    def test_autorizacion_inicial_aprobada_notifica_a_control_calidad_para_cierre(self):
        control_calidad = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
        mesa_partes = UsuarioFactory(rol=Roles.MESA_PARTES)
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
            estado=EstadoTramite.APROBADO,
            creado_por=UsuarioFactory(),
        )

        NotificacionService.notificar_cambio_estado_tramite(
            tramite=tramite,
            estado_anterior=EstadoTramite.EN_DIRECCION_GENERAL,
            estado_nuevo=EstadoTramite.APROBADO,
        )

        assert Notificacion.objects.filter(usuario=control_calidad, tramite_id=tramite.pk).exists()
        assert not Notificacion.objects.filter(usuario=mesa_partes, tramite_id=tramite.pk).exists()

    def test_incremento_aprobado_notifica_a_control_calidad_para_cierre(self):
        control_calidad = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
        mesa_partes = UsuarioFactory(rol=Roles.MESA_PARTES)
        creador = UsuarioFactory()
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.INCREMENTO_FLOTA,
            estado=EstadoTramite.APROBADO,
            creado_por=creador,
        )

        NotificacionService.notificar_cambio_estado_tramite(
            tramite=tramite,
            estado_anterior=EstadoTramite.PENDIENTE_FIRMA,
            estado_nuevo=EstadoTramite.APROBADO,
        )

        assert Notificacion.objects.filter(usuario=control_calidad, tramite_id=tramite.pk).exists()
        assert not Notificacion.objects.filter(usuario=mesa_partes, tramite_id=tramite.pk).exists()

    def test_baja_vehiculo_pendiente_firma_no_notifica_director_administrativo(self):
        director_general = UsuarioFactory(rol=Roles.DIRECTOR_GENERAL)
        director_admin = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.BAJA_VEHICULO,
            estado=EstadoTramite.PENDIENTE_FIRMA,
        )

        NotificacionService.notificar_cambio_estado_tramite(
            tramite=tramite,
            estado_anterior=EstadoTramite.EN_REVISION_LEGAL,
            estado_nuevo=EstadoTramite.PENDIENTE_FIRMA,
        )

        assert Notificacion.objects.filter(usuario=director_general, tramite_id=tramite.pk).exists()
        assert not Notificacion.objects.filter(usuario=director_admin, tramite_id=tramite.pk).exists()

    def test_baja_vehiculo_en_control_calidad_notifica_control_calidad(self):
        control_calidad = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
        tramite = TramiteFactory(
            tipo_tramite=TipoTramite.BAJA_VEHICULO,
            estado=EstadoTramite.EN_CONTROL_CALIDAD,
        )

        NotificacionService.notificar_cambio_estado_tramite(
            tramite=tramite,
            estado_anterior=EstadoTramite.RECIBIDO,
            estado_nuevo=EstadoTramite.EN_CONTROL_CALIDAD,
        )

        assert Notificacion.objects.filter(usuario=control_calidad, tramite_id=tramite.pk).exists()
