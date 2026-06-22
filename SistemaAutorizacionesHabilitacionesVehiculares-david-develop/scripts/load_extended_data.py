import os
import sys
import django
from django.utils import timezone
from datetime import timedelta, date
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.autorizaciones.models import Autorizacion
from apps.configuracion.models import Carroceria, TipoServicio, Ruta
from apps.usuarios.models import Usuario
from apps.tramites.models import Tramite
from utils.constants import (
    EstadoEmpresa, EstadoVehiculo, EstadoConductor, EstadoAutorizacion, 
    EstadoHabilitacion, CategoriaLicencia, TipoTramite, EstadoTramite
)

def load_extended_data():
    print("🚀 Iniciando carga de datos extendidos...")

    # Obtener usuario admin
    try:
        admin_user = Usuario.objects.get(username='admin')
    except Usuario.DoesNotExist:
        print("❌ Error: Usuario 'admin' no encontrado. Ejecuta init_db.py primero.")
        return

    # 1. Crear Rutas
    print("\n🛣️ Creando rutas (Madre de Dios)...")
    rutas_data = [
        {
            'codigo': 'R-001',
            'nombre': 'RUTA INTEROCEANICA NORTE',
            'origen': 'PUERTO MALDONADO',
            'destino': 'IÑAPARI',
            'puntos': 'EL TRIUNFO, PLANCHON, ALEGRIA, MAVILA, IBERIA, ALERTA',
            'distancia': 220.0,
            'tiempo': 240
        },
        {
            'codigo': 'R-002',
            'nombre': 'RUTA INTEROCEANICA SUR',
            'origen': 'PUERTO MALDONADO',
            'destino': 'MAZUKO',
            'puntos': 'SANTA ROSA, UNION PROGRESO, LOROMAYO',
            'distancia': 180.0,
            'tiempo': 180
        },
        {
            'codigo': 'R-003',
            'nombre': 'RUTA FLUVIAL LABERINTO',
            'origen': 'PUERTO MALDONADO',
            'destino': 'PUERTO LABERINTO',
            'puntos': 'LA JOYA, EL PRADO',
            'distancia': 60.0,
            'tiempo': 60
        },
        {
            'codigo': 'R-004',
            'nombre': 'RUTA MINERA HUEPETUHE',
            'origen': 'PUERTO MALDONADO',
            'destino': 'HUEPETUHE',
            'puntos': 'MAZUKO, PUENTE INAMBARI, CHOQUE',
            'distancia': 210.0,
            'tiempo': 300
        },
        {
            'codigo': 'R-005',
            'nombre': 'RUTA MANU',
            'origen': 'PUERTO MALDONADO',
            'destino': 'SALVACION',
            'puntos': 'SANTA ROSA, BOCA COLORADO, PILCOPATA',
            'distancia': 250.0,
            'tiempo': 360
        }
    ]

    rutas = []
    for data in rutas_data:
        ruta, created = Ruta.objects.update_or_create(
            codigo=data['codigo'],
            defaults={
                'nombre': data['nombre'],
                'origen': data['origen'],
                'destino': data['destino'],
                'puntos_intermedios': data['puntos'],
                'distancia_km': data['distancia'],
                'tiempo_estimado_minutos': data['tiempo'],
                'creado_por': admin_user
            }
        )
        rutas.append(ruta)
        if created:
            print(f"✅ Ruta creada: {ruta.nombre}")
        else:
            print(f"🔄 Ruta actualizada: {ruta.nombre}")

    # 2. Crear Más Empresas
    print("\n🏢 Creando más empresas...")
    empresas_extra = [
        {
            'ruc': '20555555551',
            'razon_social': 'TRANSPORTES RAPIDOS DEL SUR S.A.C.',
            'nombre_comercial': 'RAPIDOS DEL SUR',
            'domicilio': 'AV. MADRE DE DIOS 500',
            'rep': 'CARLOS GOMEZ',
            'dni': '09876543'
        },
        {
            'ruc': '20666666662',
            'razon_social': 'TURISMO AMAZONICO E.I.R.L.',
            'nombre_comercial': 'TURISMO AMAZONICO',
            'domicilio': 'JR. CUSCO 200',
            'rep': 'ANA TORRES',
            'dni': '11223344'
        },
        {
            'ruc': '20777777773',
            'razon_social': 'COOPERATIVA DE TRANSPORTES TAMBOPATA',
            'nombre_comercial': 'COOP. TAMBOPATA',
            'domicilio': 'AV. FITZCARRALD 800',
            'rep': 'LUIS DIAZ',
            'dni': '55667788'
        }
    ]

    empresas = list(EmpresaTransporte.objects.all())
    for data in empresas_extra:
        empresa, created = EmpresaTransporte.objects.get_or_create(
            ruc=data['ruc'],
            defaults={
                'razon_social': data['razon_social'],
                'nombre_comercial': data['nombre_comercial'],
                'domicilio_fiscal': data['domicilio'],
                'representante_legal': data['rep'],
                'dni_representante': data['dni'],
                'provincia': 'TAMBOPATA',
                'distrito': 'TAMBOPATA',
                'estado': EstadoEmpresa.ACTIVA,
                'creado_por': admin_user
            }
        )
        if created:
            empresas.append(empresa)
            print(f"✅ Empresa creada: {empresa.razon_social}")

    # 3. Crear Más Vehículos
    print("\n🚌 Creando más vehículos...")
    tipos = list(Carroceria.objects.all())
    marcas = ['TOYOTA', 'HYUNDAI', 'MITSUBISHI', 'NISSAN', 'MERCEDES-BENZ']
    modelos = ['HIACE', 'H1', 'ROSA', 'URVAN', 'SPRINTER']
    
    for i in range(10):
        # Generar placa sin guiones para evitar problemas con get_or_create y la normalización del modelo
        placa = f"ABC{100+i}"
        empresa = random.choice(empresas)
        tipo = random.choice(tipos)
        
        vehiculo, created = Vehiculo.objects.get_or_create(
            placa=placa,
            defaults={
                'empresa_propietaria': empresa,
                'marca': random.choice(marcas),
                'modelo': random.choice(modelos),
                'anio_fabricacion': random.randint(2015, 2023),
                'carroceria': tipo,
                'capacidad_sentados': random.randint(10, 40),
                'estado': EstadoVehiculo.HABILITADO,
                'numero_tiv': f"TIV-{placa}",
                'fecha_venc_soat': date(2025, 12, 31),
                'fecha_venc_citv': date(2025, 12, 31),
                'creado_por': admin_user
            }
        )
        if created:
            print(f"✅ Vehículo creado: {vehiculo.placa} ({empresa.nombre_comercial})")
        else:
            print(f"ℹ️ Vehículo ya existe: {vehiculo.placa}")

    # 4. Crear Más Conductores
    print("\n👨‍✈️ Creando más conductores...")
    nombres = ['JUAN', 'PEDRO', 'LUIS', 'JOSE', 'CARLOS', 'MIGUEL', 'ANGEL', 'VICTOR']
    apellidos = ['PEREZ', 'GOMEZ', 'TORRES', 'DIAZ', 'ROJAS', 'QUISPE', 'MAMANI', 'FLORES']
    categorias = [CategoriaLicencia.AII_A, CategoriaLicencia.AII_B, CategoriaLicencia.AIII_A, CategoriaLicencia.AIII_B, CategoriaLicencia.AIII_C]

    for i in range(10):
        dni = f"450000{i:02d}"
        empresa = random.choice(empresas)
        
        conductor, created = Conductor.objects.get_or_create(
            dni=dni,
            defaults={
                'empresa': empresa,
                'nombres': random.choice(nombres),
                'apellido_paterno': random.choice(apellidos),
                'apellido_materno': random.choice(apellidos),
                'fecha_nacimiento': date(1985, 1, 1),
                'licencia_numero': f"Q{dni}",
                'licencia_categoria': random.choice(categorias),
                'licencia_fecha_emision': date(2020, 1, 1),
                'licencia_fecha_vencimiento': date(2025, 1, 1),
                'estado': EstadoConductor.ACTIVO,
                'creado_por': admin_user,
                'telefono': '987654321',
                'email': f"cond{dni}@mail.com",
                'direccion': 'AV. PRINCIPAL 123'
            }
        )
        if created:
            print(f"✅ Conductor creado: {conductor.nombres} {conductor.apellido_paterno}")

    # 5. Crear Trámites de Ejemplo
    print("\npaperwork Creando trámites de ejemplo...")
    tipos_tramite = [
        TipoTramite.AUTORIZACION_INICIAL,
        TipoTramite.INCREMENTO_FLOTA,
        TipoTramite.HABILITACION_CONDUCTOR,
        TipoTramite.MODIFICACION_AUTORIZACION
    ]
    
    estados_tramite = [
        EstadoTramite.RECIBIDO,
        EstadoTramite.EN_EVAL_TECNICA,
        EstadoTramite.EN_REVISION_LEGAL,
        EstadoTramite.PENDIENTE_FIRMA,
        EstadoTramite.APROBADO
    ]

    for i in range(15):
        empresa = random.choice(empresas)
        tipo = random.choice(tipos_tramite)
        estado = random.choice(estados_tramite)
        
        # Generar expediente manual para evitar conflictos si la logica automatica falla en script
        expediente = f"EXP-2024-{1000+i}"
        
        tramite, created = Tramite.objects.get_or_create(
            numero_expediente=expediente,
            defaults={
                'tipo_tramite': tipo,
                'estado': estado,
                'empresa': empresa,
                'descripcion_solicitud': f"Solicitud de {tipo} para la empresa {empresa.razon_social}",
                'creado_por': admin_user,
                'fecha_creacion': timezone.now() - timedelta(days=random.randint(1, 30))
            }
        )
        if created:
            print(f"✅ Trámite creado: {tramite.numero_expediente} ({tramite.get_estado_display()})")

    print("\n✨ ¡Carga de datos extendidos completada! ✨")

if __name__ == '__main__':
    load_extended_data()
