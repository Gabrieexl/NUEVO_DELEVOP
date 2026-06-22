import pytest
from playwright.sync_api import Page, expect

@pytest.mark.django_db
def test_crud_empresa(page: Page, live_server, admin_user):
    # Login
    page.goto(f"{live_server.url}/usuarios/login/")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "testpass123")
    page.click('button[type="submit"]')
    
    # Ir a lista de empresas
    page.goto(f"{live_server.url}/empresas/")
    expect(page.locator("h2").first).to_contain_text("Empresas")
    
    # Crear empresa
    page.click('a:has-text("Nueva Empresa")')
    page.fill('input[name="ruc"]', "20123456789")
    page.fill('input[name="razon_social"]', "Transportes Test S.A.C.")
    page.fill('input[name="domicilio_fiscal"]', "Av. Test 123")
    page.fill('input[name="representante_legal"]', "Juan Perez")
    page.fill('input[name="dni_representante"]', "12345678")
    page.locator('main form button[type="submit"]').click()
    
    # Verificar creación
    expect(page.locator("body")).to_contain_text("Transportes Test S.A.C.")
    expect(page.locator("body")).to_contain_text("20123456789")
    
    # Editar empresa
    page.click('a[title="Ver"]')
    page.click('a:has-text("Editar")')
    page.fill('input[name="razon_social"]', "Transportes Test Editado S.A.C.")
    page.locator('main form button[type="submit"]').click()
    
    # Verificar edición
    expect(page.locator("body")).to_contain_text("Transportes Test Editado S.A.C.")
