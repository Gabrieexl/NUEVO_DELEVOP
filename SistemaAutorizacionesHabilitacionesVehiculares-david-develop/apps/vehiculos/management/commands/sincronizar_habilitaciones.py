"""
Comando para sincronizar habilitaciones de vehículos y conductores existentes.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.autorizaciones.models import Autorizacion
from utils.constants import EstadoVehiculo, EstadoHabilitacion


class Command(BaseCommand):
    help = 'Sincroniza las habilitaciones de vehículos y conductores existentes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--solo-vehiculos',
            action='store_true',
            help='Solo sincronizar vehículos'
        )
        parser.add_argument(
            '--solo-conductores',
            action='store_true',
            help='Solo sincronizar conductores'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin hacer cambios'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        solo_vehiculos = options['solo_vehiculos']
        solo_conductores = options['solo_conductores']
        
        hoy = timezone.now().date()
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== MODO DRY-RUN (no se harán cambios) ===\n'))
        
        if not solo_conductores:
            self.sincronizar_vehiculos(hoy, dry_run)
        
        if not solo_vehiculos:
            self.sincronizar_conductores(hoy, dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Sincronizacion completada'))
    
    def sincronizar_vehiculos(self, hoy, dry_run):
        """Sincroniza habilitaciones de vehículos."""
        self.stdout.write(self.style.HTTP_INFO('\n=== Sincronizando Vehículos ==='))
        
        # Buscar vehículos HABILITADOS con autorización pero sin HabilitacionVehicular
        vehiculos_habilitados = Vehiculo.objects.filter(
            estado=EstadoVehiculo.HABILITADO,
            autorizacion_principal__isnull=False
        ).select_related('autorizacion_principal', 'empresa_propietaria')
        
        creadas = 0
        ya_existentes = 0
        
        for vehiculo in vehiculos_habilitados:
            # Verificar si ya tiene habilitación vigente
            existe = HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                autorizacion=vehiculo.autorizacion_principal,
                estado=EstadoHabilitacion.VIGENTE
            ).exists()
            
            if existe:
                ya_existentes += 1
                continue
            
            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] Crearía habilitación para: {vehiculo.placa} '
                    f'-> {vehiculo.autorizacion_principal.numero_resolucion}'
                )
            else:
                HabilitacionVehicular.objects.create(
                    vehiculo=vehiculo,
                    autorizacion=vehiculo.autorizacion_principal,
                    fecha_inicio=hoy,
                    estado=EstadoHabilitacion.VIGENTE,
                    motivo='Habilitación creada por sincronización automática'
                )
                self.stdout.write(
                    f'  [OK] Habilitacion creada: {vehiculo.placa} '
                    f'-> {vehiculo.autorizacion_principal.numero_resolucion}'
                )
            creadas += 1
        
        self.stdout.write(
            f'\n  Resumen vehículos: {creadas} habilitaciones {"a crear" if dry_run else "creadas"}, '
            f'{ya_existentes} ya existían'
        )
    
    def sincronizar_conductores(self, hoy, dry_run):
        """Sincroniza habilitaciones de conductores."""
        self.stdout.write(self.style.HTTP_INFO('\n=== Sincronizando Conductores ==='))
        
        # Buscar conductores ACTIVOS con empresa
        conductores_activos = Conductor.objects.filter(
            estado='ACTIVO',
            empresa__isnull=False
        ).select_related('empresa')
        
        creadas = 0
        ya_existentes = 0
        
        for conductor in conductores_activos:
            # Buscar autorizaciones vigentes de la empresa
            autorizaciones = Autorizacion.objects.filter(
                empresa=conductor.empresa,
                estado='VIGENTE'
            )
            
            for autorizacion in autorizaciones:
                # Verificar si ya tiene habilitación vigente para esta autorización
                existe = HabilitacionConductor.objects.filter(
                    conductor=conductor,
                    empresa=conductor.empresa,
                    autorizacion=autorizacion,
                    estado=EstadoHabilitacion.VIGENTE
                ).exists()
                
                if existe:
                    ya_existentes += 1
                    continue
                
                if dry_run:
                    self.stdout.write(
                        f'  [DRY-RUN] Crearía habilitación para: {conductor.nombre_completo} '
                        f'-> {autorizacion.numero_resolucion}'
                    )
                else:
                    HabilitacionConductor.objects.create(
                        conductor=conductor,
                        empresa=conductor.empresa,
                        autorizacion=autorizacion,
                        fecha_inicio=hoy,
                        estado=EstadoHabilitacion.VIGENTE,
                        motivo='Habilitación creada por sincronización automática'
                    )
                    self.stdout.write(
                        f'  [OK] Habilitacion creada: {conductor.nombre_completo} '
                        f'-> {autorizacion.numero_resolucion}'
                    )
                creadas += 1
        
        self.stdout.write(
            f'\n  Resumen conductores: {creadas} habilitaciones {"a crear" if dry_run else "creadas"}, '
            f'{ya_existentes} ya existían'
        )
