import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.usuarios.models import Usuario
from utils.constants import Roles

def fix_admin_role():
    try:
        admin = Usuario.objects.get(username='admin')
        if admin.rol != Roles.ADMIN_SISTEMA:
            print(f"Actualizando rol de admin: {admin.rol} -> {Roles.ADMIN_SISTEMA}")
            admin.rol = Roles.ADMIN_SISTEMA
            admin.save()
            print("✅ Rol actualizado correctamente.")
        else:
            print("ℹ️ El usuario admin ya tiene el rol correcto.")
    except Usuario.DoesNotExist:
        print("❌ Usuario admin no encontrado.")

if __name__ == '__main__':
    fix_admin_role()
