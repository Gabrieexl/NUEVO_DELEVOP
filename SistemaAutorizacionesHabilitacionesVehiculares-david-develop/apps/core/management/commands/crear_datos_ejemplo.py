"""
Management command para crear datos de ejemplo completos.
Uso: python manage.py crear_datos_ejemplo
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.empresas.models import EmpresaTransporte
from apps.autorizaciones.models import Autorizacion
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.tramites.models import Tramite, HistorialTramite, VehiculoTramite, ConductorTramite
from apps.configuracion.models import TipoServicio, TipoVehiculo, Ruta, Frecuencia
from apps.usuarios.models import Usuario
from utils.constants import Roles

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de ejemplo completos para testing del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpia los datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando creación de datos de ejemplo...'))
        
        with transaction.atomic():
            if options['limpiar']:
                self._limpiar_datos()
            
            # Crear usuarios por rol
            usuarios = self._crear_usuarios()
            
            # Crear configuración base
            self._crear_configuracion()
            
            # Crear empresas
            empresas = self._crear_empresas(usuarios['admin'])
            
            # Crear autorizaciones
            autorizaciones = self._crear_autorizaciones(empresas, usuarios['admin'])
            
            # Crear vehículos
            vehiculos = self._crear_vehiculos(empresas, autorizaciones, usuarios['admin'])
            
            # Crear conductores
            conductores = self._crear_conductores(empresas, usuarios['admin'])
            
            # Crear habilitaciones vehiculares
            self._crear_habilitaciones_vehiculares(vehiculos, autorizaciones, usuarios['admin'])
            
            # Crear habilitaciones de conductores
            self._crear_habilitaciones_conductores(conductores, empresas, autorizaciones, usuarios['admin'])
            
            # Crear trámites en diferentes estados
            self._crear_tramites(empresas, autorizaciones, vehiculos, conductores, usuarios)
        
        self.stdout.write(self.style.SUCCESS('✅ Datos de ejemplo creados exitosamente!'))
        self._mostrar_resumen()

    def _limpiar_datos(self):
        """Limpia datos existentes (excepto superusuarios)."""
        self.stdout.write('Limpiando datos existentes...')
        
        # Limpiar en orden para respetar FKs
        HistorialTramite.objects.all().delete()
        VehiculoTramite.objects.all().delete()
        ConductorTramite.objects.all().delete()
        Tramite.objects.all().delete()
        HabilitacionConductor.objects.all().delete()
        HabilitacionVehicular.objects.all().delete()
        Conductor.objects.all().delete()
        Vehiculo.objects.all().delete()
        Autorizacion.objects.all().delete()
        EmpresaTransporte.objects.all().delete()
        Usuario.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.WARNING('  Datos limpiados'))

    def _crear_usuarios(self):
        """Crea usuarios de prueba por cada rol."""
        self.stdout.write('Creando usuarios...')
        
        usuarios = {}
        roles_data = [
            ('admin', 'ADMIN_SISTEMA', 'Administrador', 'Sistema'),
            ('mesa', 'MESA_PARTES', 'María', 'García'),
            ('tecnico', 'ESPECIALISTA_TECNICO', 'Carlos', 'López'),
            ('legal', 'ASESORIA_LEGAL', 'Ana', 'Rodríguez'),
            ('director', 'DIRECTOR', 'José', 'Martínez'),
            ('consulta', 'CONSULTA_INTERNA', 'Luis', 'Sánchez'),
            ('inspector', 'CONSULTA_INSPECTOR', 'Pedro', 'Ramírez'),
        ]
        
        for username, rol, nombre, apellido in roles_data:
            user, created = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@drtc-mdd.gob.pe',
                    'first_name': nombre,
                    'last_name': apellido,
                    'rol': rol,
                    'is_active': True,
                    'dni': f'{random.randint(10000000, 99999999)}',
                    'telefono': f'9{random.randint(10000000, 99999999)}',
                    'cargo': dict(Roles.CHOICES).get(rol, rol),
                }
            )
            if created:
                user.set_password('Demo2025!')
                user.save()
            usuarios[username] = user
            self.stdout.write(f'  Usuario: {username} ({rol})')
        
        return usuarios

    def _crear_configuracion(self):
        """Crea configuración base (rutas, frecuencias)."""
        self.stdout.write('Creando configuración...')
        
        # Rutas
        rutas_data = [
            ('R001', 'Puerto Maldonado - Laberinto', 'Puerto Maldonado', 'Laberinto', 85.0, 120),
            ('R002', 'Puerto Maldonado - Mazuko', 'Puerto Maldonado', 'Mazuko', 120.0, 180),
            ('R003', 'Puerto Maldonado - Salvación', 'Puerto Maldonado', 'Salvación', 160.0, 240),
            ('R004', 'Puerto Maldonado - Iberia', 'Puerto Maldonado', 'Iberia', 180.0, 270),
            ('R005', 'Puerto Maldonado - Iñapari', 'Puerto Maldonado', 'Iñapari', 235.0, 360),
            ('R006', 'Laberinto - Mazuko', 'Laberinto', 'Mazuko', 45.0, 60),
            ('R007', 'Puerto Maldonado - Tambopata', 'Puerto Maldonado', 'Tambopata', 30.0, 45),
            ('R008', 'Puerto Maldonado - Lago Sandoval', 'Puerto Maldonado', 'Lago Sandoval', 25.0, 40),
        ]
        
        for codigo, nombre, origen, destino, distancia, tiempo in rutas_data:
            Ruta.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre, 
                    'origen': origen,
                    'destino': destino,
                    'distancia_km': distancia,
                    'tiempo_estimado_minutos': tiempo,
                    'activo': True
                }
            )
        
        # Frecuencias
        from datetime import time as dt_time
        frecuencias_data = [
            ('F001', 'Diario 6:00 AM', 'Salida diaria a las 6:00 AM', dt_time(6, 0)),
            ('F002', 'Diario 10:00 AM', 'Salida diaria a las 10:00 AM', dt_time(10, 0)),
            ('F003', 'Diario 2:00 PM', 'Salida diaria a las 2:00 PM', dt_time(14, 0)),
            ('F004', 'Diario 6:00 PM', 'Salida diaria a las 6:00 PM', dt_time(18, 0)),
            ('F005', 'Inter-diario 8:00 AM', 'Lunes, Miércoles, Viernes a las 8:00 AM', dt_time(8, 0)),
            ('F006', 'Fines de semana 7:00 AM', 'Sábados y Domingos a las 7:00 AM', dt_time(7, 0)),
        ]
        
        for codigo, nombre, descripcion, hora in frecuencias_data:
            Frecuencia.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre, 
                    'descripcion': descripcion, 
                    'hora_salida': hora,
                    'activo': True
                }
            )
        
        self.stdout.write('  Rutas y frecuencias creadas')

    def _crear_empresas(self, usuario):
        """Crea empresas de transporte de ejemplo."""
        self.stdout.write('Creando empresas...')
        
        empresas_data = [
            {
                'ruc': '20450123456',
                'razon_social': 'TRANSPORTES MADRE DE DIOS S.A.C.',
                'nombre_comercial': 'Trans MDD',
                'domicilio_fiscal': 'Av. Fitzcarrald 456, Puerto Maldonado',
                'representante_legal': 'Juan Carlos Pérez Huamán',
                'dni_representante': '04512345',
                'telefono': '082-571234',
                'email': 'transmdd@gmail.com',
                'estado': 'ACTIVA',
            },
            {
                'ruc': '20450234567',
                'razon_social': 'EMPRESA DE TRANSPORTES TAMBOPATA E.I.R.L.',
                'nombre_comercial': 'Trans Tambopata',
                'domicilio_fiscal': 'Jr. Puno 789, Puerto Maldonado',
                'representante_legal': 'María Elena Quispe Mamani',
                'dni_representante': '04523456',
                'telefono': '082-572345',
                'email': 'transtambopata@gmail.com',
                'estado': 'ACTIVA',
            },
            {
                'ruc': '20450345678',
                'razon_social': 'TURISMO AMAZÓNICO S.R.L.',
                'nombre_comercial': 'Amazónico Tours',
                'domicilio_fiscal': 'Av. León Velarde 123, Puerto Maldonado',
                'representante_legal': 'Roberto Fernández Castro',
                'dni_representante': '04534567',
                'telefono': '082-573456',
                'email': 'amazonico.tours@gmail.com',
                'estado': 'ACTIVA',
            },
            {
                'ruc': '20450456789',
                'razon_social': 'TRANSPORTES INAMBARI S.A.',
                'nombre_comercial': 'Trans Inambari',
                'domicilio_fiscal': 'Av. Madre de Dios 321, Puerto Maldonado',
                'representante_legal': 'Carlos Alberto Ramos Silva',
                'dni_representante': '04545678',
                'telefono': '082-574567',
                'email': 'trans.inambari@gmail.com',
                'estado': 'ACTIVA',
            },
            {
                'ruc': '20450567890',
                'razon_social': 'SERVICIOS DE TRANSPORTE SELVA VERDE E.I.R.L.',
                'nombre_comercial': 'Selva Verde',
                'domicilio_fiscal': 'Jr. Cusco 567, Puerto Maldonado',
                'representante_legal': 'Ana María Torres Díaz',
                'dni_representante': '04556789',
                'telefono': '082-575678',
                'email': 'selvaverde.trans@gmail.com',
                'estado': 'INACTIVA',  # Una empresa inactiva para pruebas
            },
        ]
        
        empresas = []
        for data in empresas_data:
            empresa, created = EmpresaTransporte.objects.get_or_create(
                ruc=data['ruc'],
                defaults={**data, 'creado_por': usuario}
            )
            empresas.append(empresa)
            self.stdout.write(f'  Empresa: {empresa.nombre_comercial}')
        
        return empresas

    def _crear_autorizaciones(self, empresas, usuario):
        """Crea autorizaciones para las empresas."""
        self.stdout.write('Creando autorizaciones...')
        
        tipo_regular = TipoServicio.objects.get(codigo='REGULAR')
        tipo_turistico = TipoServicio.objects.get(codigo='TURISTICO')
        tipo_trabajadores = TipoServicio.objects.get(codigo='TRABAJADORES')
        
        rutas = list(Ruta.objects.filter(activo=True))
        frecuencias = list(Frecuencia.objects.filter(activo=True))
        
        autorizaciones_data = [
            # Trans MDD - Autorización vigente
            {
                'empresa': empresas[0],
                'numero_resolucion': '001-2023-GR-MDD/DRTC',
                'fecha_resolucion': date(2023, 1, 15),
                'fecha_inicio_vigencia': date(2023, 2, 1),
                'fecha_fin_vigencia': date(2028, 1, 31),
                'ambito': 'MADRE_DE_DIOS',
                'tipo_servicio': tipo_regular,
                'estado': 'VIGENTE',
                'descripcion_rutas': 'Puerto Maldonado - Laberinto - Mazuko',
            },
            # Trans Tambopata - Autorización vigente
            {
                'empresa': empresas[1],
                'numero_resolucion': '015-2022-GR-MDD/DRTC',
                'fecha_resolucion': date(2022, 6, 20),
                'fecha_inicio_vigencia': date(2022, 7, 1),
                'fecha_fin_vigencia': date(2027, 6, 30),
                'ambito': 'MADRE_DE_DIOS',
                'tipo_servicio': tipo_regular,
                'estado': 'VIGENTE',
                'descripcion_rutas': 'Puerto Maldonado - Salvación - Iberia',
            },
            # Amazónico Tours - Autorización turística
            {
                'empresa': empresas[2],
                'numero_resolucion': '025-2024-GR-MDD/DRTC',
                'fecha_resolucion': date(2024, 3, 10),
                'fecha_inicio_vigencia': date(2024, 4, 1),
                'fecha_fin_vigencia': date(2029, 3, 31),
                'ambito': 'MADRE_DE_DIOS',
                'tipo_servicio': tipo_turistico,
                'estado': 'VIGENTE',
                'descripcion_rutas': 'Circuito turístico Tambopata - Lago Sandoval',
            },
            # Trans Inambari - Autorización vigente
            {
                'empresa': empresas[3],
                'numero_resolucion': '030-2021-GR-MDD/DRTC',
                'fecha_resolucion': date(2021, 9, 5),
                'fecha_inicio_vigencia': date(2021, 10, 1),
                'fecha_fin_vigencia': date(2026, 9, 30),
                'ambito': 'MADRE_DE_DIOS',
                'tipo_servicio': tipo_regular,
                'estado': 'VIGENTE',
                'descripcion_rutas': 'Puerto Maldonado - Iñapari (Frontera Brasil)',
            },
            # Selva Verde - Autorización suspendida
            {
                'empresa': empresas[4],
                'numero_resolucion': '008-2020-GR-MDD/DRTC',
                'fecha_resolucion': date(2020, 4, 15),
                'fecha_inicio_vigencia': date(2020, 5, 1),
                'fecha_fin_vigencia': date(2025, 4, 30),
                'ambito': 'MADRE_DE_DIOS',
                'tipo_servicio': tipo_trabajadores,
                'estado': 'SUSPENDIDA',
                'descripcion_rutas': 'Transporte de trabajadores mineros',
                'observaciones': 'Suspendida por incumplimiento de requisitos',
            },
        ]
        
        autorizaciones = []
        for data in autorizaciones_data:
            autorizacion, created = Autorizacion.objects.get_or_create(
                numero_resolucion=data['numero_resolucion'],
                defaults={**data, 'creado_por': usuario}
            )
            # Asignar rutas y frecuencias
            if created:
                autorizacion.rutas.set(random.sample(rutas, min(3, len(rutas))))
                autorizacion.frecuencias_asignadas.set(random.sample(frecuencias, min(2, len(frecuencias))))
            autorizaciones.append(autorizacion)
            self.stdout.write(f'  Autorización: {autorizacion.numero_resolucion}')
        
        return autorizaciones

    def _crear_vehiculos(self, empresas, autorizaciones, usuario):
        """Crea vehículos para las empresas."""
        self.stdout.write('Creando vehículos...')
        
        tipo_minivan = TipoVehiculo.objects.get(codigo='MINIVAN')
        tipo_van = TipoVehiculo.objects.get(codigo='VAN')
        tipo_bus = TipoVehiculo.objects.get(codigo='BUS')
        tipo_auto = TipoVehiculo.objects.get(codigo='AUTO')
        
        vehiculos_data = [
            # Trans MDD (empresas[0])
            {'placa': 'V1A-123', 'empresa': empresas[0], 'autorizacion': autorizaciones[0], 
             'marca': 'Toyota', 'modelo': 'Hiace', 'anio': 2022, 'capacidad': 15, 
             'tipo': tipo_van, 'estado': 'HABILITADO'},
            {'placa': 'V1B-456', 'empresa': empresas[0], 'autorizacion': autorizaciones[0],
             'marca': 'Hyundai', 'modelo': 'H1', 'anio': 2021, 'capacidad': 12,
             'tipo': tipo_van, 'estado': 'HABILITADO'},
            {'placa': 'V1C-789', 'empresa': empresas[0], 'autorizacion': autorizaciones[0],
             'marca': 'Mercedes', 'modelo': 'Sprinter', 'anio': 2020, 'capacidad': 16,
             'tipo': tipo_van, 'estado': 'BAJA'},
            
            # Trans Tambopata (empresas[1])
            {'placa': 'V2A-111', 'empresa': empresas[1], 'autorizacion': autorizaciones[1],
             'marca': 'Kia', 'modelo': 'Carnival', 'anio': 2023, 'capacidad': 11,
             'tipo': tipo_minivan, 'estado': 'HABILITADO'},
            {'placa': 'V2B-222', 'empresa': empresas[1], 'autorizacion': autorizaciones[1],
             'marca': 'Toyota', 'modelo': 'Hiace', 'anio': 2022, 'capacidad': 15,
             'tipo': tipo_van, 'estado': 'HABILITADO'},
            {'placa': 'V2C-333', 'empresa': empresas[1], 'autorizacion': autorizaciones[1],
             'marca': 'Nissan', 'modelo': 'Urvan', 'anio': 2021, 'capacidad': 15,
             'tipo': tipo_van, 'estado': 'PROPUESTO'},
            
            # Amazónico Tours (empresas[2])
            {'placa': 'V3A-444', 'empresa': empresas[2], 'autorizacion': autorizaciones[2],
             'marca': 'Toyota', 'modelo': 'Land Cruiser', 'anio': 2024, 'capacidad': 7,
             'tipo': tipo_minivan, 'estado': 'HABILITADO'},
            {'placa': 'V3B-555', 'empresa': empresas[2], 'autorizacion': autorizaciones[2],
             'marca': 'Ford', 'modelo': 'Transit', 'anio': 2023, 'capacidad': 15,
             'tipo': tipo_van, 'estado': 'HABILITADO'},
            
            # Trans Inambari (empresas[3])
            {'placa': 'V4A-666', 'empresa': empresas[3], 'autorizacion': autorizaciones[3],
             'marca': 'Mercedes', 'modelo': 'Sprinter', 'anio': 2022, 'capacidad': 19,
             'tipo': tipo_bus, 'estado': 'HABILITADO'},
            {'placa': 'V4B-777', 'empresa': empresas[3], 'autorizacion': autorizaciones[3],
             'marca': 'Volkswagen', 'modelo': 'Crafter', 'anio': 2021, 'capacidad': 16,
             'tipo': tipo_van, 'estado': 'HABILITADO'},
            {'placa': 'V4C-888', 'empresa': empresas[3], 'autorizacion': autorizaciones[3],
             'marca': 'Hyundai', 'modelo': 'County', 'anio': 2019, 'capacidad': 25,
             'tipo': tipo_bus, 'estado': 'NO_HABILITADO'},
            
            # Selva Verde (empresas[4]) - empresa inactiva
            {'placa': 'V5A-999', 'empresa': empresas[4], 'autorizacion': autorizaciones[4],
             'marca': 'Toyota', 'modelo': 'Hilux', 'anio': 2020, 'capacidad': 5,
             'tipo': tipo_auto, 'estado': 'BAJA'},
        ]
        
        vehiculos = []
        for data in vehiculos_data:
            vehiculo, created = Vehiculo.objects.get_or_create(
                placa=data['placa'],
                defaults={
                    'empresa_propietaria': data['empresa'],
                    'autorizacion_principal': data['autorizacion'],
                    'marca': data['marca'],
                    'modelo': data['modelo'],
                    'anio_fabricacion': data['anio'],
                    'capacidad_sentados': data['capacidad'],
                    'tipo_vehiculo': data['tipo'],
                    'estado': data['estado'],
                    'numero_tiv': f'TIV-{data["placa"].replace("-", "")}',
                    'fecha_venc_soat': date.today() + timedelta(days=random.randint(30, 365)),
                    'fecha_venc_citv': date.today() + timedelta(days=random.randint(30, 180)),
                    'creado_por': usuario,
                }
            )
            vehiculos.append(vehiculo)
            self.stdout.write(f'  Vehículo: {vehiculo.placa} ({vehiculo.marca} {vehiculo.modelo})')
        
        return vehiculos

    def _crear_conductores(self, empresas, usuario):
        """Crea conductores de ejemplo asociados a empresas."""
        self.stdout.write('Creando conductores...')
        
        # Solo usar empresas activas
        empresas_activas = [e for e in empresas if e.estado == 'ACTIVA']
        
        conductores_data = [
            {'dni': '04512001', 'nombres': 'Pedro', 'ap': 'Quispe', 'am': 'Mamani',
             'licencia': 'Q04512001', 'categoria': 'AIIB', 'estado': 'ACTIVO', 'empresa_idx': 0},
            {'dni': '04512002', 'nombres': 'Juan', 'ap': 'Huamán', 'am': 'Torres',
             'licencia': 'Q04512002', 'categoria': 'AIIB', 'estado': 'ACTIVO', 'empresa_idx': 0},
            {'dni': '04512003', 'nombres': 'Carlos', 'ap': 'Fernández', 'am': 'López',
             'licencia': 'Q04512003', 'categoria': 'AIIIA', 'estado': 'ACTIVO', 'empresa_idx': 1},
            {'dni': '04512004', 'nombres': 'Miguel', 'ap': 'Ramos', 'am': 'García',
             'licencia': 'Q04512004', 'categoria': 'AIIB', 'estado': 'ACTIVO', 'empresa_idx': 1},
            {'dni': '04512005', 'nombres': 'Luis', 'ap': 'Castro', 'am': 'Díaz',
             'licencia': 'Q04512005', 'categoria': 'AIIA', 'estado': 'ACTIVO', 'empresa_idx': 2},
            {'dni': '04512006', 'nombres': 'Roberto', 'ap': 'Silva', 'am': 'Mendoza',
             'licencia': 'Q04512006', 'categoria': 'AIIB', 'estado': 'ACTIVO', 'empresa_idx': 2},
            {'dni': '04512007', 'nombres': 'Jorge', 'ap': 'Vargas', 'am': 'Cruz',
             'licencia': 'Q04512007', 'categoria': 'AIIIA', 'estado': 'ACTIVO', 'empresa_idx': 3},
            {'dni': '04512008', 'nombres': 'Fernando', 'ap': 'Rojas', 'am': 'Paredes',
             'licencia': 'Q04512008', 'categoria': 'AIIB', 'estado': 'INACTIVO', 'empresa_idx': 3},
            {'dni': '04512009', 'nombres': 'Ricardo', 'ap': 'Paz', 'am': 'Soto',
             'licencia': 'Q04512009', 'categoria': 'AIIA', 'estado': 'ACTIVO', 'empresa_idx': 0},
            {'dni': '04512010', 'nombres': 'Andrés', 'ap': 'Flores', 'am': 'Rivera',
             'licencia': 'Q04512010', 'categoria': 'AIIB', 'estado': 'ACTIVO', 'empresa_idx': 1},
        ]
        
        conductores = []
        for data in conductores_data:
            empresa = empresas_activas[data['empresa_idx'] % len(empresas_activas)]
            conductor, created = Conductor.objects.get_or_create(
                dni=data['dni'],
                defaults={
                    'empresa': empresa,
                    'nombres': data['nombres'],
                    'apellido_paterno': data['ap'],
                    'apellido_materno': data['am'],
                    'fecha_nacimiento': date(1980 + random.randint(0, 20), 
                                            random.randint(1, 12), 
                                            random.randint(1, 28)),
                    'licencia_numero': data['licencia'],
                    'licencia_categoria': data['categoria'],
                    'licencia_fecha_emision': date.today() - timedelta(days=random.randint(365, 1095)),
                    'licencia_fecha_vencimiento': date.today() + timedelta(days=random.randint(180, 730)),
                    'estado': data['estado'],
                    'creado_por': usuario,
                }
            )
            conductores.append(conductor)
            self.stdout.write(f'  Conductor: {conductor.nombre_completo} ({empresa.nombre_comercial})')
        
        return conductores

    def _crear_habilitaciones_vehiculares(self, vehiculos, autorizaciones, usuario):
        """Crea habilitaciones vehiculares."""
        self.stdout.write('Creando habilitaciones vehiculares...')
        
        for vehiculo in vehiculos:
            if vehiculo.estado == 'HABILITADO':
                # Buscar autorización de la empresa
                autorizacion = vehiculo.autorizacion_principal
                if autorizacion:
                    hab, created = HabilitacionVehicular.objects.get_or_create(
                        vehiculo=vehiculo,
                        autorizacion=autorizacion,
                        estado='VIGENTE',
                        defaults={
                            'fecha_inicio': autorizacion.fecha_inicio_vigencia,
                            'motivo': 'Habilitación inicial',
                            'numero_tuc': f'TUC-{vehiculo.placa.replace("-", "")}-{random.randint(1000, 9999)}',
                            'fecha_expedicion_tuc': date.today() - timedelta(days=random.randint(30, 365)),
                            'fecha_autorizacion_transportista': autorizacion.fecha_resolucion,
                            'fecha_expiracion_transportista': autorizacion.fecha_fin_vigencia,
                            'creado_por': usuario,
                        }
                    )
                    if created:
                        self.stdout.write(f'  Habilitación: {vehiculo.placa} -> {autorizacion.numero_resolucion}')

    def _crear_habilitaciones_conductores(self, conductores, empresas, autorizaciones, usuario):
        """Crea habilitaciones de conductores."""
        self.stdout.write('Creando habilitaciones de conductores...')
        
        # Distribuir conductores entre empresas activas
        empresas_activas = [e for e in empresas if e.estado == 'ACTIVA']
        autorizaciones_vigentes = [a for a in autorizaciones if a.estado == 'VIGENTE']
        
        conductores_activos = [c for c in conductores if c.estado == 'ACTIVO']
        
        for i, conductor in enumerate(conductores_activos):
            empresa = empresas_activas[i % len(empresas_activas)]
            # Buscar autorización de esta empresa
            autorizacion = next((a for a in autorizaciones_vigentes if a.empresa == empresa), None)
            
            if autorizacion:
                hab, created = HabilitacionConductor.objects.get_or_create(
                    conductor=conductor,
                    empresa=empresa,
                    estado='VIGENTE',
                    defaults={
                        'autorizacion': autorizacion,
                        'fecha_inicio': autorizacion.fecha_inicio_vigencia,
                        'motivo': 'Habilitación inicial',
                        'creado_por': usuario,
                    }
                )
                if created:
                    self.stdout.write(f'  Habilitación: {conductor.nombre_completo} -> {empresa.nombre_comercial}')

    def _crear_tramites(self, empresas, autorizaciones, vehiculos, conductores, usuarios):
        """Crea trámites en diferentes estados."""
        self.stdout.write('Creando trámites...')
        
        # Trámite 1: Recibido (Mesa de partes) - Incremento de flota
        tramite1 = Tramite.objects.create(
            tipo_tramite='INCREMENTO_FLOTA',
            empresa=empresas[0],
            autorizacion=autorizaciones[0],
            descripcion_solicitud='Solicitud de incremento de 2 unidades vehiculares para la ruta Puerto Maldonado - Laberinto',
            estado='RECIBIDO',
            creado_por=usuarios['mesa'],
        )
        # Agregar vehículos nuevos al trámite
        VehiculoTramite.objects.create(
            tramite=tramite1,
            placa_nueva='V1D-001',
            marca='Toyota',
            modelo='Hiace Commuter',
            anio_fabricacion=2024,
            capacidad_pasajeros=15,
            tipo_vehiculo='VAN',
            estado_proceso='PENDIENTE',
        )
        VehiculoTramite.objects.create(
            tramite=tramite1,
            placa_nueva='V1E-002',
            marca='Hyundai',
            modelo='H-350',
            anio_fabricacion=2024,
            capacidad_pasajeros=16,
            tipo_vehiculo='VAN',
            estado_proceso='PENDIENTE',
        )
        self.stdout.write(f'  Trámite: {tramite1.numero_expediente} - RECIBIDO')
        
        # Trámite 2: En evaluación técnica - Habilitación de conductores
        tramite2 = Tramite.objects.create(
            tipo_tramite='HABILITACION_CONDUCTOR',
            empresa=empresas[1],
            autorizacion=autorizaciones[1],
            descripcion_solicitud='Habilitación de 3 conductores nuevos para la empresa',
            estado='EN_EVAL_TECNICA',
            creado_por=usuarios['mesa'],
        )
        # Agregar conductores al trámite (datos de conductores nuevos a habilitar)
        ConductorTramite.objects.create(
            tramite=tramite2,
            dni='04599001',
            nombres='Mario',
            apellido_paterno='Gonzales',
            apellido_materno='Pérez',
            fecha_nacimiento=date(1985, 5, 15),
            licencia_numero='Q04599001',
            licencia_categoria='AIIB',
            licencia_fecha_vencimiento=date.today() + timedelta(days=730),
            estado_proceso='PENDIENTE',
        )
        ConductorTramite.objects.create(
            tramite=tramite2,
            dni='04599002',
            nombres='José',
            apellido_paterno='Mendoza',
            apellido_materno='Luna',
            fecha_nacimiento=date(1990, 8, 22),
            licencia_numero='Q04599002',
            licencia_categoria='AIIB',
            licencia_fecha_vencimiento=date.today() + timedelta(days=500),
            estado_proceso='PENDIENTE',
        )
        self.stdout.write(f'  Trámite: {tramite2.numero_expediente} - EN_EVAL_TECNICA')
        
        # Trámite 3: En revisión legal - Sustitución de vehículo
        tramite3 = Tramite.objects.create(
            tipo_tramite='SUSTITUCION_VEHICULO',
            empresa=empresas[3],
            autorizacion=autorizaciones[3],
            descripcion_solicitud='Sustitución de vehículo V4C-888 por uno nuevo',
            estado='EN_REVISION_LEGAL',
            creado_por=usuarios['mesa'],
        )
        # Agregar vehículo saliente
        vehiculo_saliente = next((v for v in vehiculos if v.placa == 'V4C-888'), None)
        if vehiculo_saliente:
            VehiculoTramite.objects.create(
                tramite=tramite3,
                vehiculo_existente=vehiculo_saliente,
                placa_nueva='V4D-NEW',
                marca='Mercedes-Benz',
                modelo='Sprinter 415',
                anio_fabricacion=2024,
                capacidad_pasajeros=19,
                tipo_vehiculo='BUS',
                estado_proceso='PENDIENTE',
                observaciones='Vehículo V4C-888 será dado de baja por antigüedad',
            )
        self.stdout.write(f'  Trámite: {tramite3.numero_expediente} - EN_REVISION_LEGAL')
        
        # Trámite 4: Pendiente de firma - Modificación de autorización
        tramite4 = Tramite.objects.create(
            tipo_tramite='MODIFICACION_AUTORIZACION',
            empresa=empresas[2],
            autorizacion=autorizaciones[2],
            descripcion_solicitud='Modificación de rutas turísticas - agregar circuito Lago Valencia',
            estado='PENDIENTE_FIRMA',
            creado_por=usuarios['mesa'],
        )
        self.stdout.write(f'  Trámite: {tramite4.numero_expediente} - PENDIENTE_FIRMA')
        
        # Trámite 5: Aprobado - Incremento de flota
        tramite5 = Tramite.objects.create(
            tipo_tramite='INCREMENTO_FLOTA',
            empresa=empresas[1],
            autorizacion=autorizaciones[1],
            descripcion_solicitud='Incremento de 1 unidad vehicular - Toyota Hiace 2024',
            estado='APROBADO',
            creado_por=usuarios['mesa'],
        )
        VehiculoTramite.objects.create(
            tramite=tramite5,
            placa_nueva='V2D-APR',
            marca='Toyota',
            modelo='Hiace',
            anio_fabricacion=2024,
            capacidad_pasajeros=15,
            tipo_vehiculo='VAN',
            estado_proceso='APROBADO',
            numero_tuc='TUC-V2DAPR-2025',
            fecha_expedicion_tuc=date.today() - timedelta(days=5),
        )
        self.stdout.write(f'  Trámite: {tramite5.numero_expediente} - APROBADO')
        
        # Trámite 6: Observado - Baja de vehículo
        tramite6 = Tramite.objects.create(
            tipo_tramite='BAJA_VEHICULO',
            empresa=empresas[0],
            autorizacion=autorizaciones[0],
            descripcion_solicitud='Baja de vehículo V1C-789 por siniestro',
            estado='OBSERVADO',
            plazo_subsanacion=date.today() + timedelta(days=10),
            creado_por=usuarios['mesa'],
        )
        vehiculo_baja = next((v for v in vehiculos if v.placa == 'V1C-789'), None)
        if vehiculo_baja:
            VehiculoTramite.objects.create(
                tramite=tramite6,
                vehiculo_existente=vehiculo_baja,
                estado_proceso='PENDIENTE',
                observaciones='Falta documento de denuncia policial y certificado de siniestro',
            )
        self.stdout.write(f'  Trámite: {tramite6.numero_expediente} - OBSERVADO')
        
        # Trámite 7: Denegado - Autorización inicial
        tramite7 = Tramite.objects.create(
            tipo_tramite='AUTORIZACION_INICIAL',
            empresa=empresas[4],
            descripcion_solicitud='Solicitud de autorización nueva para transporte de personal',
            estado='DENEGADO',
            creado_por=usuarios['mesa'],
        )
        self.stdout.write(f'  Trámite: {tramite7.numero_expediente} - DENEGADO')
        
        # Trámite 8: Renovación de autorización
        tramite8 = Tramite.objects.create(
            tipo_tramite='RENOVACION_AUTORIZACION',
            empresa=empresas[3],
            autorizacion=autorizaciones[3],
            descripcion_solicitud='Renovación de autorización por vencimiento próximo',
            estado='RECIBIDO',
            creado_por=usuarios['mesa'],
        )
        self.stdout.write(f'  Trámite: {tramite8.numero_expediente} - RECIBIDO (Renovación)')
        
        # Trámite 9: Baja de conductor
        tramite9 = Tramite.objects.create(
            tipo_tramite='BAJA_CONDUCTOR',
            empresa=empresas[3],
            autorizacion=autorizaciones[3],
            descripcion_solicitud='Baja de conductor por renuncia voluntaria',
            estado='EN_EVAL_TECNICA',
            creado_por=usuarios['mesa'],
        )
        conductor_baja = next((c for c in conductores if c.estado == 'INACTIVO'), None)
        if conductor_baja:
            ConductorTramite.objects.create(
                tramite=tramite9,
                conductor_existente=conductor_baja,
                estado_proceso='PENDIENTE',
                observaciones='El conductor presentó carta de renuncia',
            )
        self.stdout.write(f'  Trámite: {tramite9.numero_expediente} - EN_EVAL_TECNICA (Baja)')
        
        # Crear historial para algunos trámites
        self._crear_historial_tramite(tramite2, usuarios)
        self._crear_historial_tramite(tramite3, usuarios)
        self._crear_historial_tramite(tramite4, usuarios)
        self._crear_historial_tramite(tramite5, usuarios)

    def _crear_historial_tramite(self, tramite, usuarios):
        """Crea historial de cambios de estado para un trámite."""
        estados_previos = {
            'EN_EVAL_TECNICA': ['RECIBIDO'],
            'EN_REVISION_LEGAL': ['RECIBIDO', 'EN_EVAL_TECNICA'],
            'PENDIENTE_FIRMA': ['RECIBIDO', 'EN_EVAL_TECNICA', 'EN_REVISION_LEGAL'],
            'APROBADO': ['RECIBIDO', 'EN_EVAL_TECNICA', 'EN_REVISION_LEGAL', 'PENDIENTE_FIRMA'],
        }
        
        if tramite.estado in estados_previos:
            estados = estados_previos[tramite.estado]
            fecha_base = tramite.fecha_creacion
            
            usuarios_por_estado = {
                'RECIBIDO': usuarios['mesa'],
                'EN_EVAL_TECNICA': usuarios['tecnico'],
                'EN_REVISION_LEGAL': usuarios['legal'],
                'PENDIENTE_FIRMA': usuarios['director'],
                'APROBADO': usuarios['director'],
            }
            
            for i, estado in enumerate(estados):
                estado_anterior = estados[i-1] if i > 0 else 'RECIBIDO'
                estado_nuevo = estados[i+1] if i < len(estados)-1 else tramite.estado
                
                HistorialTramite.objects.create(
                    tramite=tramite,
                    estado_anterior=estado,
                    estado_nuevo=estado_nuevo,
                    usuario=usuarios_por_estado.get(estado_nuevo, usuarios['admin']),
                    comentario=f'Trámite avanzado a {estado_nuevo}',
                )

    def _mostrar_resumen(self):
        """Muestra resumen de datos creados."""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS CREADOS'))
        self.stdout.write('='*50)
        self.stdout.write(f'  Usuarios: {Usuario.objects.count()}')
        self.stdout.write(f'  Empresas: {EmpresaTransporte.objects.count()}')
        self.stdout.write(f'  Autorizaciones: {Autorizacion.objects.count()}')
        self.stdout.write(f'  Vehículos: {Vehiculo.objects.count()}')
        self.stdout.write(f'  Conductores: {Conductor.objects.count()}')
        self.stdout.write(f'  Habilitaciones Vehiculares: {HabilitacionVehicular.objects.count()}')
        self.stdout.write(f'  Habilitaciones Conductores: {HabilitacionConductor.objects.count()}')
        self.stdout.write(f'  Trámites: {Tramite.objects.count()}')
        self.stdout.write(f'  Rutas: {Ruta.objects.count()}')
        self.stdout.write(f'  Frecuencias: {Frecuencia.objects.count()}')
        self.stdout.write(f'  Tipos de Servicio: {TipoServicio.objects.count()}')
        self.stdout.write(f'  Tipos de Vehículo: {TipoVehiculo.objects.count()}')
        self.stdout.write('='*50)
        self.stdout.write('\nCredenciales de usuarios:')
        self.stdout.write('  Contraseña para todos: Demo2025!')
        self.stdout.write('  admin / mesa / tecnico / legal / director / consulta / sutran')
        self.stdout.write('='*50)
