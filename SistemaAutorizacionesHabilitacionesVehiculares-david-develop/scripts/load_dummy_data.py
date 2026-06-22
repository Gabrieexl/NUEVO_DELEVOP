import os
import sys
import django
from django.utils import timezone
from datetime import timedelta, date

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.autorizaciones.models import Autorizacion
from apps.configuracion.models import Carroceria, TipoServicio
from apps.usuarios.models import Usuario
from utils.constants import EstadoEmpresa, EstadoVehiculo, EstadoConductor, EstadoAutorizacion, EstadoHabilitacion, CategoriaLicencia

def load_dummy_data():
    print("🚀 Iniciando carga de datos de prueba...")

    # Obtener usuario admin
    try:
        admin_user = Usuario.objects.get(username='admin')
    except Usuario.DoesNotExist:
        print("❌ Error: Usuario 'admin' no encontrado. Ejecuta init_db.py primero.")
        return

    # 1. Crear Empresas
    print("\n🏢 Creando empresas...")
    empresas_data = [
        {
            'ruc': '20123456789',
            'razon_social': 'TRANSPORTES EL VELOZ S.A.C.',
            'nombre_comercial': 'EL VELOZ',
            'domicilio_fiscal': 'AV. LOS INCAS 123, TAMBOPATA',
            'representante_legal': 'JUAN PEREZ',
            'dni_representante': '12345678',
            'provincia': 'TAMBOPATA',
            'distrito': 'TAMBOPATA',
            'telefono': '987654321',
            'email': 'contacto@elveloz.com'
        },
        {
            'ruc': '20987654321',
            'razon_social': 'EMPRESA DE TRANSPORTE TURISTICO SELVA VERDE E.I.R.L.',
            'nombre_comercial': 'SELVA VERDE',
            'domicilio_fiscal': 'JR. LEON DE VIVERO 456, TAMBOPATA',
            'representante_legal': 'MARIA LOPEZ',
            'dni_representante': '87654321',
            'provincia': 'TAMBOPATA',
            'distrito': 'TAMBOPATA',
            'telefono': '912345678',
            'email': 'info@selvaverde.com'
        }
    ]

    empresas = []
    for data in empresas_data:
        empresa, created = EmpresaTransporte.objects.get_or_create(
            ruc=data['ruc'],
            defaults={
                'razon_social': data['razon_social'],
                'nombre_comercial': data['nombre_comercial'],
                'domicilio_fiscal': data['domicilio_fiscal'],
                'representante_legal': data['representante_legal'],
                'dni_representante': data['dni_representante'],
                'provincia': data['provincia'],
                'distrito': data['distrito'],
                'telefono': data['telefono'],
                'email': data['email'],
                'estado': EstadoEmpresa.ACTIVA,
                'creado_por': admin_user
            }
        )
        empresas.append(empresa)
        if created:
            print(f"✅ Empresa creada: {empresa.razon_social}")
        else:
            print(f"ℹ️ Empresa ya existe: {empresa.razon_social}")

    # 2. Crear Autorizaciones
    print("\n📜 Creando autorizaciones...")
    tipo_servicio_regular = TipoServicio.objects.filter(codigo='REGULAR').first()
    tipo_servicio_turistico = TipoServicio.objects.filter(codigo='TURISTICO').first()

    if not tipo_servicio_regular or not tipo_servicio_turistico:
        print("❌ Error: Tipos de servicio no encontrados. Ejecuta init_db.py primero.")
        return

    autorizaciones_data = [
        {
            'empresa': empresas[0],
            'numero_resolucion': 'RD-001-2024-DRTC-MDD',
            'fecha_resolucion': date(2024, 1, 15),
            'fecha_inicio': date(2024, 1, 15),
            'fecha_fin': date(2034, 1, 14),
            'tipo_servicio': tipo_servicio_regular,
            'rutas': 'PUERTO MALDONADO - IBERIA - IÑAPARI'
        },
        {
            'empresa': empresas[1],
            'numero_resolucion': 'RD-002-2024-DRTC-MDD',
            'fecha_resolucion': date(2024, 2, 20),
            'fecha_inicio': date(2024, 2, 20),
            'fecha_fin': date(2034, 2, 19),
            'tipo_servicio': tipo_servicio_turistico,
            'rutas': 'CIRCUITO TURISTICO TAMBOPATA'
        }
    ]

    autorizaciones = []
    for data in autorizaciones_data:
        auth, created = Autorizacion.objects.get_or_create(
            numero_resolucion=data['numero_resolucion'],
            defaults={
                'empresa': data['empresa'],
                'fecha_resolucion': data['fecha_resolucion'],
                'fecha_inicio_vigencia': data['fecha_inicio'],
                'fecha_fin_vigencia': data['fecha_fin'],
                'tipo_servicio': data['tipo_servicio'],
                'descripcion_rutas': data['rutas'],
                'estado': EstadoAutorizacion.VIGENTE,
                'creado_por': admin_user
            }
        )
        autorizaciones.append(auth)
        if created:
            print(f"✅ Autorización creada: {auth.numero_resolucion}")
        else:
            print(f"ℹ️ Autorización ya existe: {auth.numero_resolucion}")

    # 3. Crear Vehículos y Habilitaciones
    print("\n🚌 Creando vehículos y habilitaciones...")
    tipo_m3 = Carroceria.objects.filter(codigo='M3').first()
    tipo_m2 = Carroceria.objects.filter(codigo='M2').first()

    vehiculos_data = [
        {
            'placa': 'X1A-999',
            'empresa': empresas[0],
            'marca': 'TOYOTA',
            'modelo': 'COASTER',
            'anio': 2020,
            'tipo': tipo_m3,
            'capacidad': 25,
            'autorizacion': autorizaciones[0],
            'tuc': 'TUC-001-2024'
        },
        {
            'placa': 'Z2B-888',
            'empresa': empresas[0],
            'marca': 'MITSUBISHI',
            'modelo': 'ROSA',
            'anio': 2021,
            'tipo': tipo_m3,
            'capacidad': 30,
            'autorizacion': autorizaciones[0],
            'tuc': 'TUC-002-2024'
        },
        {
            'placa': 'V3C-777',
            'empresa': empresas[1],
            'marca': 'HYUNDAI',
            'modelo': 'H1',
            'anio': 2022,
            'tipo': tipo_m2,
            'capacidad': 12,
            'autorizacion': autorizaciones[1],
            'tuc': 'TUC-003-2024'
        }
    ]

    for data in vehiculos_data:
        vehiculo, created = Vehiculo.objects.get_or_create(
            placa=data['placa'],
            defaults={
                'empresa_propietaria': data['empresa'],
                'marca': data['marca'],
                'modelo': data['modelo'],
                'anio_fabricacion': data['anio'],
                'carroceria': data['tipo'],
                'capacidad_sentados': data['capacidad'],
                'estado': EstadoVehiculo.HABILITADO,
                'numero_tiv': f"TIV-{data['placa']}",
                'fecha_venc_soat': date(2025, 12, 31),
                'fecha_venc_citv': date(2025, 12, 31),
                'creado_por': admin_user,
                'autorizacion_principal': data['autorizacion']
            }
        )
        if created:
            print(f"✅ Vehículo creado: {vehiculo.placa}")
            
            # Crear Habilitación Vehicular
            HabilitacionVehicular.objects.create(
                vehiculo=vehiculo,
                autorizacion=data['autorizacion'],
                fecha_inicio=data['autorizacion'].fecha_inicio_vigencia,
                estado=EstadoHabilitacion.VIGENTE,
                numero_tuc=data['tuc'],
                fecha_expedicion_tuc=date(2024, 1, 20),
                creado_por=admin_user
            )
            print(f"   ✅ Habilitación creada con TUC: {data['tuc']}")
        else:
            print(f"ℹ️ Vehículo ya existe: {vehiculo.placa}")

    # 4. Crear Conductores y Habilitaciones
    print("\n👨‍✈️ Creando conductores y habilitaciones...")
    conductores_data = [
        {
            'dni': '40000001',
            'nombres': 'CARLOS',
            'apellidos': 'QUISPE MAMANI',
            'empresa': empresas[0],
            'licencia': 'Q40000001',
            'cat': CategoriaLicencia.AIII_C,
            'autorizacion': autorizaciones[0]
        },
        {
            'dni': '40000002',
            'nombres': 'MIGUEL',
            'apellidos': 'FLORES ROJAS',
            'empresa': empresas[0],
            'licencia': 'Q40000002',
            'cat': CategoriaLicencia.AIII_A,
            'autorizacion': autorizaciones[0]
        },
        {
            'dni': '40000003',
            'nombres': 'JORGE',
            'apellidos': 'SOTO DIAZ',
            'empresa': empresas[1],
            'licencia': 'Q40000003',
            'cat': CategoriaLicencia.AII_B,
            'autorizacion': autorizaciones[1]
        }
    ]

    for data in conductores_data:
        ap_paterno = data['apellidos'].split()[0]
        ap_materno = data['apellidos'].split()[1] if len(data['apellidos'].split()) > 1 else ''
        
        conductor, created = Conductor.objects.get_or_create(
            dni=data['dni'],
            defaults={
                'empresa': data['empresa'],
                'nombres': data['nombres'],
                'apellido_paterno': ap_paterno,
                'apellido_materno': ap_materno,
                'fecha_nacimiento': date(1980, 5, 15),
                'licencia_numero': data['licencia'],
                'licencia_categoria': data['cat'],
                'licencia_fecha_emision': date(2020, 1, 1),
                'licencia_fecha_vencimiento': date(2025, 1, 1),
                'estado': EstadoConductor.ACTIVO,
                'creado_por': admin_user,
                'telefono': '900000000',
                'email': f"conductor{data['dni']}@mail.com",
                'direccion': 'AV. CIRCUNVALACION 100'
            }
        )
        
        if created:
            print(f"✅ Conductor creado: {conductor.nombres} {conductor.apellido_paterno}")
            
            # Crear Habilitación Conductor
            HabilitacionConductor.objects.create(
                conductor=conductor,
                empresa=data['empresa'],
                autorizacion=data['autorizacion'],
                fecha_inicio=date(2024, 1, 20),
                estado=EstadoHabilitacion.VIGENTE,
                creado_por=admin_user
            )
            print(f"   ✅ Habilitación de conductor creada")
        else:
            print(f"ℹ️ Conductor ya existe: {conductor.dni}")

    print("\n✨ ¡Carga de datos de prueba completada! ✨")

if __name__ == '__main__':
    load_dummy_data()
