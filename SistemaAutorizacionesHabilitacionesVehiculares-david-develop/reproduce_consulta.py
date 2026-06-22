import os
import django
import sys

# Configurar entorno Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.vehiculos.models import Vehiculo
from apps.configuracion.models import TipoVehiculo
from apps.empresas.models import EmpresaTransporte
from apps.consultas.services import ConsultaPlacaService

def test_consulta():
    print("--- INICIANDO TEST DE CONSULTA ---")
    
    # 1. Crear datos de prueba
    empresa, _ = EmpresaTransporte.objects.get_or_create(
        ruc="20999999999",
        defaults={"razon_social": "EMPRESA TEST", "estado": "ACTIVA"}
    )
    
    tipo, _ = TipoVehiculo.objects.get_or_create(
        nombre="AUTO",
        defaults={"codigo": "AUTO_TEST"}
    )
    
    placa_db = "ABC999"
    vehiculo, created = Vehiculo.objects.get_or_create(
        placa=placa_db,
        defaults={
            "empresa_propietaria": empresa,
            "marca": "TOYOTA",
            "modelo": "COROLLA",
            "anio_fabricacion": 2020,
            "capacidad_sentados": 4,
            "tipo_vehiculo": tipo,
            "estado": "HABILITADO"
        }
    )
    print(f"Vehículo en DB: '{vehiculo.placa}'")
    
    # 2. Probar servicio con diferentes formatos
    placas_a_probar = ["ABC999", "ABC-999", "abc-999", "abc 999"]
    
    for p in placas_a_probar:
        print(f"\nConsultando: '{p}'")
        # Simular la limpieza del form
        placa_limpia = p.replace('-', '').replace(' ', '').upper()
        print(f"Placa limpia: '{placa_limpia}'")
        
        resultado = ConsultaPlacaService.consultar_placa(placa_limpia)
        if resultado:
            print("✅ ENCONTRADO")
        else:
            print("❌ NO ENCONTRADO")

if __name__ == '__main__':
    test_consulta()
