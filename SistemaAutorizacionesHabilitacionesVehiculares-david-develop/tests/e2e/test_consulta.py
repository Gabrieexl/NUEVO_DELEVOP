import pytest
from playwright.sync_api import Page, expect
from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.configuracion.models import Carroceria, TipoServicio, CategoriaVehiculo
from apps.autorizaciones.models import Autorizacion
from django.utils import timezone

@pytest.mark.django_db
def test_consulta_publica_placa(page: Page, live_server):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    User.objects.create_superuser(username="admin", email="admin@test.com", password="testpass123")

    # Crear datos para la consulta
    cat_m3 = CategoriaVehiculo.objects.create(codigo="M3", nombre="Categoría M3")
    tipo_v = Carroceria.objects.create(codigo="BUS", nombre="Bus", descripcion="Bus", categoria=cat_m3)
    tipo_s = TipoServicio.objects.create(nombre="REGULAR", descripcion="Servicio Regular")
    empresa = EmpresaTransporte.objects.create(
        ruc="20987654321",
        razon_social="Transportes Consulta S.A.",
        domicilio_fiscal="Av. Consulta 456",
        representante_legal="Maria Lopez",
        dni_representante="87654321"
    )
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion="RES-2025-001",
        fecha_resolucion=timezone.now().date(),
        fecha_inicio_vigencia=timezone.now().date(),
        fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=365),
        ambito="MADRE_DE_DIOS",
        tipo_servicio=tipo_s,
        estado="VIGENTE"
    )
    vehiculo = Vehiculo.objects.create(
        placa="CON-123",
        empresa_propietaria=empresa,
        marca="Toyota",
        modelo="Coaster",
        anio_fabricacion=2021,
        capacidad_sentados=25,
        carroceria=tipo_v
    )
    HabilitacionVehicular.objects.create(
        vehiculo=vehiculo,
        autorizacion=autorizacion,
        fecha_inicio=timezone.now().date(),
        estado='VIGENTE',
        numero_tuc="TUC-CONSULTA-001"
    )

    # Login (ConsultaPlacaView requires login)
    page.goto(f"{live_server.url}/usuarios/login/")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    
    # Esperar a que cargue el dashboard
    expect(page.locator("body")).to_contain_text("Dashboard")

    # Ir a la página de consulta
    page.goto(f"{live_server.url}/consulta/placa/")
    expect(page.locator('input[name="placa"]')).to_be_visible()
    page.fill('input[name="placa"]', "CON-123")
    page.click('button:has-text("Consultar")')
    
    # Verificar resultados
    expect(page.locator("body")).to_contain_text("CON123")
    expect(page.locator("body")).to_contain_text("Transportes Consulta S.A.")
    expect(page.locator("body")).to_contain_text("TUC-CONSULTA-001")
    expect(page.locator("body")).to_contain_text("Vigente")
