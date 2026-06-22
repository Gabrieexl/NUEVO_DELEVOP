import pytest
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.configuracion.models import Carroceria, CategoriaVehiculo, TipoServicio
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.tramites.models import ConductorTramite, DatosTramite, Tramite, VehiculoTramite
from apps.tramites.tests.factories import TramiteFactory
from apps.usuarios.tests.factories import MesaPartesUsuarioFactory, UsuarioFactory
from apps.vehiculos.models import HabilitacionVehicular, Vehiculo
from apps.vehiculos.tests.factories import HabilitacionVehicularFactory, VehiculoHabilitadoFactory
from utils.constants import EstadoTramite, Roles, TipoTramite


@pytest.mark.django_db
def test_crear_incremento_flota_paso_2_renderiza_formsets(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    empresa = EmpresaTransporteFactory()
    autorizacion = AutorizacionFactory(empresa=empresa)

    session = client.session
    session['tramites_creacion_borrador'] = {
        'tipo_tramite': TipoTramite.INCREMENTO_FLOTA,
        'empresa': empresa.pk,
        'empresa_nombre': empresa.razon_social,
        'autorizacion': autorizacion.pk,
        'vehiculo': None,
        'conductor': None,
        'descripcion': 'Incremento de flota',
        'expediente_externo': '',
        'solicitante_dni': '',
        'solicitante_nombres': '',
        'solicitante_telefono': '',
        'solicitante_email': '',
        'return_url': reverse('tramites:lista'),
    }
    session.save()

    response = client.get(f"{reverse('tramites:crear')}?paso=2")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="agregar-vehiculo-incremento"' in content
    assert 'id="agregar-conductor-incremento"' in content
    assert 'name="vehiculos-TOTAL_FORMS"' in content
    assert 'name="conductores-TOTAL_FORMS"' in content
    assert empresa.razon_social in content


@pytest.mark.django_db
def test_crear_autorizacion_inicial_paso_2_renderiza_formsets(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    empresa = EmpresaTransporteFactory()
    TipoServicio.objects.get_or_create(
        codigo='REGULAR',
        defaults={'nombre': 'Regular'},
    )

    session = client.session
    session['tramites_creacion_borrador'] = {
        'tipo_tramite': TipoTramite.AUTORIZACION_INICIAL,
        'empresa': empresa.pk,
        'empresa_nombre': empresa.razon_social,
        'autorizacion': None,
        'vehiculo': None,
        'conductor': None,
        'descripcion': 'Autorizacion inicial',
        'expediente_externo': '',
        'solicitante_dni': '',
        'solicitante_nombres': '',
        'solicitante_telefono': '',
        'solicitante_email': '',
        'return_url': reverse('tramites:lista'),
    }
    session.save()

    response = client.get(f"{reverse('tramites:crear')}?paso=2")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'Vehiculos de la Flota Inicial' in content
    assert 'Conductores Iniciales' in content
    assert 'id="agregar-vehiculo-incremento"' in content
    assert 'id="agregar-conductor-incremento"' in content
    assert 'name="vehiculos-TOTAL_FORMS"' in content
    assert 'name="conductores-TOTAL_FORMS"' in content


@pytest.mark.django_db
def test_crear_autorizacion_inicial_guarda_vehiculo_con_categoria_produccion(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    empresa = EmpresaTransporteFactory()
    tipo_servicio, _ = TipoServicio.objects.get_or_create(
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

    session = client.session
    session['tramites_creacion_borrador'] = {
        'tipo_tramite': TipoTramite.AUTORIZACION_INICIAL,
        'empresa': empresa.pk,
        'empresa_nombre': empresa.razon_social,
        'autorizacion': None,
        'vehiculo': None,
        'conductor': None,
        'descripcion': 'Autorizacion inicial con flota',
        'expediente_externo': '',
        'solicitante_dni': '12345678',
        'solicitante_nombres': 'Solicitante de prueba',
        'solicitante_telefono': '',
        'solicitante_email': '',
        'return_url': reverse('tramites:lista'),
    }
    session.save()

    data = {
        'paso': '2',
        'tipo_servicio': str(tipo_servicio.pk),
        'modalidad': 'Transporte regular de personas',
        'ambito': 'MADRE_DE_DIOS',
        'fecha_inicio_vigencia': '2026-06-19',
        'fecha_fin_vigencia': '2030-06-19',
        'descripcion_rutas': '',
        'observaciones': '',
        'vehiculos-TOTAL_FORMS': '1',
        'vehiculos-INITIAL_FORMS': '0',
        'vehiculos-MIN_NUM_FORMS': '1',
        'vehiculos-MAX_NUM_FORMS': '1000',
        'vehiculos-0-placa': 'AI-1234',
        'vehiculos-0-marca': 'RENAULT',
        'vehiculos-0-modelo': 'MASTER',
        'vehiculos-0-anio_fabricacion': '2026',
        'vehiculos-0-categoria': str(categoria.pk),
        'vehiculos-0-carroceria': str(carroceria.pk),
        'vehiculos-0-capacidad_sentados': '16',
        'vehiculos-0-peso_bruto': '3500',
        'vehiculos-0-fecha_venc_soat': '2027-06-19',
        'conductores-TOTAL_FORMS': '1',
        'conductores-INITIAL_FORMS': '0',
        'conductores-MIN_NUM_FORMS': '1',
        'conductores-MAX_NUM_FORMS': '1000',
        'conductores-0-dni': '23456789',
        'conductores-0-nombres': 'JUAN',
        'conductores-0-apellido_paterno': 'PEREZ',
        'conductores-0-apellido_materno': 'RAMOS',
        'conductores-0-fecha_nacimiento': '1990-01-01',
        'conductores-0-licencia_numero': 'Q23456789',
        'conductores-0-licencia_categoria': 'AII-B',
        'conductores-0-licencia_fecha_emision': '2024-01-01',
        'conductores-0-licencia_fecha_vencimiento': '2029-01-01',
    }

    response = client.post(reverse('tramites:crear'), data)

    assert response.status_code == 302
    tramite = Tramite.objects.get(tipo_tramite=TipoTramite.AUTORIZACION_INICIAL)
    vehiculo_tramite = VehiculoTramite.objects.get(tramite=tramite)
    assert vehiculo_tramite.categoria == categoria
    assert vehiculo_tramite.categoria.nombre == 'Categoría M2'
    assert ConductorTramite.objects.filter(tramite=tramite).count() == 1

    datos = DatosTramite.objects.get(tramite=tramite).datos_json
    assert datos['autorizacion']['tipo_servicio'] == tipo_servicio.pk
    assert len(datos['vehiculos']) == 1
    assert len(datos['conductores']) == 1


@pytest.mark.django_db
def test_crear_incremento_flota_paso_2_permite_varios_vehiculos_y_conductores(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)

    empresa = EmpresaTransporteFactory()
    autorizacion = AutorizacionFactory(empresa=empresa)
    categoria, _ = CategoriaVehiculo.objects.get_or_create(
        codigo='M1',
        defaults={'nombre': 'Categoría M1'},
    )
    carroceria, _ = Carroceria.objects.get_or_create(
        categoria=categoria,
        codigo='CONV',
        defaults={'nombre': 'Convertible'},
    )

    session = client.session
    session['tramites_creacion_borrador'] = {
        'tipo_tramite': TipoTramite.INCREMENTO_FLOTA,
        'empresa': empresa.pk,
        'empresa_nombre': empresa.razon_social,
        'autorizacion': autorizacion.pk,
        'vehiculo': None,
        'conductor': None,
        'descripcion': 'Incremento de flota con multiples vehiculos',
        'expediente_externo': '',
        'solicitante_dni': '',
        'solicitante_nombres': '',
        'solicitante_telefono': '',
        'solicitante_email': '',
        'return_url': reverse('tramites:lista'),
    }
    session.save()

    data = {
        'paso': '2',
        'vehiculos-TOTAL_FORMS': '2',
        'vehiculos-INITIAL_FORMS': '0',
        'vehiculos-MIN_NUM_FORMS': '1',
        'vehiculos-MAX_NUM_FORMS': '1000',
        'vehiculos-0-placa': 'AAA-111',
        'vehiculos-0-marca': 'TOYOTA',
        'vehiculos-0-modelo': 'HIACE',
        'vehiculos-0-anio_fabricacion': '2026',
        'vehiculos-0-categoria': str(categoria.pk),
        'vehiculos-0-carroceria': str(carroceria.pk),
        'vehiculos-0-capacidad_sentados': '7',
        'vehiculos-0-peso_bruto': '76546',
        'vehiculos-0-fecha_venc_soat': '2028-02-20',
        'vehiculos-1-placa': 'BBB-222',
        'vehiculos-1-marca': 'TOYOTA',
        'vehiculos-1-modelo': 'HIACE',
        'vehiculos-1-anio_fabricacion': '2026',
        'vehiculos-1-categoria': str(categoria.pk),
        'vehiculos-1-carroceria': str(carroceria.pk),
        'vehiculos-1-capacidad_sentados': '8',
        'vehiculos-1-peso_bruto': '76547',
        'vehiculos-1-fecha_venc_soat': '2028-02-21',
        'conductores-TOTAL_FORMS': '2',
        'conductores-INITIAL_FORMS': '0',
        'conductores-MIN_NUM_FORMS': '1',
        'conductores-MAX_NUM_FORMS': '1000',
        'conductores-0-dni': '12345678',
        'conductores-0-nombres': 'JUAN',
        'conductores-0-apellido_paterno': 'PEREZ',
        'conductores-0-apellido_materno': 'RAMOS',
        'conductores-0-fecha_nacimiento': '1990-01-01',
        'conductores-0-licencia_numero': 'Q12345678',
        'conductores-0-licencia_categoria': 'AII-B',
        'conductores-0-licencia_fecha_emision': '2024-01-01',
        'conductores-0-licencia_fecha_vencimiento': '2029-01-01',
        'conductores-1-dni': '87654321',
        'conductores-1-nombres': 'MARIA',
        'conductores-1-apellido_paterno': 'GOMEZ',
        'conductores-1-apellido_materno': 'LOPEZ',
        'conductores-1-fecha_nacimiento': '1992-02-02',
        'conductores-1-licencia_numero': 'Q87654321',
        'conductores-1-licencia_categoria': 'AII-B',
        'conductores-1-licencia_fecha_emision': '2024-02-02',
        'conductores-1-licencia_fecha_vencimiento': '2029-02-02',
    }

    response = client.post(reverse('tramites:crear'), data)

    assert response.status_code == 302
    tramite = Tramite.objects.get(tipo_tramite=TipoTramite.INCREMENTO_FLOTA)
    assert tramite.empresa == empresa
    assert tramite.autorizacion == autorizacion
    assert VehiculoTramite.objects.filter(tramite=tramite).count() == 2
    assert ConductorTramite.objects.filter(tramite=tramite).count() == 2

    datos = DatosTramite.objects.get(tramite=tramite).datos_json
    assert len(datos['vehiculos']) == 2
    assert len(datos['conductores']) == 2


@pytest.mark.django_db
def test_crear_renovacion_tuc_paso_2_renderiza_formset_de_vehiculos(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    empresa = EmpresaTransporteFactory()
    autorizacion = AutorizacionFactory(empresa=empresa)

    session = client.session
    session['tramites_creacion_borrador'] = {
        'tipo_tramite': TipoTramite.RENOVACION_TUC,
        'empresa': empresa.pk,
        'empresa_nombre': empresa.razon_social,
        'autorizacion': autorizacion.pk,
        'vehiculo': None,
        'conductor': None,
        'descripcion': 'Renovacion de TUC',
        'expediente_externo': '',
        'solicitante_dni': '',
        'solicitante_nombres': '',
        'solicitante_telefono': '',
        'solicitante_email': '',
        'return_url': reverse('tramites:lista'),
    }
    session.save()

    response = client.get(f"{reverse('tramites:crear')}?paso=2")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="agregar-vehiculo-renovacion-tuc"' in content
    assert 'name="renovacion_tuc-TOTAL_FORMS"' in content
    assert 'Debe seleccionar una autorizaci' not in content


@pytest.mark.django_db
def test_crear_renovacion_tuc_permite_seleccionar_varios_vehiculos(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    empresa = EmpresaTransporteFactory()
    autorizacion = AutorizacionFactory(empresa=empresa)

    vehiculo_1 = VehiculoHabilitadoFactory(
        empresa_propietaria=empresa,
        placa='RTA-001',
    )
    vehiculo_2 = VehiculoHabilitadoFactory(
        empresa_propietaria=empresa,
        placa='RTB-002',
    )
    HabilitacionVehicularFactory(
        vehiculo=vehiculo_1,
        autorizacion=autorizacion,
        numero_tuc='TUC-001',
        fecha_expedicion_tuc=date(2025, 1, 10),
        fecha_autorizacion_transportista=date(2025, 1, 1),
        fecha_expiracion_transportista=date(2026, 1, 1),
    )
    HabilitacionVehicularFactory(
        vehiculo=vehiculo_2,
        autorizacion=autorizacion,
        numero_tuc='TUC-002',
        fecha_expedicion_tuc=date(2025, 2, 10),
        fecha_autorizacion_transportista=date(2025, 2, 1),
        fecha_expiracion_transportista=date(2026, 2, 1),
    )

    session = client.session
    session['tramites_creacion_borrador'] = {
        'tipo_tramite': TipoTramite.RENOVACION_TUC,
        'empresa': empresa.pk,
        'empresa_nombre': empresa.razon_social,
        'autorizacion': autorizacion.pk,
        'vehiculo': None,
        'conductor': None,
        'descripcion': 'Renovacion de multiples TUC',
        'expediente_externo': '',
        'solicitante_dni': '',
        'solicitante_nombres': '',
        'solicitante_telefono': '',
        'solicitante_email': '',
        'return_url': reverse('tramites:lista'),
    }
    session.save()

    data = {
        'paso': '2',
        'renovacion_tuc-TOTAL_FORMS': '2',
        'renovacion_tuc-INITIAL_FORMS': '0',
        'renovacion_tuc-MIN_NUM_FORMS': '1',
        'renovacion_tuc-MAX_NUM_FORMS': '1000',
        'renovacion_tuc-0-placa': vehiculo_1.placa,
        'renovacion_tuc-0-vehiculo': str(vehiculo_1.pk),
        'renovacion_tuc-0-numero_tuc': 'TUC-001',
        'renovacion_tuc-0-fecha_expedicion_tuc': '2025-01-10',
        'renovacion_tuc-1-placa': vehiculo_2.placa,
        'renovacion_tuc-1-vehiculo': str(vehiculo_2.pk),
        'renovacion_tuc-1-numero_tuc': 'TUC-002',
        'renovacion_tuc-1-fecha_expedicion_tuc': '2025-02-10',
    }

    response = client.post(reverse('tramites:crear'), data)

    assert response.status_code == 302
    tramite = Tramite.objects.get(tipo_tramite=TipoTramite.RENOVACION_TUC)
    vehiculos_tramite = list(VehiculoTramite.objects.filter(tramite=tramite).order_by('placa_nueva'))

    assert len(vehiculos_tramite) == 2
    assert [vt.placa_nueva for vt in vehiculos_tramite] == sorted([vehiculo_1.placa, vehiculo_2.placa])
    assert vehiculos_tramite[0].numero_tuc == 'TUC-001'
    assert vehiculos_tramite[0].fecha_autorizacion_transportista == date(2025, 1, 1)
    assert vehiculos_tramite[0].fecha_expiracion_transportista == date(2026, 1, 1)

    datos = DatosTramite.objects.get(tramite=tramite).datos_json
    assert len(datos['renovacion_tuc']['vehiculos']) == 2


@pytest.mark.django_db
def test_renovacion_tuc_mesa_partes_envia_a_control_calidad(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.RENOVACION_TUC,
        estado=EstadoTramite.RECIBIDO,
    )

    response = client.post(reverse('tramites:enviar_evaluacion', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.PENDIENTE_FIRMA


@pytest.mark.django_db
def test_baja_vehiculo_mesa_partes_envia_a_control_calidad(client):
    usuario = MesaPartesUsuarioFactory()
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.BAJA_VEHICULO,
        estado=EstadoTramite.RECIBIDO,
    )

    response = client.post(reverse('tramites:enviar_evaluacion', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_CONTROL_CALIDAD


@pytest.mark.django_db
def test_baja_vehiculo_control_calidad_deriva_a_evaluacion_tecnica(client):
    usuario = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.BAJA_VEHICULO,
        estado=EstadoTramite.EN_CONTROL_CALIDAD,
    )

    response = client.post(reverse('tramites:aprobar_evaluacion', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_EVAL_TECNICA


@pytest.mark.django_db
def test_renovacion_tuc_control_calidad_deriva_a_direccion_administrativa(client):
    usuario = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.RENOVACION_TUC,
        estado=EstadoTramite.PENDIENTE_FIRMA,
    )

    response = client.post(reverse('tramites:enviar_direccion_administrativa', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA


@pytest.mark.django_db
def test_renovacion_tuc_director_admin_firma_y_deriva_a_tecnico(client):
    usuario = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.RENOVACION_TUC,
        estado=EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
    )

    response = client.post(reverse('tramites:firmar_derivar_tecnico', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_EVAL_TECNICA


@pytest.mark.django_db
def test_autorizacion_inicial_especialista_deriva_a_direccion_administrativa(client):
    usuario = UsuarioFactory(rol=Roles.ESPECIALISTA_TECNICO)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
        estado=EstadoTramite.EN_EVAL_TECNICA,
    )

    response = client.post(reverse('tramites:aprobar_evaluacion', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_DIRECCION_ADMINISTRATIVA


@pytest.mark.django_db
def test_autorizacion_inicial_director_admin_deriva_a_direccion_general(client):
    usuario = UsuarioFactory(rol=Roles.DIRECTOR_ADMINISTRATIVO)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
        estado=EstadoTramite.EN_DIRECCION_ADMINISTRATIVA,
    )

    response = client.post(reverse('tramites:enviar_direccion_general', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_DIRECCION_GENERAL


@pytest.mark.django_db
def test_autorizacion_inicial_director_general_deriva_a_asesoria_legal(client):
    usuario = UsuarioFactory(rol=Roles.DIRECTOR_GENERAL)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
        estado=EstadoTramite.EN_DIRECCION_GENERAL,
    )

    response = client.post(reverse('tramites:enviar_legal', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_REVISION_LEGAL


@pytest.mark.django_db
def test_autorizacion_inicial_legal_deriva_de_regreso_a_direccion_general(client):
    usuario = UsuarioFactory(rol=Roles.ASESORIA_LEGAL)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
        estado=EstadoTramite.EN_REVISION_LEGAL,
    )

    response = client.post(reverse('tramites:aprobar_legal', args=[tramite.pk]), {'comentario': ''})

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.EN_DIRECCION_GENERAL
    assert tramite_actualizado.retorno_legal_a_direccion_general() is True


@pytest.mark.django_db
def test_autorizacion_inicial_director_general_aprueba_despues_de_legal(client):
    usuario = UsuarioFactory(rol=Roles.DIRECTOR_GENERAL)
    client.force_login(usuario)
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
        estado=EstadoTramite.EN_REVISION_LEGAL,
    )
    tramite.derivar_legal_a_direccion_general_autorizacion_inicial(usuario=usuario)
    tramite.save()

    archivo = SimpleUploadedFile(
        'resolucion.pdf',
        b'%PDF-1.4\n%%EOF',
        content_type='application/pdf',
    )
    response = client.post(
        reverse('tramites:aprobar', args=[tramite.pk]),
        {
            'numero_resolucion': 'RES-AI-VIEW-001',
            'fecha_resolucion': '2026-06-19',
            'archivo_resolucion': archivo,
            'comentario': '',
        },
    )

    assert response.status_code == 302
    tramite_actualizado = Tramite.objects.get(pk=tramite.pk)
    assert tramite_actualizado.estado == EstadoTramite.APROBADO
    assert tramite_actualizado.numero_resolucion == 'RES-AI-VIEW-001'


@pytest.mark.django_db
def test_autorizacion_inicial_control_calidad_cierra_registrando_tuc(client):
    usuario = UsuarioFactory(rol=Roles.CONTROL_CALIDAD)
    client.force_login(usuario)
    empresa = EmpresaTransporteFactory()
    tipo_servicio, _ = TipoServicio.objects.get_or_create(
        codigo='REGULAR',
        defaults={'nombre': 'Regular'},
    )
    categoria, _ = CategoriaVehiculo.objects.get_or_create(
        codigo='M2',
        defaults={'nombre': 'Categoría M2'},
    )
    carroceria, _ = Carroceria.objects.get_or_create(
        categoria=categoria,
        codigo='MICRO',
        defaults={'nombre': 'Microbus'},
    )
    tramite = TramiteFactory(
        tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
        estado=EstadoTramite.APROBADO,
        empresa=empresa,
        numero_resolucion='RES-AI-CLOSE-001',
        fecha_resolucion=date(2026, 6, 19),
    )
    DatosTramite.objects.create(
        tramite=tramite,
        datos_json={
            'autorizacion': {
                'tipo_servicio': tipo_servicio.pk,
                'fecha_inicio_vigencia': '2026-06-19',
                'fecha_fin_vigencia': '2030-06-19',
                'ambito': 'MADRE_DE_DIOS',
                'modalidad': 'Transporte regular',
                'rutas': [],
                'frecuencias': [],
                'descripcion_rutas': '',
                'observaciones': '',
            }
        },
    )
    vehiculo_tramite = VehiculoTramite.objects.create(
        tramite=tramite,
        placa_nueva='AI-1234',
        marca='RENAULT',
        modelo='MASTER',
        anio_fabricacion=2026,
        categoria=categoria,
        carroceria=carroceria,
        capacidad_pasajeros=16,
        peso_bruto='3500',
        fecha_venc_soat=date(2027, 6, 19),
    )

    response = client.post(
        reverse('tramites:cerrar', args=[tramite.pk]),
        {
            'comentario': '',
            'tucs-TOTAL_FORMS': '1',
            'tucs-INITIAL_FORMS': '1',
            'tucs-MIN_NUM_FORMS': '0',
            'tucs-MAX_NUM_FORMS': '1000',
            'tucs-0-id': str(vehiculo_tramite.pk),
            'tucs-0-numero_tuc': 'TUC-AI-001',
            'tucs-0-fecha_expedicion_tuc': '2026-06-19',
            'tucs-0-fecha_autorizacion_transportista': '2026-06-19',
            'tucs-0-fecha_expiracion_transportista': '2027-06-19',
        },
    )

    assert response.status_code == 302
    tramite.refresh_from_db()
    vehiculo_tramite.refresh_from_db()
    assert tramite.estado == EstadoTramite.CERRADO
    assert tramite.autorizacion is not None
    assert vehiculo_tramite.numero_tuc == 'TUC-AI-001'

    vehiculo = Vehiculo.objects.get(placa='AI1234', empresa_propietaria=empresa)
    habilitacion = HabilitacionVehicular.objects.get(vehiculo=vehiculo, autorizacion=tramite.autorizacion)
    assert habilitacion.numero_tuc == 'TUC-AI-001'
