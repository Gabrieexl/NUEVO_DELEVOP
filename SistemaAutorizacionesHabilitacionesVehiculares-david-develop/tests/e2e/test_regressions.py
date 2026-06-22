import pytest
from playwright.sync_api import Page, expect
from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.configuracion.models import Carroceria, TipoServicio, CategoriaVehiculo
from apps.autorizaciones.models import Autorizacion
from apps.tramites.models import Tramite, DatosTramite
from apps.notificaciones.models import Notificacion
from utils.constants import TipoTramite, EstadoTramite, Roles, EstadoHabilitacion, EstadoVehiculo
from django.utils import timezone
import io

@pytest.mark.django_db(transaction=True)
class TestRegressions:
    """
    Pruebas E2E para asegurar que los errores corregidos no vuelvan a ocurrir.
    """

    def test_excel_export_no_500(self, page: Page, live_server, admin_user, user_password):
        """
        Error: AttributeError: 'Vehiculo' object has no attribute 'get_tipo_vehiculo_display'
        Verifica que la exportación a Excel de vehículos funcione sin errores 500.
        """
        # Crear datos mínimos
        cat_m3, _ = CategoriaVehiculo.objects.get_or_create(codigo="M3", defaults={"nombre": "Categoría M3"})
        tipo_v, _ = Carroceria.objects.get_or_create(codigo="M3", defaults={"nombre": "M3", "categoria": cat_m3})
        empresa = EmpresaTransporte.objects.create(ruc="12345678901", razon_social="Empresa PDF Padron Test")
        Vehiculo.objects.create(
            placa="PAD-123", 
            empresa_propietaria=empresa, 
            marca="Toyota", 
            modelo="Hiace", 
            anio_fabricacion=2020,
            capacidad_sentados=15,
            carroceria=tipo_v,
            estado=EstadoVehiculo.HABILITADO
        )

        # Login
        page.goto(f"{live_server.url}/usuarios/login/")
        page.fill('input[name="username"]', admin_user.username)
        page.fill('input[name="password"]', user_password)
        page.click('button[type="submit"]')

        # Ir a reportes y descargar Excel
        # URL correcta: /reportes/excel/vehiculos/
        # No usamos page.goto porque inicia una descarga y falla el test
        
        # Si no hay error 500, la respuesta debería ser un archivo o al menos no una página de error
        response = page.request.get(f"{live_server.url}/reportes/excel/vehiculos/")
        assert response.status == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]

    def test_html_messages_rendering(self, page: Page, live_server, admin_user, user_password):
        """
        Error: Etiquetas HTML (<ul>, <li>) visibles en mensajes de éxito.
        Verifica que los mensajes con HTML se rendericen como elementos HTML y no como texto plano.
        """
        # Login
        page.goto(f"{live_server.url}/usuarios/login/")
        page.fill('input[name="username"]', admin_user.username)
        page.fill('input[name="password"]', user_password)
        page.click('button[type="submit"]')

        # Crear un trámite y aprobarlo para generar el mensaje con HTML
        cat_m3, _ = CategoriaVehiculo.objects.get_or_create(codigo="M3", defaults={"nombre": "Categoría M3"})
        tipo_v, _ = Carroceria.objects.get_or_create(codigo="M3", defaults={"nombre": "M3", "categoria": cat_m3})
        tipo_s, _ = TipoServicio.objects.get_or_create(codigo="REGULAR", defaults={"nombre": "REGULAR"})
        empresa = EmpresaTransporte.objects.create(ruc="11111111111", razon_social="Empresa HTML Test")
        autorizacion = Autorizacion.objects.create(
            empresa=empresa, numero_resolucion="RES-HTML", 
            fecha_resolucion=timezone.now().date(),
            fecha_inicio_vigencia=timezone.now().date(),
            fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=365),
            tipo_servicio=tipo_s
        )
        
        tramite = Tramite.objects.create(
            tipo_tramite=TipoTramite.AUTORIZACION_INICIAL,
            empresa=empresa,
            estado=EstadoTramite.PENDIENTE_FIRMA,
            creado_por=admin_user
        )
        DatosTramite.objects.create(tramite=tramite, datos_json={
            'autorizacion': {
                'fecha_inicio_vigencia': timezone.now().date().isoformat(),
                'fecha_fin_vigencia': (timezone.now().date() + timezone.timedelta(days=365)).isoformat(),
                'ambito': 'MADRE_DE_DIOS',
                'tipo_servicio': 'REGULAR'
            }
        })

        # Ir a aprobar el trámite
        page.goto(f"{live_server.url}/tramites/{tramite.pk}/aprobar/")
        page.fill('input[name="numero_resolucion"]', "RES-APROBADA-001")
        # Usar selector más específico para el botón de submit del formulario principal
        page.click('form[method="post"] button[type="submit"].btn-primary')

        # Verificar que el mensaje NO contenga las etiquetas como texto
        # Esperar a que aparezca el mensaje de éxito
        try:
            expect(page.locator(".alert-success")).to_be_visible(timeout=10000)
        except:
            # Si falla, imprimir errores si los hay
            if page.locator(".alert-danger").is_visible():
                print(f"Error en formulario: {page.locator('.alert-danger').inner_text()}")
            if page.locator(".invalid-feedback").is_visible():
                print(f"Errores de campo: {page.locator('.invalid-feedback').all_inner_texts()}")
            raise

        # Si se renderiza bien, el locator no debería encontrar "<ul>" como texto plano
        assert "<ul>" not in page.locator(".alert-success").inner_text()
        # Pero sí debería estar en el inner_html
        assert "<ul>" in page.locator(".alert-success").inner_html()
        assert "<li>" in page.locator(".alert-success").inner_html()

    def test_plate_search_logic_enabled_vehicle(self, page: Page, live_server, admin_user, user_password):
        """
        Error: "Vehículo sin autorización vigente" para vehículos habilitados.
        Verifica que un vehículo con estado HABILITADO y autorizacion_principal se muestre como habilitado.
        """
        cat_m3, _ = CategoriaVehiculo.objects.get_or_create(codigo="M3", defaults={"nombre": "Categoría M3"})
        tipo_v, _ = Carroceria.objects.get_or_create(codigo="M3", defaults={"nombre": "M3", "categoria": cat_m3})
        empresa = EmpresaTransporte.objects.create(ruc="22222222222", razon_social="Empresa Consulta Test")
        autorizacion = Autorizacion.objects.create(
            empresa=empresa, numero_resolucion="RES-CONSULTA", 
            fecha_resolucion=timezone.now().date(),
            fecha_inicio_vigencia=timezone.now().date(),
            fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=365),
            estado='VIGENTE'
        )
        # Vehículo habilitado CON registro en HabilitacionVehicular (Datos correctos)
        vehiculo = Vehiculo.objects.create(
            placa="HAB-123", 
            empresa_propietaria=empresa, 
            marca="Toyota", 
            modelo="Hiace", 
            anio_fabricacion=2020,
            capacidad_sentados=15,
            carroceria=tipo_v,
            estado=EstadoVehiculo.HABILITADO,
            autorizacion_principal=autorizacion
        )
        # Crear la habilitación vehicular (requisito obligatorio)
        HabilitacionVehicular.objects.create(
            vehiculo=vehiculo,
            autorizacion=autorizacion,
            fecha_inicio=timezone.now().date(),
            estado=EstadoHabilitacion.VIGENTE,
            motivo="Carga inicial"
        )

        # Login
        page.goto(f"{live_server.url}/usuarios/login/")
        page.fill('input[name="username"]', admin_user.username)
        page.fill('input[name="password"]', user_password)
        page.click('button[type="submit"]')

        # Consultar placa
        page.goto(f"{live_server.url}/consulta/placa/")
        page.fill('input[name="placa"]', "HAB-123")
        page.click('button:has-text(\"Consultar\")')

        # Verificar que el mensaje sea positivo
        expect(page.locator(".alert-success")).to_contain_text("Vehículo habilitado para el servicio")
        expect(page.locator("body")).to_contain_text("Vigente")

    def test_subsanar_button_visibility_mesa_partes(self, page: Page, live_server, mesa_partes_user, user_password):
        """
        Error: No aparece el botón "Subsanar" para Mesa de Partes.
        Verifica que el botón sea visible cuando el trámite está OBSERVADO.
        """
        empresa = EmpresaTransporte.objects.create(ruc="33333333333", razon_social="Empresa Subsanar Test")
        tramite = Tramite.objects.create(
            tipo_tramite=TipoTramite.INCREMENTO_FLOTA,
            empresa=empresa,
            estado=EstadoTramite.OBSERVADO,
            creado_por=mesa_partes_user
        )

        # Login como Mesa de Partes
        page.goto(f"{live_server.url}/usuarios/login/")
        page.fill('input[name="username"]', mesa_partes_user.username)
        page.fill('input[name="password"]', user_password)
        page.click('button[type="submit"]')

        # Ir al detalle del trámite
        page.goto(f"{live_server.url}/tramites/{tramite.pk}/")
        
        # Verificar visibilidad del botón (usar selector exacto para evitar coincidencia con nombre de empresa)
        expect(page.locator('a.btn:has-text(\"Subsanar\")')).to_be_visible()
        expect(page.locator('a.btn:has-text(\"Editar\")')).to_be_visible()

    def test_notification_routing_on_state_change(self, page: Page, live_server, admin_user, especialista_user, user_password):
        """
        Error: Los roles no reciben las notificaciones que les corresponden.
        Verifica que al enviar a evaluación, el especialista reciba una notificación.
        """
        empresa = EmpresaTransporte.objects.create(ruc="44444444444", razon_social="Empresa Notif Test")
        tramite = Tramite.objects.create(
            tipo_tramite=TipoTramite.INCREMENTO_FLOTA,
            empresa=empresa,
            estado=EstadoTramite.RECIBIDO,
            creado_por=admin_user
        )

        # Login como Admin para realizar la acción
        page.goto(f"{live_server.url}/usuarios/login/")
        page.fill('input[name="username"]', admin_user.username)
        page.fill('input[name="password"]', user_password)
        page.click('button[type="submit"]')

        # Enviar a evaluación
        page.goto(f"{live_server.url}/tramites/{tramite.pk}/enviar-evaluacion/")
        page.click('form[method="post"] button[type="submit"].btn-primary')

        # Verificar que se creó la notificación para el especialista
        notif = Notificacion.objects.filter(
            usuario=especialista_user,
            tramite_id=tramite.pk
        ).first()
        
        assert notif is not None
        assert "cambiado de estado" in notif.mensaje
        assert "EN_EVAL_TECNICA" in notif.mensaje or "Evaluación Técnica" in notif.mensaje
