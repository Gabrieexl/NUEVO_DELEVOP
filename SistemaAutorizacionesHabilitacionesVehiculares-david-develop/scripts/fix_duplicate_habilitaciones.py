import os
import sys
import django
from django.db.models import Count

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.conductores.models import HabilitacionConductor
from utils.constants import EstadoHabilitacion

def fix_duplicates():
    print("Buscando habilitaciones de conductor duplicadas...")
    
    # Agrupar por campos clave para encontrar duplicados
    duplicates = HabilitacionConductor.objects.values(
        'conductor', 'empresa', 'autorizacion', 'estado'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1, estado=EstadoHabilitacion.VIGENTE)

    total_duplicates = 0
    
    for dup in duplicates:
        conductor_id = dup['conductor']
        empresa_id = dup['empresa']
        autorizacion_id = dup['autorizacion']
        
        # Obtener los registros duplicados
        records = HabilitacionConductor.objects.filter(
            conductor_id=conductor_id,
            empresa_id=empresa_id,
            autorizacion_id=autorizacion_id,
            estado=EstadoHabilitacion.VIGENTE
        ).order_by('fecha_inicio', 'id')
        
        print(f"\nEncontrados {records.count()} registros para Conductor ID {conductor_id}, Empresa ID {empresa_id}")
        
        # Mantener el primero (o el más antiguo/reciente según lógica)
        # En este caso, mantenemos el primero creado (menor ID) o el que tenga fecha inicio más antigua
        original = records.first()
        copies = records.exclude(id=original.id)
        
        print(f"Manteniendo original ID: {original.id} (Fecha: {original.fecha_inicio})")
        
        for copy in copies:
            print(f"Eliminando duplicado ID: {copy.id} (Fecha: {copy.fecha_inicio})")
            copy.delete()
            total_duplicates += 1

    print(f"\nTotal de duplicados eliminados: {total_duplicates}")

if __name__ == '__main__':
    fix_duplicates()
