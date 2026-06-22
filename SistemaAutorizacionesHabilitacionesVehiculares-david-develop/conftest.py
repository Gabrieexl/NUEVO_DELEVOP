"""
Configuración global de pytest para el proyecto.
"""

import os
import pytest
from django.contrib.auth import get_user_model

# Permitir operaciones síncronas de Django en contextos asíncronos (necesario para Playwright)
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture
def user_password():
    """Password común para usuarios de prueba."""
    return 'testpass123'


@pytest.fixture
def admin_user(db, user_password):
    """Usuario administrador de prueba."""
    User = get_user_model()
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password=user_password,
        dni='12345678',
        rol='ADMIN_SISTEMA',
        is_staff=True,
        is_superuser=True,
    )
    return user


@pytest.fixture
def mesa_partes_user(db, user_password):
    """Usuario de Mesa de Partes de prueba."""
    User = get_user_model()
    user = User.objects.create_user(
        username='mesapartes',
        email='mesapartes@test.com',
        password=user_password,
        dni='23456789',
        rol='MESA_PARTES',
    )
    return user


@pytest.fixture
def especialista_user(db, user_password):
    """Usuario Especialista Técnico de prueba."""
    User = get_user_model()
    user = User.objects.create_user(
        username='especialista',
        email='especialista@test.com',
        password=user_password,
        dni='34567890',
        rol='ESPECIALISTA_TECNICO',
    )
    return user


@pytest.fixture
def legal_user(db, user_password):
    """Usuario Asesoría Legal de prueba."""
    User = get_user_model()
    user = User.objects.create_user(
        username='legal',
        email='legal@test.com',
        password=user_password,
        dni='45678901',
        rol='ASESORIA_LEGAL',
    )
    return user


@pytest.fixture
def director_user(db, user_password):
    """Usuario Director General de prueba."""
    User = get_user_model()
    user = User.objects.create_user(
        username='director',
        email='director@test.com',
        password=user_password,
        dni='56789012',
        rol='DIRECTOR_GENERAL',
    )
    return user


@pytest.fixture
def api_client():
    """Cliente REST Framework para pruebas de API."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, admin_user, user_password):
    """Cliente API autenticado como admin."""
    api_client.login(username=admin_user.username, password=user_password)
    return api_client
