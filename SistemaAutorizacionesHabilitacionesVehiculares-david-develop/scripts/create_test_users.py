import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.usuarios.models import Usuario
from utils.constants import Roles
from django.contrib.auth.models import Group

def create_test_users():
    print("🚀 Creando usuarios de prueba para cada rol...")
    
    users_data = [
        {
            'username': 'mesa_partes',
            'email': 'mesa@drtc.gob.pe',
            'password': 'password123',
            'rol': Roles.MESA_PARTES,
            'first_name': 'Maria',
            'last_name': 'Mesa',
            'dni': '10000001',
            'cargo': 'Recepcionista'
        },
        {
            'username': 'especialista',
            'email': 'tecnico@drtc.gob.pe',
            'password': 'password123',
            'rol': Roles.ESPECIALISTA_TECNICO,
            'first_name': 'Juan',
            'last_name': 'Tecnico',
            'dni': '10000002',
            'cargo': 'Ingeniero de Transportes'
        },
        {
            'username': 'legal',
            'email': 'legal@drtc.gob.pe',
            'password': 'password123',
            'rol': Roles.ASESORIA_LEGAL,
            'first_name': 'Ana',
            'last_name': 'Legal',
            'dni': '10000003',
            'cargo': 'Abogada'
        },
        {
            'username': 'director',
            'email': 'director@drtc.gob.pe',
            'password': 'password123',
            'rol': Roles.DIRECTOR_GENERAL,
            'first_name': 'Carlos',
            'last_name': 'Director',
            'dni': '10000004',
            'cargo': 'Director Regional'
        },
        {
            'username': 'consulta',
            'email': 'consulta@drtc.gob.pe',
            'password': 'password123',
            'rol': Roles.CONSULTA_INTERNA,
            'first_name': 'Pedro',
            'last_name': 'Consulta',
            'dni': '10000005',
            'cargo': 'Inspector'
        },
        {
            'username': 'inspector',
            'email': 'inspector@drtc.gob.pe',
            'password': 'password123',
            'rol': Roles.CONSULTA_INSPECTOR,
            'first_name': 'Inspector',
            'last_name': 'General',
            'dni': '10000006',
            'cargo': 'Fiscalizador'
        }
    ]

    for data in users_data:
        user, created = Usuario.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'rol': data['rol'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'dni': data['dni'],
                'cargo': data['cargo'],
                'area': 'Dirección de Circulación Terrestre'
            }
        )
        
        if created:
            user.set_password(data['password'])
            user.save()
            
            # Asignar grupo si existe
            group, _ = Group.objects.get_or_create(name=data['rol'])
            user.groups.add(group)
            
            print(f"✅ Usuario creado: {data['username']} (Rol: {data['rol']})")
        else:
            # Asegurar que la contraseña sea la correcta aunque el usuario ya exista
            user.set_password(data['password'])
            user.rol = data['rol'] # Asegurar rol correcto
            user.save()
            print(f"ℹ️ Usuario actualizado: {data['username']}")

    print("\n✨ ¡Usuarios de prueba creados exitosamente! ✨")
    print("------------------------------------------------")
    print("🔑 Contraseña para todos: password123")
    print("------------------------------------------------")
    for u in users_data:
        print(f"👤 {u['username']:<15} - {u['rol']}")

if __name__ == '__main__':
    create_test_users()
