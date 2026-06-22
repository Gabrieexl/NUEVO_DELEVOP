import pytest
from playwright.sync_api import Page, expect
from apps.empresas.models import EmpresaTransporte
from apps.conductores.models import Conductor
from django.utils import timezone

@pytest.mark.django_db
def test_crud_conductor(page: Page, live_server, admin_user):
    # Crear empresa para asociar
    empresa = EmpresaTransporte.objects.create(
        ruc="20123456789",
        razon_social="Empresa Test Conductores",
        domicilio_fiscal="Av. Test 123",
        representante_legal="Juan Perez",
        dni_representante="12345678",
        email="empresa@test.com",
        telefono="987654321"
    )

    # Login
    page.goto(f"{live_server.url}/usuarios/login/")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    
    # 1. Crear Conductor
    page.goto(f"{live_server.url}/conductores/crear/")
    
    # Llenar formulario
    page.select_option('#id_empresa', str(empresa.id))
    page.fill('#id_dni', "87654321")
    page.fill('#id_nombres', "Conductor Test")
    page.fill('#id_apellido_paterno', "ApellidoP")
    page.fill('#id_apellido_materno', "ApellidoM")
    page.fill('#id_fecha_nacimiento', "1990-01-01")
    page.fill('#id_licencia_numero', "Q87654321")
    page.select_option('#id_licencia_categoria', "AIII-C")
    page.fill('#id_licencia_fecha_emision', "2020-01-01")
    page.fill('#id_licencia_fecha_vencimiento', "2025-01-01")
    page.fill('#id_telefono', "999888777")
    
    page.click('button.btn-primary[type="submit"]')
    
    # Verificar redirección y mensaje
    expect(page.locator("body")).to_contain_text("Conductor registrado exitosamente")
    expect(page.locator("body")).to_contain_text("Conductor Test")
    
    # 2. Editar Conductor
    # Buscar el ID del conductor creado
    conductor = Conductor.objects.get(dni="87654321")
    page.goto(f"{live_server.url}/conductores/{conductor.id}/editar/")
    
    page.fill('#id_nombres', "Conductor Editado")
    page.click('button.btn-primary[type="submit"]')
    
    expect(page.locator("body")).to_contain_text("Conductor actualizado exitosamente")
    expect(page.locator("body")).to_contain_text("Conductor Editado")
    
    # 3. Listar Conductores
    page.goto(f"{live_server.url}/conductores/")
    expect(page.locator("body")).to_contain_text("Conductor Editado")
    expect(page.locator("body")).to_contain_text("87654321")
