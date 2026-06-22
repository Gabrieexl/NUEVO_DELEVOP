"""
Factories para tests de usuarios.
"""

import factory
from django.contrib.auth import get_user_model

from utils.constants import Roles

Usuario = get_user_model()


class UsuarioFactory(factory.django.DjangoModelFactory):
    """Factory para crear usuarios de prueba."""
    
    class Meta:
        model = Usuario
        skip_postgeneration_save = True
    
    username = factory.Sequence(lambda n: f'usuario{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    dni = factory.Sequence(lambda n: f'{10000000 + n}')
    first_name = factory.Faker('first_name', locale='es')
    last_name = factory.Faker('last_name', locale='es')
    rol = Roles.CONSULTA_INTERNA
    is_active = True
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or 'testpass123'
        self.set_password(password)
        if create:
            self.save()


class AdminUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios administradores."""
    rol = Roles.ADMIN_SISTEMA
    is_staff = True
    is_superuser = True


class MesaPartesUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios de Mesa de Partes."""
    rol = Roles.MESA_PARTES


class EspecialistaUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios Especialistas Técnicos."""
    rol = Roles.ESPECIALISTA_TECNICO


class LegalUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios de Asesoría Legal."""
    rol = Roles.ASESORIA_LEGAL


class DirectorUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios Directores."""
    rol = Roles.DIRECTOR_GENERAL


class ConsultaInspectorUsuarioFactory(UsuarioFactory):
    """Factory para crear usuarios de Consulta Inspector."""
    rol = Roles.CONSULTA_INSPECTOR
