import pytest
from playwright.sync_api import Page, expect
from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import Vehiculo
from apps.configuracion.models import Carroceria, TipoServicio, CategoriaVehiculo
from apps.autorizaciones.models import Autorizacion
from apps.tramites.models import VehiculoTramite
from django.utils import timezone

@pytest.mark.django_db(transaction=True)
def test_flujo_tramite_incremento_flota(page: Page, live_server, admin_user, tmp_path):
    # Crear datos base necesarios
    cat_m2, _ = CategoriaVehiculo.objects.get_or_create(codigo="M2", defaults={"nombre": "Categoría M2"})
    tipo_v, _ = Carroceria.objects.get_or_create(nombre="Minivan", defaults={"descripcion": "Minivan", "codigo": "MINIVAN", "categoria": cat_m2})
    tipo_s, _ = TipoServicio.objects.get_or_create(nombre="REGULAR", defaults={"descripcion": "Servicio Regular"})
    empresa = EmpresaTransporte.objects.create(
        ruc="20123456789",
        razon_social="Empresa Test",
        domicilio_fiscal="Direccion Test",
        representante_legal="Representante Test",
        dni_representante="12345678"
    )
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion="RES-EXISTENTE-001",
        fecha_resolucion=timezone.now().date(),
        fecha_inicio_vigencia=timezone.now().date(),
        fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=365),
        ambito="MADRE_DE_DIOS",
        tipo_servicio=tipo_s,
        estado="VIGENTE"
    )

    # Login
    page.goto(f"{live_server.url}/usuarios/login/")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    
    # 1. Crear Trámite (Mesa de Partes) - Paso 1
    page.goto(f"{live_server.url}/tramites/crear/")
    page.select_option('select[name="tipo_tramite"]', "INCREMENTO_FLOTA")
    page.select_option('select[name="empresa"]', str(empresa.id))
    page.select_option('select[name="autorizacion"]', str(autorizacion.id))
    page.fill('textarea[name="descripcion_solicitud"]', "Solicitud de incremento de flota para prueba E2E")
    page.locator('main form button[type="submit"]').click()
    
    # Paso 2: Datos del vehículo
    page.fill('input[name="vehiculos-0-placa"]', "NEW-123")
    page.fill('input[name="vehiculos-0-marca"]', "Toyota")
    page.fill('input[name="vehiculos-0-modelo"]', "Hiace")
    page.fill('input[name="vehiculos-0-anio_fabricacion"]', "2022")
    page.fill('input[name="vehiculos-0-capacidad_sentados"]', "15")
    page.select_option('select[name="vehiculos-0-categoria"]', str(cat_m2.id))
    page.select_option('select[name="vehiculos-0-carroceria"]', str(tipo_v.id))
    page.fill('input[name="conductores-0-dni"]', "12345670")
    page.fill('input[name="conductores-0-nombres"]', "Juan")
    page.fill('input[name="conductores-0-apellido_paterno"]', "Perez")
    page.fill('input[name="conductores-0-apellido_materno"]', "Ramos")
    page.fill('input[name="conductores-0-fecha_nacimiento"]', "1990-01-01")
    page.fill('input[name="conductores-0-licencia_numero"]', "Q12345670")
    page.select_option('select[name="conductores-0-licencia_categoria"]', "AII-B")
    page.fill('input[name="conductores-0-licencia_fecha_emision"]', "2024-01-01")
    page.fill('input[name="conductores-0-licencia_fecha_vencimiento"]', "2029-01-01")
    page.locator('main form button[type="submit"]').click()
    
    # Obtener ID del trámite desde la URL (ahora debería estar en el detalle)
    # URL: /tramites/123/
    tramite_id = page.url.split('/')[-2]
    
    # 2. Enviar a Evaluación Técnica
    page.goto(f"{live_server.url}/tramites/{tramite_id}/")
    page.click('a:has-text("Enviar a Evaluación")')
    page.locator('main form button[type="submit"]').click()
    
    # Esperar a que cambie el estado
    expect(page.locator("body")).to_contain_text("Evaluación Técnica")
    
    # Recargar para asegurar que los botones se actualicen
    page.reload()

    # 3. Aprobar Evaluación Técnica y derivar a Dirección Administrativa
    # Usar navegación directa para evitar problemas con selectores
    page.goto(f"{live_server.url}/tramites/{tramite_id}/aprobar-evaluacion/")
    page.locator('main form button[type="submit"]').click()
    
    # 4. Director Administrativo deriva a Director General
    page.goto(f"{live_server.url}/tramites/{tramite_id}/enviar-direccion-general/")
    page.locator('main form button[type="submit"]').click()

    # 5. Director General deriva a Revisión Legal
    page.goto(f"{live_server.url}/tramites/{tramite_id}/enviar-legal/")
    page.locator('main form button[type="submit"]').click()
    
    # 6. Aprobar Revisión Legal y devolver a Director General
    page.goto(f"{live_server.url}/tramites/{tramite_id}/aprobar-legal/")
    page.locator('main form button[type="submit"]').click()
    
    # 7. Aprobar Trámite (Dirección General) con resolución
    resolucion_pdf = tmp_path / "resolucion.pdf"
    resolucion_pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
    page.goto(f"{live_server.url}/tramites/{tramite_id}/aprobar/")
    page.fill('input[name="numero_resolucion"]', "RES-001-2025")
    page.fill('input[name="fecha_resolucion"]', "2025-01-01")
    page.set_input_files('input[name="archivo_resolucion"]', str(resolucion_pdf))
    page.locator('main form button[type="submit"]').click()
    
    # 8. Control de Calidad registra TUC y cierra el trámite
    # Verificar estado aprobado
    expect(page.locator("body")).to_contain_text("Aprobado")
    page.goto(f"{live_server.url}/tramites/{tramite_id}/cerrar/")
    page.fill('input[name$="-numero_tuc"]', "TUC-123456")
    page.fill('input[name$="-fecha_expedicion_tuc"]', "2025-01-01")
    page.fill('input[name$="-fecha_autorizacion_transportista"]', "2025-01-01")
    page.fill('input[name$="-fecha_expiracion_transportista"]', "2026-01-01")
    page.locator('main form button[type="submit"]').click()
    
    # Verificar que el vehículo ahora tiene la habilitación y el TUC
    vehiculo = Vehiculo.objects.get(placa="NEW123")
    page.goto(f"{live_server.url}/vehiculos/{vehiculo.id}/")
    expect(page.locator("body")).to_contain_text("TUC-123456")
    expect(page.locator("body")).to_contain_text("HABILITADO")
