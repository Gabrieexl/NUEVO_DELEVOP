import pytest
from playwright.sync_api import Page, expect

def test_login_page_loads(page: Page, live_server):
    """
    Verifica que la página de login carga correctamente.
    """
    page.goto(f"{live_server.url}/usuarios/login/")
    
    # Verificar título o contenido
    # Ajusta el título esperado según tu template base
    expect(page).to_have_title("Iniciar Sesión - DRTC")
    
    # Verificar campos del formulario
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()

def test_login_failure(page: Page, live_server):
    """
    Verifica que el login falla con credenciales incorrectas.
    """
    page.goto(f"{live_server.url}/usuarios/login/")
    
    page.fill("input[name='username']", "usuario_inexistente")
    page.fill("input[name='password']", "password_incorrecto")
    page.click("button[type='submit']")
    
    # Verificar mensaje de error
    # Ajusta el selector según cómo muestras los errores (alert, toast, etc.)
    # Por defecto Django suele mostrar errores en una lista o alerta
    expect(page.locator("text=Usuario o contraseña incorrectos")).to_be_visible()

def test_login_success(page: Page, live_server, admin_user, user_password):
    """
    Verifica que el login funciona con credenciales correctas.
    """
    page.goto(f"{live_server.url}/usuarios/login/")
    
    page.fill("input[name='username']", admin_user.username)
    page.fill("input[name='password']", user_password)
    page.click("button[type='submit']")
    
    # Verificar redirección al dashboard
    # Ajusta la URL o el contenido esperado del dashboard
    expect(page).to_have_url(f"{live_server.url}/usuarios/dashboard/")
    
    # Verificar mensaje de éxito (alerta)
    expect(page.locator(".alert-success")).to_contain_text("Bienvenido")
    
    # O verificar elemento del dashboard
    # expect(page.locator("h1")).to_contain_text("Dashboard")
