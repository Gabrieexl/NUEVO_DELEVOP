import os
import django
import sys
from datetime import date, timedelta

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.tramites.models import Tramite, DatosTramite
from apps.tramites.services import TramiteProcesador
from utils.constants import (
    TipoTramite, EstadoTramite, EstadoAutorizacion, 
    EstadoHabilitacion, EstadoVehiculo, EstadoConductor
)

User = get_user_model()

def get_or_create_admin():
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("Creando usuario admin temporal...")
        user = User.objects.create_superuser('admin_test', 'admin@test.com', 'admin123')
    return user

def limpiar_datos_prueba():
    print("Limpiando datos de prueba anteriores...")
    rucs_prueba = ['20123456789', '20987654321', '20555555555']
    empresas = EmpresaTransporte.objects.filter(ruc__in=rucs_prueba)
    
    for empresa in empresas:
        print(f"Eliminando datos de empresa {empresa.ruc}...")
        # 1. Eliminar trámites y sus datos
        tramites = Tramite.objects.filter(empresa=empresa)
        DatosTramite.objects.filter(tramite__in=tramites).delete()
        # Eliminar relaciones en trámites antes de borrar trámites
        for t in tramites:
            t.vehiculos_tramite.all().delete()
            t.conductores_tramite.all().delete()
        tramites.delete()
        
        # 2. Eliminar habilitaciones
        HabilitacionVehicular.objects.filter(vehiculo__empresa_propietaria=empresa).delete()
        HabilitacionConductor.objects.filter(empresa=empresa).delete()
        
        # 3. Eliminar vehículos y conductores
        Vehiculo.objects.filter(empresa_propietaria=empresa).delete()
        Conductor.objects.filter(empresa=empresa).delete()
        
        # 4. Eliminar autorizaciones
        Autorizacion.objects.filter(empresa=empresa).delete()
        
        # 5. Finalmente la empresa
        empresa.delete()

def prueba_renovacion(usuario):
    print("\n--- PRUEBA 1: RENOVACIÓN DE AUTORIZACIÓN ---")
    
    # 1. Crear datos base
    empresa = EmpresaTransporte.objects.create(
        ruc='20123456789',
        razon_social='EMPRESA TEST RENOVACION S.A.C.',
        domicilio_fiscal='AV. TEST 123',
        representante_legal='JUAN PEREZ',
        dni_representante='12345678',
        creado_por=usuario
    )
    
    fecha_venc_original = date(2024, 12, 31)
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion='RES-001-2020',
        fecha_resolucion=date(2020, 1, 1),
        fecha_inicio_vigencia=date(2020, 1, 1),
        fecha_fin_vigencia=fecha_venc_original,
        estado=EstadoAutorizacion.VIGENTE,
        creado_por=usuario
    )
    print(f"Autorización creada. Vence: {autorizacion.fecha_fin_vigencia}")
    
    # 2. Crear Trámite de Renovación
    tramite = Tramite.objects.create(
        tipo_tramite=TipoTramite.RENOVACION_AUTORIZACION,
        empresa=empresa,
        autorizacion=autorizacion,
        descripcion_solicitud="Solicito renovación",
        estado=EstadoTramite.PENDIENTE_FIRMA, # Simulamos que ya llegó al final
        creado_por=usuario
    )
    
    nueva_fecha = date(2030, 12, 31)
    DatosTramite.objects.create(
        tramite=tramite,
        datos_json={
            'renovacion': {
                'nueva_fecha_fin_vigencia': nueva_fecha.isoformat()
            }
        }
    )
    
    # 3. Procesar Trámite (Simular Aprobación)
    print("Procesando trámite de renovación...")
    procesador = TramiteProcesador(tramite, usuario)
    resultado = procesador.procesar()
    
    # 4. Verificar
    autorizacion.refresh_from_db()
    print(f"Resultado procesador: {resultado['exito']} - {resultado['mensaje']}")
    print(f"Nueva fecha vencimiento: {autorizacion.fecha_fin_vigencia}")
    
    if autorizacion.fecha_fin_vigencia == nueva_fecha:
        print("✅ PRUEBA RENOVACIÓN: ÉXITO")
    else:
        print("❌ PRUEBA RENOVACIÓN: FALLÓ")

