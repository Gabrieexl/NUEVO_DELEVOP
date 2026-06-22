import os
import sys
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.configuracion.models import TipoVehiculo, TipoServicio, Ruta, Frecuencia
from apps.usuarios.models import Usuario
from django.contrib.auth.models import Group, Permission

def init_db():
    print("🚀 Iniciando configuración de base de datos...")

    # 1. Migraciones
    print("\n📦 Ejecutando migraciones...")
    call_command('migrate')
    print("✅ Migraciones completadas.")

    # 2. Crear Superusuario
    print("\n👤 Creando superusuario...")
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@drtc.gob.pe', 'admin123')
        print("✅ Superusuario creado: admin / admin123")
    else:
        print("ℹ️ El superusuario 'admin' ya existe.")

    # 3. Crear Grupos y Permisos Básicos
    print("\n👥 Configurando grupos y roles...")
    roles = ['MESA_PARTES', 'ESPECIALISTA_TECNICO', 'ASESORIA_LEGAL', 'DIRECTOR', 'CONSULTA_INTERNA']
    for rol in roles:
        Group.objects.get_or_create(name=rol)
    print(f"✅ Roles creados: {', '.join(roles)}")

    # 4. Datos Maestros - Tipos de Vehículo
    print("\n🚌 Creando tipos de vehículo...")
    tipos_vehiculo = [
        ('M1', 'Vehículo de hasta 8 asientos sin contar el conductor (Auto, Station Wagon)'),
        ('M2', 'Vehículo de más de 8 asientos, peso bruto <= 5 ton (Minivan, Combi)'),
        ('M3', 'Vehículo de más de 8 asientos, peso bruto > 5 ton (Omnibus, Bus)'),
    ]
    for codigo, desc in tipos_vehiculo:
        TipoVehiculo.objects.get_or_create(codigo=codigo, defaults={'nombre': codigo, 'descripcion': desc})
    print("✅ Tipos de vehículo creados.")

    # 5. Datos Maestros - Tipos de Servicio
    print("\n📋 Creando tipos de servicio...")
    tipos_servicio = [
        ('REGULAR', 'Servicio de Transporte Regular de Personas'),
        ('TURISTICO', 'Servicio de Transporte Turístico'),
        ('PERSONAL', 'Servicio de Transporte de Personal'),
        ('MERCANCIAS', 'Servicio de Transporte de Mercancías'),
    ]
    for codigo, desc in tipos_servicio:
        TipoServicio.objects.get_or_create(
            codigo=codigo, 
            defaults={
                'nombre': desc.split(' (')[0] if '(' in desc else desc, # Use description as name or part of it
                'descripcion': desc
            }
        )
    print("✅ Tipos de servicio creados.")

    print("\n✨ ¡Instalación completada con éxito! ✨")
    print("------------------------------------------------")
    print("🌐 Servidor: python manage.py runserver")
    print("🔑 Admin: admin / admin123")
    print("------------------------------------------------")

if __name__ == '__main__':
    init_db()
