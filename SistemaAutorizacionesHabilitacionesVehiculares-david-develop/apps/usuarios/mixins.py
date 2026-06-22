"""
Mixins de permisos para vistas basadas en roles.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

from utils.constants import Roles


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin base para requerir un rol específico.
    Sobrescribir `roles_permitidos` con una lista de roles aceptados.
    """
    roles_permitidos = []
    
    def test_func(self):
        """Verifica si el usuario tiene uno de los roles permitidos."""
        user = self.request.user
        if user.is_superuser:
            return True
        return user.rol in self.roles_permitidos
    
    def handle_no_permission(self):
        """Maneja el caso de acceso denegado."""
        if self.request.user.is_authenticated:
            messages.error(
                self.request, 
                'No tiene permisos para acceder a esta sección.'
            )
            return redirect('usuarios:dashboard')
        return super().handle_no_permission()


class AdminRequeridoMixin(RolRequeridoMixin):
    """Requiere rol de Administrador."""
    roles_permitidos = [Roles.ADMIN_SISTEMA]


class MesaPartesRequeridoMixin(RolRequeridoMixin):
    """Requiere rol de Mesa de Partes o superior."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.MESA_PARTES]


class EspecialistaRequeridoMixin(RolRequeridoMixin):
    """Requiere rol de Especialista Técnico o superior."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ESPECIALISTA_TECNICO]


class LegalRequeridoMixin(RolRequeridoMixin):
    """Requiere rol de Asesoría Legal o superior."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.ASESORIA_LEGAL]


class DirectorRequeridoMixin(RolRequeridoMixin):
    """Requiere rol de Director (General o Administrativo) o superior."""
    roles_permitidos = [Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO]


class ConsultaInternaRequeridoMixin(RolRequeridoMixin):
    """Requiere cualquier rol interno (excluye SUTRAN)."""
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
        Roles.CONSULTA_INTERNA,
    ]


class SoloLecturaExcluidoMixin(RolRequeridoMixin):
    """Excluye usuarios de solo lectura (pueden modificar datos)."""
    roles_permitidos = [
        Roles.ADMIN_SISTEMA,
        Roles.MESA_PARTES,
        Roles.ESPECIALISTA_TECNICO,
        Roles.ASESORIA_LEGAL,
        Roles.DIRECTOR_GENERAL,
        Roles.DIRECTOR_ADMINISTRATIVO,
    ]


# Decoradores para vistas basadas en funciones

def rol_requerido(roles_permitidos):
    """
    Decorador para requerir roles específicos en vistas de función.
    
    Uso:
        @rol_requerido([Roles.ADMIN_SISTEMA, Roles.MESA_PARTES])
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            
            if request.user.is_superuser or request.user.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'No tiene permisos para acceder a esta sección.')
            return redirect('usuarios:dashboard')
        
        return wrapper
    return decorator


def admin_requerido(view_func):
    """Decorador que requiere rol de administrador."""
    return rol_requerido([Roles.ADMIN_SISTEMA])(view_func)


def mesa_partes_requerido(view_func):
    """Decorador que requiere rol de Mesa de Partes."""
    return rol_requerido([Roles.ADMIN_SISTEMA, Roles.MESA_PARTES])(view_func)


def especialista_requerido(view_func):
    """Decorador que requiere rol de Especialista Técnico."""
    return rol_requerido([Roles.ADMIN_SISTEMA, Roles.ESPECIALISTA_TECNICO])(view_func)


def legal_requerido(view_func):
    """Decorador que requiere rol de Asesoría Legal."""
    return rol_requerido([Roles.ADMIN_SISTEMA, Roles.ASESORIA_LEGAL])(view_func)


def director_requerido(view_func):
    """Decorador que requiere rol de Director (General o Administrativo)."""
    return rol_requerido([Roles.ADMIN_SISTEMA, Roles.DIRECTOR_GENERAL, Roles.DIRECTOR_ADMINISTRATIVO])(view_func)
