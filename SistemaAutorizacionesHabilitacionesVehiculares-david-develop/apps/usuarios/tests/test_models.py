"""
Tests del modelo Usuario.
"""

import pytest
from django.contrib.auth import get_user_model

from utils.constants import Roles
from .factories import (
    UsuarioFactory, AdminUsuarioFactory, MesaPartesUsuarioFactory,
    EspecialistaUsuarioFactory, LegalUsuarioFactory, DirectorUsuarioFactory,
    ConsultaInspectorUsuarioFactory
)

Usuario = get_user_model()


@pytest.mark.django_db
class TestUsuarioModel:
    """Tests para el modelo Usuario."""
    
    def test_crear_usuario(self):
        """Test: Crear un usuario básico."""
        usuario = UsuarioFactory()
        assert usuario.pk is not None
        assert usuario.dni is not None
        assert len(usuario.dni) == 8
    
    def test_usuario_str(self):
        """Test: Representación string del usuario."""
        usuario = UsuarioFactory(
            first_name='Juan',
            last_name='Pérez',
            dni='12345678'
        )
        assert 'Juan Pérez' in str(usuario)
        assert '12345678' in str(usuario)
    
    def test_get_full_name(self):
        """Test: Obtener nombre completo."""
        usuario = UsuarioFactory(
            first_name='María',
            last_name='García'
        )
        assert usuario.get_full_name() == 'María García'
    
    def test_get_full_name_sin_nombre(self):
        """Test: Nombre completo cuando no hay nombre/apellido."""
        usuario = UsuarioFactory(
            first_name='',
            last_name='',
            username='testuser'
        )
        assert usuario.get_full_name() == 'testuser'
    
    def test_dni_unico(self):
        """Test: DNI debe ser único."""
        UsuarioFactory(dni='11111111')
        with pytest.raises(Exception):
            UsuarioFactory(dni='11111111')
    
    def test_rol_default(self):
        """Test: Rol por defecto es CONSULTA_INTERNA."""
        usuario = Usuario.objects.create_user(
            username='nuevo',
            password='testpass',
            dni='99999999'
        )
        assert usuario.rol == Roles.CONSULTA_INTERNA


@pytest.mark.django_db
class TestUsuarioPermisos:
    """Tests para los permisos basados en roles."""
    
    def test_es_admin(self):
        """Test: Verificar rol de administrador."""
        admin = AdminUsuarioFactory()
        normal = UsuarioFactory()
        
        assert admin.es_admin is True
        assert normal.es_admin is False
    
    def test_es_mesa_partes(self):
        """Test: Verificar rol de Mesa de Partes."""
        mesa = MesaPartesUsuarioFactory()
        otro = UsuarioFactory()
        
        assert mesa.es_mesa_partes is True
        assert otro.es_mesa_partes is False
    
    def test_es_especialista(self):
        """Test: Verificar rol de Especialista Técnico."""
        especialista = EspecialistaUsuarioFactory()
        otro = UsuarioFactory()
        
        assert especialista.es_especialista is True
        assert otro.es_especialista is False
    
    def test_es_legal(self):
        """Test: Verificar rol de Asesoría Legal."""
        legal = LegalUsuarioFactory()
        otro = UsuarioFactory()
        
        assert legal.es_legal is True
        assert otro.es_legal is False
    
    def test_es_director(self):
        """Test: Verificar rol de Director."""
        director = DirectorUsuarioFactory()
        otro = UsuarioFactory()
        
        assert director.es_director is True
        assert otro.es_director is False
    
    def test_puede_crear_tramites(self):
        """Test: Solo Admin y Mesa de Partes pueden crear trámites."""
        admin = AdminUsuarioFactory()
        mesa = MesaPartesUsuarioFactory()
        especialista = EspecialistaUsuarioFactory()
        
        assert admin.puede_crear_tramites is True
        assert mesa.puede_crear_tramites is True
        assert especialista.puede_crear_tramites is False
    
    def test_puede_evaluar_tecnicamente(self):
        """Test: Solo Admin y Especialista pueden evaluar técnicamente."""
        admin = AdminUsuarioFactory()
        especialista = EspecialistaUsuarioFactory()
        mesa = MesaPartesUsuarioFactory()
        
        assert admin.puede_evaluar_tecnicamente is True
        assert especialista.puede_evaluar_tecnicamente is True
        assert mesa.puede_evaluar_tecnicamente is False
    
    def test_puede_evaluar_legalmente(self):
        """Test: Solo Admin y Legal pueden evaluar legalmente."""
        admin = AdminUsuarioFactory()
        legal = LegalUsuarioFactory()
        especialista = EspecialistaUsuarioFactory()
        
        assert admin.puede_evaluar_legalmente is True
        assert legal.puede_evaluar_legalmente is True
        assert especialista.puede_evaluar_legalmente is False
    
    def test_puede_firmar(self):
        """Test: Solo Admin y Director pueden firmar."""
        admin = AdminUsuarioFactory()
        director = DirectorUsuarioFactory()
        legal = LegalUsuarioFactory()
        
        assert admin.puede_firmar is True
        assert director.puede_firmar is True
        assert legal.puede_firmar is False
    
    def test_solo_lectura(self):
        """Test: Consulta Interna y SUTRAN son solo lectura."""
        consulta = UsuarioFactory(rol=Roles.CONSULTA_INTERNA)
        sutran = ConsultaInspectorUsuarioFactory()
        especialista = EspecialistaUsuarioFactory()
        
        assert consulta.solo_lectura is True
        assert sutran.solo_lectura is True
        assert especialista.solo_lectura is False


@pytest.mark.django_db
class TestUsuarioAutenticacion:
    """Tests para autenticación de usuarios."""
    
    def test_login_correcto(self, client):
        """Test: Login con credenciales correctas."""
        usuario = UsuarioFactory(password='mipassword123')
        
        response = client.post('/usuarios/login/', {
            'username': usuario.username,
            'password': 'mipassword123'
        })
        
        # Debería redirigir al dashboard
        assert response.status_code == 302
        assert response.url == '/usuarios/dashboard/'
    
    def test_login_incorrecto(self, client):
        """Test: Login con credenciales incorrectas."""
        usuario = UsuarioFactory(password='mipassword123')
        
        response = client.post('/usuarios/login/', {
            'username': usuario.username,
            'password': 'passwordincorrecto'
        })
        
        # No debería redirigir (error en formulario)
        assert response.status_code == 200
    
    def test_logout(self, client):
        """Test: Cerrar sesión."""
        usuario = UsuarioFactory()
        client.force_login(usuario)
        
        response = client.post('/usuarios/logout/')
        
        assert response.status_code == 302
