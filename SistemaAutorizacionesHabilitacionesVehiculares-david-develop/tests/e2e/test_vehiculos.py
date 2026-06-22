import pytest
from playwright.sync_api import Page, expect

from apps.configuracion.models import Carroceria, CategoriaVehiculo
from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from apps.configuracion.models import TipoServicio
from django.utils import timezone

@pytest.mark.django_db
def test_crud_vehiculo(page: Page, live_server, admin_user):
    # Crear datos necesarios
    cat_m2 = CategoriaVehiculo.objects.create(codigo="M2", nombre="Categoría M2")
    tipo = Carroceria.objects.create(codigo="MINIVAN", nombre="Minivan", descripcion="Minivan", categoria=cat_m2)
    empresa = EmpresaTransporte.objects.create(
        ruc="20123456789",
        razon_social="Empresa Propietaria",
        domicilio_fiscal="Direccion",
        representante_legal="Representante",
        dni_representante="12345678"
    )
    
    tipo_servicio = TipoServicio.objects.create(nombre="REGULAR", codigo="REGULAR")
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion="RES-001-2025",
        fecha_resolucion=timezone.now().date(),
        fecha_inicio_vigencia=timezone.now().date(),
        fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=365),
        tipo_servicio=tipo_servicio,
        estado="VIGENTE"
    )

    # Login
    page.goto(f"{live_server.url}/usuarios/login/")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    
    # Ir a lista de vehículos
    page.goto(f"{live_server.url}/vehiculos/")
    expect(page.locator("h5").first).to_contain_text("Lista de Vehículos")
    
    # Crear vehículo
    page.click('a:has-text("Nuevo Vehículo")')
    page.fill('input[name="placa"]', "ABC-123")
    page.select_option('select[name="empresa_propietaria"]', str(empresa.id))
    
    # Esperar a que se carguen las autorizaciones (AJAX)
    page.wait_for_timeout(1000) # Pequeña espera para AJAX
    page.select_option('select[name="autorizacion_principal"]', str(autorizacion.id))
    
    page.fill('input[name="marca"]', "Toyota")
    page.fill('input[name="modelo"]', "Hiace")
    page.fill('input[name="anio_fabricacion"]', "2020")
    page.fill('input[name="capacidad_sentados"]', "15")
    page.select_option('select[name="carroceria"]', str(tipo.id))
    
    # Ingresar TUC
    page.fill('input[name="numero_tuc"]', "TUC-001")
    
    page.locator('main form button[type="submit"]').click()
    
    # Verificar creación
    expect(page.locator("body")).to_contain_text("ABC123")
    expect(page.locator("body")).to_contain_text("Toyota")
    
    # Verificar TUC en detalle
    page.click('a[title="Ver detalle"]')
    expect(page.locator("body")).to_contain_text("TUC-001")
    
    # Editar vehículo
    page.click('a:has-text("Editar")')
    page.fill('input[name="modelo"]', "Hiace Pro")
    page.fill('input[name="numero_tuc"]', "TUC-002")
    page.locator('main form button[type="submit"]').click()
    
    # Verificar edición
    expect(page.locator("body")).to_contain_text("Hiace Pro")
    expect(page.locator("body")).to_contain_text("TUC-002")