def prueba_suspension(usuario):
    print("\n--- PRUEBA 2: SUSPENSIÓN DE AUTORIZACIÓN ---")
    
    # 1. Crear datos base
    empresa = EmpresaTransporte.objects.create(
        ruc='20987654321',
        razon_social='EMPRESA TEST SUSPENSION S.A.C.',
        domicilio_fiscal='AV. TEST 456',
        representante_legal='MARIA LOPEZ',
        dni_representante='87654321',
        creado_por=usuario
    )
    
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion='RES-002-2021',
        fecha_resolucion=date(2021, 1, 1),
        fecha_inicio_vigencia=date(2021, 1, 1),
        fecha_fin_vigencia=date(2026, 12, 31),
        estado=EstadoAutorizacion.VIGENTE,
        creado_por=usuario
    )
    
    vehiculo = Vehiculo.objects.create(
        placa='SUS-001',
        empresa_propietaria=empresa,
        anio_fabricacion=2020,
        capacidad_sentados=15,
        estado=EstadoVehiculo.HABILITADO,
        creado_por=usuario
    )
    
    habilitacion = HabilitacionVehicular.objects.create(
        vehiculo=vehiculo,
        autorizacion=autorizacion,
        fecha_inicio=date(2021, 1, 1),
        estado=EstadoHabilitacion.VIGENTE,
        creado_por=usuario
    )
    
    print(f"Autorización estado inicial: {autorizacion.estado}")
    print(f"Habilitación estado inicial: {habilitacion.estado}")
    
    # 2. Crear Trámite de Suspensión
    tramite = Tramite.objects.create(
        tipo_tramite=TipoTramite.SUSPENSION_AUTORIZACION,
        empresa=empresa,
        autorizacion=autorizacion,
        descripcion_solicitud="Suspensión por sanción",
        estado=EstadoTramite.PENDIENTE_FIRMA,
        creado_por=usuario
    )
    
    DatosTramite.objects.create(
        tramite=tramite,
        datos_json={
            'suspension': {
                'motivo': 'Incumplimiento grave de normas'
            }
        }
    )
    
    # 3. Procesar
    print("Procesando trámite de suspensión...")
    procesador = TramiteProcesador(tramite, usuario)
    resultado = procesador.procesar()
    
    # 4. Verificar
    autorizacion.refresh_from_db()
    habilitacion.refresh_from_db()
    
    print(f"Autorización estado final: {autorizacion.estado}")
    print(f"Habilitación estado final: {habilitacion.estado}")
    
    if autorizacion.estado == EstadoAutorizacion.SUSPENDIDA and habilitacion.estado == EstadoHabilitacion.SUSPENDIDA:
        print("✅ PRUEBA SUSPENSIÓN: ÉXITO")
    else:
        print("❌ PRUEBA SUSPENSIÓN: FALLÓ")

def prueba_baja(usuario):
    print("\n--- PRUEBA 3: BAJA DE AUTORIZACIÓN ---")
    
    # 1. Crear datos base
    empresa = EmpresaTransporte.objects.create(
        ruc='20555555555',
        razon_social='EMPRESA TEST BAJA S.A.C.',
        domicilio_fiscal='AV. TEST 789',
        representante_legal='CARLOS RUIZ',
        dni_representante='55555555',
        creado_por=usuario
    )
    
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion='RES-003-2022',
        fecha_resolucion=date(2022, 1, 1),
        fecha_inicio_vigencia=date(2022, 1, 1),
        fecha_fin_vigencia=date(2027, 12, 31),
        estado=EstadoAutorizacion.VIGENTE,
        creado_por=usuario
    )
    
    vehiculo = Vehiculo.objects.create(
        placa='BAJ-001',
        empresa_propietaria=empresa,
        anio_fabricacion=2021,
        capacidad_sentados=20,
        estado=EstadoVehiculo.HABILITADO,
        autorizacion_principal=autorizacion,
        creado_por=usuario
    )
    
    habilitacion = HabilitacionVehicular.objects.create(
        vehiculo=vehiculo,
        autorizacion=autorizacion,
        fecha_inicio=date(2022, 1, 1),
        estado=EstadoHabilitacion.VIGENTE,
        creado_por=usuario
    )
    
    print(f"Autorización estado inicial: {autorizacion.estado}")
    print(f"Habilitación estado inicial: {habilitacion.estado}")
    
    # 2. Crear Trámite de Baja
    tramite = Tramite.objects.create(
        tipo_tramite=TipoTramite.BAJA_AUTORIZACION,
        empresa=empresa,
        autorizacion=autorizacion,
        descripcion_solicitud="Renuncia voluntaria",
        estado=EstadoTramite.PENDIENTE_FIRMA,
        creado_por=usuario
    )
    
    DatosTramite.objects.create(
        tramite=tramite,
        datos_json={
            'baja': {
                'motivo': 'Cese de actividades'
            }
        }
    )
    
    # 3. Procesar
    print("Procesando trámite de baja...")
    procesador = TramiteProcesador(tramite, usuario)
    resultado = procesador.procesar()
    
    # 4. Verificar
    autorizacion.refresh_from_db()
    habilitacion.refresh_from_db()
    vehiculo.refresh_from_db()
    
    print(f"Autorización estado final: {autorizacion.estado}")
    print(f"Habilitación estado final: {habilitacion.estado}")
    print(f"Vehículo estado final: {vehiculo.estado}")
    
    if (autorizacion.estado == EstadoAutorizacion.CANCELADA and 
        habilitacion.estado == EstadoHabilitacion.BAJA and
        vehiculo.estado == EstadoVehiculo.BAJA):
        print("✅ PRUEBA BAJA: ÉXITO")
    else:
        print("❌ PRUEBA BAJA: FALLÓ")

if __name__ == '__main__':
    try:
        limpiar_datos_prueba()
        usuario = get_or_create_admin()
        prueba_renovacion(usuario)
        prueba_suspension(usuario)
        prueba_baja(usuario)
        print("\n=== TODAS LAS PRUEBAS FINALIZADAS ===")
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
