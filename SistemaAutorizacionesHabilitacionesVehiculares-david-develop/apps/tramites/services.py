"""
Servicios para procesar trámites y crear entidades correspondientes.
Este módulo contiene la lógica de negocio que se ejecuta cuando un trámite es aprobado.
"""

from django.db import transaction
from django.utils import timezone
from datetime import datetime

from apps.autorizaciones.models import Autorizacion, HistorialAutorizacion
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import Conductor, HabilitacionConductor
from apps.configuracion.models import Ruta, Frecuencia, Carroceria as CarroceriaModel, TipoServicio as TipoServicioModel, CategoriaVehiculo
from apps.vehiculos import signals as vehiculos_signals
from apps.conductores import signals as conductores_signals
from utils.constants import (
    TipoTramite, EstadoVehiculo, EstadoHabilitacion, 
    EstadoConductor, EstadoAutorizacion
)


def desactivar_autorizacion_cascada(autorizacion, nuevo_estado, motivo, usuario=None):
    """
    Desactiva una autorización y todas sus entidades relacionadas (vehículos, conductores, habilitaciones).
    
    Args:
        autorizacion: Instancia de Autorizacion
        nuevo_estado: EstadoAutorizacion.CANCELADA o EstadoAutorizacion.VENCIDA
        motivo: Texto descriptivo del motivo
        usuario: Usuario que realiza la acción (opcional)
    """
    with transaction.atomic():
        estado_anterior = autorizacion.estado
        hoy = timezone.now().date()
        
        # 1. Guardar historial de la autorización
        HistorialAutorizacion.objects.create(
            autorizacion=autorizacion,
            campo_modificado='estado',
            valor_anterior=estado_anterior,
            valor_nuevo=nuevo_estado,
            usuario=usuario,
            motivo=motivo
        )
        
        # 2. Cambiar estado de la autorización
        autorizacion.estado = nuevo_estado
        autorizacion.save()
        
        # 3. Dar de baja todas las habilitaciones vehiculares vigentes
        habilitaciones_v = HabilitacionVehicular.objects.filter(
            autorizacion=autorizacion,
            estado=EstadoHabilitacion.VIGENTE
        )
        
        vehiculos_afectados_ids = list(habilitaciones_v.values_list('vehiculo_id', flat=True))
        
        habilitaciones_v.update(
            estado=EstadoHabilitacion.BAJA,
            fecha_fin=autorizacion.fecha_resolucion if hasattr(autorizacion, 'fecha_resolucion') and autorizacion.fecha_resolucion else hoy,
            motivo=motivo
        )
        
        # 4. Cambiar estado de los vehículos asociados a BAJA
        # Solo si estaban HABILITADOS
        Vehiculo.objects.filter(
            id__in=vehiculos_afectados_ids,
            estado=EstadoVehiculo.HABILITADO
        ).update(estado=EstadoVehiculo.BAJA)
        
        # 5. Dar de baja todas las habilitaciones de conductores vigentes
        habilitaciones_c = HabilitacionConductor.objects.filter(
            autorizacion=autorizacion,
            estado=EstadoHabilitacion.VIGENTE
        )
        
        conductores_afectados_ids = list(habilitaciones_c.values_list('conductor_id', flat=True))
        
        habilitaciones_c.update(
            estado=EstadoHabilitacion.BAJA,
            fecha_fin=hoy,
            motivo=motivo
        )
        
        # 6. Cambiar estado de los conductores a INACTIVO
        # SOLO si no tienen ninguna otra habilitación VIGENTE en el sistema
        for conductor_id in conductores_afectados_ids:
            tiene_otras = HabilitacionConductor.objects.filter(
                conductor_id=conductor_id,
                estado=EstadoHabilitacion.VIGENTE
            ).exclude(autorizacion=autorizacion).exists()
            
            if not tiene_otras:
                Conductor.objects.filter(id=conductor_id).update(estado=EstadoConductor.INACTIVO)
                
    return {
        'vehiculos_count': len(vehiculos_afectados_ids),
        'conductores_count': len(conductores_afectados_ids)
    }


class TramiteProcesador:
    """
    Clase para procesar trámites aprobados y crear/actualizar entidades.
    """
    
    def __init__(self, tramite, usuario):
        self.tramite = tramite
        self.usuario = usuario
        self.datos = getattr(tramite, 'datos', None)
        self.resultado = {
            'exito': False,
            'mensaje': '',
            'entidades_creadas': []
        }
    
    def procesar(self):
        """Procesa el trámite según su tipo."""
        if not self.datos:
            self.resultado['mensaje'] = 'El trámite no tiene datos específicos para procesar.'
            return self.resultado
        
        procesadores = {
            TipoTramite.AUTORIZACION_INICIAL: self._procesar_autorizacion_inicial,
            TipoTramite.AUTORIZACION_RUTA: self._procesar_autorizacion_ruta,
            TipoTramite.MODIFICACION_AUTORIZACION: self._procesar_modificacion_autorizacion,
            TipoTramite.RENOVACION_AUTORIZACION: self._procesar_renovacion_autorizacion,
            TipoTramite.RENOVACION_TUC: self._procesar_renovacion_tuc,
            TipoTramite.BAJA_AUTORIZACION: self._procesar_baja_autorizacion,
            TipoTramite.SUSPENSION_AUTORIZACION: self._procesar_suspension_autorizacion,
            TipoTramite.INCREMENTO_FLOTA: self._procesar_incremento_flota,
            TipoTramite.SUSTITUCION_VEHICULO: self._procesar_sustitucion_vehiculo,
            TipoTramite.BAJA_VEHICULO: self._procesar_baja_vehiculo,
            TipoTramite.HABILITACION_CONDUCTOR: self._procesar_habilitacion_conductor,
            TipoTramite.BAJA_CONDUCTOR: self._procesar_baja_conductor,
        }
        
        procesador = procesadores.get(self.tramite.tipo_tramite)
        if procesador:
            try:
                with transaction.atomic():
                    # Desactivar signals para evitar duplicados de habilitaciones
                    vehiculos_signals.disable_signals()
                    conductores_signals.disable_signals()
                    try:
                        procesador()
                        self.resultado['exito'] = True
                    finally:
                        # Reactivar signals
                        vehiculos_signals.enable_signals()
                        conductores_signals.enable_signals()
            except Exception as e:
                self.resultado['exito'] = False
                self.resultado['mensaje'] = f'Error al procesar: {str(e)}'
        else:
            self.resultado['mensaje'] = f'Tipo de trámite no soportado: {self.tramite.tipo_tramite}'
        
        return self.resultado
    
    def _parse_date(self, date_str):
        """Convierte string a fecha."""
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            return date_str.date()
        if hasattr(date_str, 'date'):
            return date_str
        try:
            return datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            return None
    
    def _obtener_tipo_vehiculo(self, tipo_str):
        """Obtiene la instancia de Carroceria a partir del string."""
        if not tipo_str:
            return None
        
        # Intentar buscar por código
        tipo = CarroceriaModel.objects.filter(codigo=tipo_str).first()
        if tipo:
            return tipo
            
        # Intentar buscar por nombre
        tipo = CarroceriaModel.objects.filter(nombre=tipo_str).first()
        if tipo:
            return tipo
            
        # Si no existe, crear uno básico (fallback)
        # Nota: Requiere una categoría. Buscamos o creamos una por defecto.
        categoria, _ = CategoriaVehiculo.objects.get_or_create(
            codigo='M2',
            defaults={'nombre': 'Categoría M2'}
        )
        
        return CarroceriaModel.objects.create(
            codigo=tipo_str[:20],
            nombre=tipo_str[:100],
            descripcion='Generado automáticamente por trámite',
            categoria=categoria,
            creado_por=self.usuario
        )

    def _obtener_tipo_servicio(self, tipo_ref):
        """Obtiene la instancia de TipoServicio a partir de ID, codigo o nombre."""
        if not tipo_ref:
            return None
        
        # Intentar buscar por código o nombre
        if hasattr(tipo_ref, 'pk'):
            return tipo_ref

        tipo = None
        try:
            tipo = TipoServicioModel.objects.filter(pk=int(tipo_ref)).first()
        except (TypeError, ValueError):
            pass

        if tipo:
            return tipo

        tipo = TipoServicioModel.objects.filter(codigo=tipo_ref).first()
        if not tipo:
            tipo = TipoServicioModel.objects.filter(nombre=tipo_ref).first()
            
        if tipo:
            return tipo
            
        # Si no existe, crear uno básico (fallback)
        return TipoServicioModel.objects.create(
            codigo=str(tipo_ref)[:20],
            nombre=str(tipo_ref)[:100],
            descripcion='Generado automáticamente por trámite',
            creado_por=self.usuario
        )

    # ========== AUTORIZACIÓN INICIAL ==========
    def _procesar_autorizacion_inicial(self):
        """Crea una nueva autorización para la empresa."""
        datos = self.datos.datos_json.get('autorizacion', {})
        
        # Crear la autorización
        autorizacion = Autorizacion.objects.create(
            empresa=self.tramite.empresa,
            numero_resolucion=self.tramite.numero_resolucion,
            fecha_resolucion=self.tramite.fecha_resolucion or timezone.now().date(),
            archivo_resolucion=self.tramite.archivo_resolucion,
            fecha_inicio_vigencia=self._parse_date(datos.get('fecha_inicio_vigencia')),
            fecha_fin_vigencia=self._parse_date(datos.get('fecha_fin_vigencia')),
            ambito=datos.get('ambito', 'MADRE_DE_DIOS'),
            tipo_servicio=self._obtener_tipo_servicio(datos.get('tipo_servicio', 'REGULAR')),
            modalidad=datos.get('modalidad', ''),
            descripcion_rutas=datos.get('descripcion_rutas', ''),
            estado=EstadoAutorizacion.VIGENTE,
            observaciones=datos.get('observaciones', ''),
            creado_por=self.usuario
        )
        
        # Asignar rutas
        rutas_ids = datos.get('rutas', [])
        if rutas_ids:
            rutas = Ruta.objects.filter(id__in=rutas_ids)
            autorizacion.rutas.set(rutas)
        
        # Asignar frecuencias
        frecuencias_ids = datos.get('frecuencias', [])
        if frecuencias_ids:
            frecuencias = Frecuencia.objects.filter(id__in=frecuencias_ids)
            autorizacion.frecuencias_asignadas.set(frecuencias)
        
        # Vincular al trámite
        self.tramite.autorizacion = autorizacion
        self.tramite.save()
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Autorización',
            'id': autorizacion.id,
            'descripcion': f'{autorizacion.numero_resolucion} - {autorizacion.empresa.razon_social}'
        })
        
        # ========== PROCESAR VEHÍCULOS DEL TRÁMITE (flota inicial) ==========
        vehiculos_tramite = self.tramite.vehiculos_tramite.filter(estado_proceso='PENDIENTE')
        for veh_tramite in vehiculos_tramite:
            if veh_tramite.placa_nueva:
                # Crear vehículo nuevo
                vehiculo = Vehiculo.objects.create(
                    placa=veh_tramite.placa_nueva.upper(),
                    empresa_propietaria=self.tramite.empresa,
                    marca=veh_tramite.marca or '',
                    modelo=veh_tramite.modelo or '',
                    anio_fabricacion=veh_tramite.anio_fabricacion,
                    color=veh_tramite.color or '',
                    numero_serie=veh_tramite.numero_serie or '',
                    numero_motor=veh_tramite.numero_motor or '',
                    capacidad_sentados=veh_tramite.capacidad_pasajeros,
                    peso_bruto=veh_tramite.peso_bruto,
                    categoria=veh_tramite.categoria,
                    carroceria=veh_tramite.carroceria,
                    estado=EstadoVehiculo.HABILITADO,
                    numero_tiv=veh_tramite.numero_tarjeta_propiedad or '',
                    fecha_venc_soat=veh_tramite.fecha_venc_soat,
                    fecha_venc_citv=veh_tramite.fecha_venc_citv,
                    autorizacion_principal=autorizacion,
                    numero_resolucion=self.tramite.numero_resolucion,
                    fecha_resolucion=self.tramite.fecha_resolucion,
                    archivo_resolucion=self.tramite.archivo_resolucion,
                    creado_por=self.usuario
                )
                
                # Crear habilitación vehicular
                HabilitacionVehicular.objects.create(
                    vehiculo=vehiculo,
                    autorizacion=autorizacion,
                    fecha_inicio=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                    estado=EstadoHabilitacion.VIGENTE,
                    motivo=f'Flota inicial - Trámite {self.tramite.numero_expediente}',
                    tramite_origen=self.tramite,
                    # Datos TUC
                    numero_tuc=veh_tramite.numero_tuc or '',
                    fecha_expedicion_tuc=veh_tramite.fecha_expedicion_tuc,
                    fecha_autorizacion_transportista=veh_tramite.fecha_autorizacion_transportista,
                    fecha_expiracion_transportista=veh_tramite.fecha_expiracion_transportista,
                    creado_por=self.usuario
                )
                
                # Actualizar registro del trámite
                veh_tramite.vehiculo_creado = vehiculo
                veh_tramite.estado_proceso = 'APROBADO'
                veh_tramite.save()
                
                self.resultado['entidades_creadas'].append({
                    'tipo': 'Vehículo (Flota Inicial)',
                    'id': vehiculo.id,
                    'descripcion': f'{vehiculo.placa} - {vehiculo.marca} {vehiculo.modelo}'
                })
        
        # ========== PROCESAR CONDUCTORES DEL TRÁMITE (conductores iniciales) ==========
        conductores_tramite = self.tramite.conductores_tramite.filter(estado_proceso='PENDIENTE')
        for cond_tramite in conductores_tramite:
            if cond_tramite.conductor_existente:
                conductor = cond_tramite.conductor_existente
            elif cond_tramite.dni:
                # Buscar si ya existe un conductor con ese DNI
                conductor = Conductor.objects.filter(dni=cond_tramite.dni).first()
                
                if conductor:
                    # Actualizar datos
                    conductor.nombres = cond_tramite.nombres or conductor.nombres
                    conductor.apellido_paterno = cond_tramite.apellido_paterno or conductor.apellido_paterno
                    conductor.apellido_materno = cond_tramite.apellido_materno or conductor.apellido_materno
                    conductor.fecha_nacimiento = cond_tramite.fecha_nacimiento or conductor.fecha_nacimiento
                    conductor.direccion = cond_tramite.direccion or conductor.direccion
                    conductor.telefono = cond_tramite.telefono or conductor.telefono
                    conductor.email = cond_tramite.email or conductor.email
                    conductor.licencia_numero = cond_tramite.licencia_numero or conductor.licencia_numero
                    conductor.licencia_categoria = cond_tramite.licencia_categoria or conductor.licencia_categoria
                    conductor.licencia_fecha_emision = cond_tramite.licencia_fecha_emision or conductor.licencia_fecha_emision
                    conductor.licencia_fecha_vencimiento = cond_tramite.licencia_fecha_vencimiento or conductor.licencia_fecha_vencimiento
                    conductor.estado = EstadoConductor.ACTIVO
                    
                    # Actualizar datos de resolución
                    if self.tramite.numero_resolucion:
                        conductor.numero_resolucion = self.tramite.numero_resolucion
                    if self.tramite.fecha_resolucion:
                        conductor.fecha_resolucion = self.tramite.fecha_resolucion
                    if self.tramite.archivo_resolucion:
                        conductor.archivo_resolucion = self.tramite.archivo_resolucion
                        
                    conductor.save()
                    
                    self.resultado['entidades_creadas'].append({
                        'tipo': 'Conductor (Actualizado)',
                        'id': conductor.id,
                        'descripcion': conductor.nombre_completo
                    })
                else:
                    # Crear conductor nuevo
                    conductor = Conductor.objects.create(
                        empresa=self.tramite.empresa,
                        dni=cond_tramite.dni,
                        nombres=cond_tramite.nombres or '',
                        apellido_paterno=cond_tramite.apellido_paterno or '',
                        apellido_materno=cond_tramite.apellido_materno or '',
                        fecha_nacimiento=cond_tramite.fecha_nacimiento,
                        direccion=cond_tramite.direccion or '',
                        telefono=cond_tramite.telefono or '',
                        email=cond_tramite.email or '',
                        licencia_numero=cond_tramite.licencia_numero or '',
                        licencia_categoria=cond_tramite.licencia_categoria or '',
                        licencia_fecha_emision=cond_tramite.licencia_fecha_emision,
                        licencia_fecha_vencimiento=cond_tramite.licencia_fecha_vencimiento,
                        estado=EstadoConductor.ACTIVO,
                        numero_resolucion=self.tramite.numero_resolucion,
                        fecha_resolucion=self.tramite.fecha_resolucion,
                        archivo_resolucion=self.tramite.archivo_resolucion,
                        creado_por=self.usuario
                    )
                    
                    self.resultado['entidades_creadas'].append({
                        'tipo': 'Conductor (Nuevo)',
                        'id': conductor.id,
                        'descripcion': conductor.nombre_completo
                    })
            else:
                continue
            
            # Crear habilitación del conductor
            HabilitacionConductor.objects.create(
                conductor=conductor,
                empresa=self.tramite.empresa,
                autorizacion=autorizacion,
                fecha_inicio=timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Habilitación inicial - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                creado_por=self.usuario
            )
            
            # Actualizar registro del trámite
            cond_tramite.conductor_creado = conductor
            cond_tramite.estado_proceso = 'APROBADO'
            cond_tramite.save()
            
            self.resultado['entidades_creadas'].append({
                'tipo': 'Habilitación Conductor',
                'id': conductor.id,
                'descripcion': f'{conductor.nombre_completo} habilitado'
            })
        
        self.resultado['mensaje'] = f'Autorización {autorizacion.numero_resolucion} creada exitosamente.'
    
    # ========== AUTORIZACION DE RUTA ==========
    def _procesar_autorizacion_ruta(self):
        """Crea una autorizacion de ruta sin procesar flota ni conductores."""
        datos = self.datos.datos_json.get('autorizacion', {})

        autorizacion = Autorizacion.objects.create(
            empresa=self.tramite.empresa,
            numero_resolucion=self.tramite.numero_resolucion,
            fecha_resolucion=self.tramite.fecha_resolucion or timezone.now().date(),
            archivo_resolucion=self.tramite.archivo_resolucion,
            fecha_inicio_vigencia=self._parse_date(datos.get('fecha_inicio_vigencia')),
            fecha_fin_vigencia=self._parse_date(datos.get('fecha_fin_vigencia')),
            ambito=datos.get('ambito', 'MADRE_DE_DIOS'),
            tipo_servicio=self._obtener_tipo_servicio(datos.get('tipo_servicio', 'REGULAR')),
            modalidad=datos.get('modalidad', ''),
            descripcion_rutas=datos.get('descripcion_rutas', ''),
            estado=EstadoAutorizacion.VIGENTE,
            observaciones=datos.get('observaciones', ''),
            creado_por=self.usuario
        )

        rutas_ids = datos.get('rutas', [])
        if rutas_ids:
            rutas = Ruta.objects.filter(id__in=rutas_ids)
            autorizacion.rutas.set(rutas)

        frecuencias_ids = datos.get('frecuencias', [])
        if frecuencias_ids:
            frecuencias = Frecuencia.objects.filter(id__in=frecuencias_ids)
            autorizacion.frecuencias_asignadas.set(frecuencias)

        self.tramite.autorizacion = autorizacion
        self.tramite.save()

        self.resultado['entidades_creadas'].append({
            'tipo': 'Autorizacion de Ruta',
            'id': autorizacion.id,
            'descripcion': f'{autorizacion.numero_resolucion} - {autorizacion.empresa.razon_social}'
        })
        self.resultado['mensaje'] = f'Autorizacion de Ruta {autorizacion.numero_resolucion} creada exitosamente.'

    # ========== MODIFICACIÓN DE AUTORIZACIÓN ==========
    def _procesar_modificacion_autorizacion(self):
        """Modifica una autorización existente y los datos de su empresa."""
        datos = self.datos.datos_json.get('modificacion', {})
        autorizacion = self.tramite.autorizacion
        
        if not autorizacion:
            raise ValueError('No se especificó la autorización a modificar.')
        
        # Guardar estado anterior para historial
        HistorialAutorizacion.objects.create(
            autorizacion=autorizacion,
            campo_modificado='Múltiples campos',
            valor_anterior=f'Tipo: {autorizacion.tipo_servicio}, Modalidad: {autorizacion.modalidad}',
            valor_nuevo=f'Modificado por trámite {self.tramite.numero_expediente}',
            usuario=self.usuario,
            motivo=datos.get('motivo_modificacion', '')
        )
        
        # ===== ACTUALIZAR DATOS DE LA AUTORIZACIÓN =====
        # Actualizar campos si se proporcionaron
        if datos.get('tipo_servicio'):
            autorizacion.tipo_servicio = self._obtener_tipo_servicio(datos['tipo_servicio'])
        
        if datos.get('modalidad'):
            autorizacion.modalidad = datos['modalidad']
        
        if datos.get('descripcion_rutas'):
            autorizacion.descripcion_rutas = datos['descripcion_rutas']
        
        # Actualizar datos de resolución si existen en el trámite
        if self.tramite.numero_resolucion:
            autorizacion.numero_resolucion = self.tramite.numero_resolucion
        if self.tramite.fecha_resolucion:
            autorizacion.fecha_resolucion = self.tramite.fecha_resolucion
        if self.tramite.archivo_resolucion:
            autorizacion.archivo_resolucion = self.tramite.archivo_resolucion

        autorizacion.save()
        
        # Actualizar rutas si se proporcionaron
        rutas_ids = datos.get('rutas', [])
        if rutas_ids:
            rutas = Ruta.objects.filter(id__in=rutas_ids)
            autorizacion.rutas.set(rutas)
        
        # Actualizar frecuencias si se proporcionaron
        frecuencias_ids = datos.get('frecuencias', [])
        if frecuencias_ids:
            frecuencias = Frecuencia.objects.filter(id__in=frecuencias_ids)
            autorizacion.frecuencias_asignadas.set(frecuencias)
        
        # ===== ACTUALIZAR DATOS DE LA EMPRESA =====
        empresa = autorizacion.empresa
        if empresa:
            empresa_actualizada = False
            
            # Actualizar campos de la empresa si se proporcionaron
            if datos.get('razon_social'):
                empresa.razon_social = datos['razon_social']
                empresa_actualizada = True
            
            if datos.get('nombre_comercial'):
                empresa.nombre_comercial = datos['nombre_comercial']
                empresa_actualizada = True
            
            if datos.get('domicilio_fiscal'):
                empresa.domicilio_fiscal = datos['domicilio_fiscal']
                empresa_actualizada = True
            
            if datos.get('representante_legal'):
                empresa.representante_legal = datos['representante_legal']
                empresa_actualizada = True
            
            if datos.get('dni_representante'):
                empresa.dni_representante = datos['dni_representante']
                empresa_actualizada = True
            
            if datos.get('telefono'):
                empresa.telefono = datos['telefono']
                empresa_actualizada = True
            
            if datos.get('email'):
                empresa.email = datos['email']
                empresa_actualizada = True
            
            if empresa_actualizada:
                empresa.save()
                self.resultado['entidades_modificadas'] = self.resultado.get('entidades_modificadas', [])
                self.resultado['entidades_modificadas'].append({
                    'tipo': 'Empresa de Transporte',
                    'id': empresa.id,
                    'descripcion': empresa.razon_social
                })
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Autorización (Modificada)',
            'id': autorizacion.id,
            'descripcion': autorizacion.numero_resolucion
        })
        self.resultado['mensaje'] = f'Autorización {autorizacion.numero_resolucion} y datos de empresa modificados exitosamente.'
    
    # ========== RENOVACIÓN DE AUTORIZACIÓN ==========
    def _procesar_renovacion_autorizacion(self):
        """Renueva una autorización extendiendo su fecha de vigencia."""
        datos = self.datos.datos_json.get('renovacion', {})
        autorizacion = self.tramite.autorizacion
        
        if not autorizacion:
            raise ValueError('No se especificó la autorización a renovar.')
        
        fecha_anterior = autorizacion.fecha_fin_vigencia
        nueva_fecha = self._parse_date(datos.get('nueva_fecha_fin_vigencia'))
        
        if not nueva_fecha:
            raise ValueError('No se especificó la nueva fecha de fin de vigencia.')
        
        # Guardar historial
        HistorialAutorizacion.objects.create(
            autorizacion=autorizacion,
            campo_modificado='fecha_fin_vigencia',
            valor_anterior=str(fecha_anterior),
            valor_nuevo=str(nueva_fecha),
            usuario=self.usuario,
            motivo=f'Renovación por trámite {self.tramite.numero_expediente}'
        )
        
        # Actualizar fecha de vigencia y datos de resolución
        autorizacion.fecha_fin_vigencia = nueva_fecha
        autorizacion.estado = EstadoAutorizacion.VIGENTE
        
        if self.tramite.numero_resolucion:
            autorizacion.numero_resolucion = self.tramite.numero_resolucion
        if self.tramite.fecha_resolucion:
            autorizacion.fecha_resolucion = self.tramite.fecha_resolucion
        if self.tramite.archivo_resolucion:
            autorizacion.archivo_resolucion = self.tramite.archivo_resolucion
            
        autorizacion.save()
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Autorización (Renovada)',
            'id': autorizacion.id,
            'descripcion': f'{autorizacion.numero_resolucion} - Vigente hasta {nueva_fecha}'
        })
        self.resultado['mensaje'] = f'Autorización {autorizacion.numero_resolucion} renovada hasta {nueva_fecha}.'
    
    # ========== BAJA DE AUTORIZACIÓN (Voluntaria) ==========
    def _procesar_baja_autorizacion(self):
        """
        Da de baja una autorización de forma voluntaria.
        Cambia el estado a CANCELADA y da de baja todas las habilitaciones.
        """
        datos = self.datos.datos_json.get('baja', {})
        autorizacion = self.tramite.autorizacion
        
        if not autorizacion:
            raise ValueError('No se especificó la autorización a dar de baja.')
        
        motivo = datos.get('motivo', f'Baja voluntaria - Trámite {self.tramite.numero_expediente}')
        
        # Usar el helper para desactivación en cascada
        resultado_cascada = desactivar_autorizacion_cascada(
            autorizacion=autorizacion,
            nuevo_estado=EstadoAutorizacion.CANCELADA,
            motivo=motivo,
            usuario=self.usuario
        )
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Autorización (Baja Voluntaria)',
            'id': autorizacion.id,
            'descripcion': f'{autorizacion.numero_resolucion} - CANCELADA'
        })
        
        mensaje = f'Autorización {autorizacion.numero_resolucion} dada de baja.'
        if resultado_cascada['vehiculos_count'] > 0 or resultado_cascada['conductores_count'] > 0:
            mensaje += f' Se desactivaron {resultado_cascada["vehiculos_count"]} vehículos y {resultado_cascada["conductores_count"]} conductores.'
            
        self.resultado['mensaje'] = mensaje
    
    # ========== SUSPENSIÓN DE AUTORIZACIÓN (Sanción Interna) ==========
    def _procesar_suspension_autorizacion(self):
        """
        Suspende una autorización por sanción interna.
        Cambia el estado a SUSPENDIDA y suspende todas las habilitaciones.
        """
        datos = self.datos.datos_json.get('suspension', {})
        autorizacion = self.tramite.autorizacion
        
        if not autorizacion:
            raise ValueError('No se especificó la autorización a suspender.')
        
        motivo = datos.get('motivo', f'Suspensión por sanción - Trámite {self.tramite.numero_expediente}')
        
        # Guardar historial
        HistorialAutorizacion.objects.create(
            autorizacion=autorizacion,
            campo_modificado='estado',
            valor_anterior=autorizacion.estado,
            valor_nuevo=EstadoAutorizacion.SUSPENDIDA,
            usuario=self.usuario,
            motivo=motivo
        )
        
        # Cambiar estado de la autorización a SUSPENDIDA
        autorizacion.estado = EstadoAutorizacion.SUSPENDIDA
        autorizacion.save()
        
        # Suspender todas las habilitaciones vehiculares
        HabilitacionVehicular.objects.filter(
            autorizacion=autorizacion,
            estado=EstadoHabilitacion.VIGENTE
        ).update(
            estado=EstadoHabilitacion.SUSPENDIDA,
            motivo=motivo
        )
        
        # Suspender todas las habilitaciones de conductores
        HabilitacionConductor.objects.filter(
            autorizacion=autorizacion,
            estado=EstadoHabilitacion.VIGENTE
        ).update(
            estado=EstadoHabilitacion.SUSPENDIDA,
            motivo=motivo
        )
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Autorización (Suspendida por Sanción)',
            'id': autorizacion.id,
            'descripcion': f'{autorizacion.numero_resolucion} - SUSPENDIDA'
        })
        self.resultado['mensaje'] = f'Autorización {autorizacion.numero_resolucion} suspendida por sanción junto con sus habilitaciones.'

    # ========== INCREMENTO DE FLOTA ==========
    def _procesar_incremento_flota(self):
        """Crea nuevos vehículos y sus habilitaciones desde VehiculoTramite."""
        vehiculos_tramite = self.tramite.vehiculos_tramite.all()
        
        if not vehiculos_tramite.exists():
            # Fallback a datos JSON si no hay VehiculoTramite (compatibilidad)
            datos = self.datos.datos_json.get('vehiculo', {})
            if not datos:
                raise ValueError('No hay vehículos registrados en el trámite.')
            self._crear_vehiculo_y_habilitacion(datos)
        else:
            for vt in vehiculos_tramite:
                self._crear_vehiculo_y_habilitacion_desde_vt(vt)

        conductores_tramite = self.tramite.conductores_tramite.all()
        for ct in conductores_tramite:
            self._habilitar_conductor_ct(ct)
        
        self.resultado['mensaje'] = f'Se procesaron {len(self.resultado["entidades_creadas"])} entidades correctamente.'

    # ========== RENOVACIÓN DE TUC ==========
    def _procesar_renovacion_tuc(self):
        """Renueva datos de TUC en habilitaciones vehiculares existentes."""
        vehiculos_tramite = self.tramite.vehiculos_tramite.all()

        if not vehiculos_tramite.exists():
            raise ValueError('No hay vehículos registrados en el trámite de Renovación de TUC.')

        if not self.tramite.autorizacion:
            raise ValueError('El trámite de Renovación de TUC requiere una autorización asociada.')

        for vt in vehiculos_tramite:
            vehiculo = vt.vehiculo_existente
            if not vehiculo and vt.placa_nueva:
                placa_normalizada = vt.placa_nueva.upper().replace('-', '').replace(' ', '')
                vehiculo = Vehiculo.objects.filter(placa=placa_normalizada).first()

            if not vehiculo:
                raise ValueError('No se encontró el vehículo para renovar TUC.')

            habilitacion = HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                autorizacion=self.tramite.autorizacion,
                estado=EstadoHabilitacion.VIGENTE
            ).first()

            if not habilitacion:
                raise ValueError(
                    f'El vehículo {vehiculo.placa} no tiene habilitación vigente en la autorización seleccionada.'
                )

            # Actualizar datos de TUC
            habilitacion.numero_tuc = vt.numero_tuc or habilitacion.numero_tuc
            habilitacion.fecha_expedicion_tuc = vt.fecha_expedicion_tuc or habilitacion.fecha_expedicion_tuc
            habilitacion.fecha_autorizacion_transportista = vt.fecha_autorizacion_transportista or habilitacion.fecha_autorizacion_transportista
            habilitacion.fecha_expiracion_transportista = vt.fecha_expiracion_transportista or habilitacion.fecha_expiracion_transportista
            habilitacion.save()

            vt.estado_proceso = 'APROBADO'
            vt.save()

            self.resultado['entidades_creadas'].append({
                'tipo': 'Renovación TUC',
                'id': habilitacion.id,
                'descripcion': f'{vehiculo.placa} (TUC: {habilitacion.numero_tuc})'
            })

        self.resultado['mensaje'] = f'Se renovaron TUCs para {len(self.resultado["entidades_creadas"])} vehículos.'

    def _crear_vehiculo_y_habilitacion_desde_vt(self, vt):
        """Crea o actualiza un vehículo y su habilitación a partir de un objeto VehiculoTramite."""
        # Buscar si el vehículo ya existe por placa
        placa_normalizada = vt.placa_nueva.upper().replace('-', '').replace(' ', '')
        vehiculo = Vehiculo.objects.filter(placa=placa_normalizada).first()
        
        if vehiculo:
            # Actualizar vehículo existente
            vehiculo.empresa_propietaria = self.tramite.empresa
            vehiculo.marca = vt.marca
            vehiculo.modelo = vt.modelo
            vehiculo.anio_fabricacion = vt.anio_fabricacion
            vehiculo.color = vt.color
            vehiculo.numero_serie = vt.numero_serie
            vehiculo.numero_motor = vt.numero_motor
            vehiculo.capacidad_sentados = vt.capacidad_pasajeros
            vehiculo.peso_bruto = vt.peso_bruto
            vehiculo.categoria = vt.categoria
            vehiculo.carroceria = vt.carroceria
            vehiculo.estado = EstadoVehiculo.HABILITADO
            vehiculo.numero_tiv = vt.numero_tarjeta_propiedad
            vehiculo.fecha_venc_soat = vt.fecha_venc_soat
            vehiculo.fecha_venc_citv = vt.fecha_venc_citv
            vehiculo.autorizacion_principal = self.tramite.autorizacion
            
            # Actualizar datos de resolución
            if self.tramite.numero_resolucion:
                vehiculo.numero_resolucion = self.tramite.numero_resolucion
            if self.tramite.fecha_resolucion:
                vehiculo.fecha_resolucion = self.tramite.fecha_resolucion
            if self.tramite.archivo_resolucion:
                vehiculo.archivo_resolucion = self.tramite.archivo_resolucion
                
            vehiculo.save()
        else:
            # Crear el vehículo
            vehiculo = Vehiculo.objects.create(
                placa=placa_normalizada,
                empresa_propietaria=self.tramite.empresa,
                marca=vt.marca,
                modelo=vt.modelo,
                anio_fabricacion=vt.anio_fabricacion,
                color=vt.color,
                numero_serie=vt.numero_serie,
                numero_motor=vt.numero_motor,
                capacidad_sentados=vt.capacidad_pasajeros,
                peso_bruto=vt.peso_bruto,
                categoria=vt.categoria,
                carroceria=vt.carroceria,
                estado=EstadoVehiculo.HABILITADO,
                numero_tiv=vt.numero_tarjeta_propiedad,
                fecha_venc_soat=vt.fecha_venc_soat,
                fecha_venc_citv=vt.fecha_venc_citv,
                autorizacion_principal=self.tramite.autorizacion,
                numero_resolucion=self.tramite.numero_resolucion,
                fecha_resolucion=self.tramite.fecha_resolucion,
                archivo_resolucion=self.tramite.archivo_resolucion,
                creado_por=self.usuario
            )
        
        # Actualizar referencia en VehiculoTramite
        vt.vehiculo_creado = vehiculo
        vt.estado_proceso = 'APROBADO'
        vt.save()
        
        # Crear habilitación vehicular
        if self.tramite.autorizacion:
            # Dar de baja habilitaciones anteriores del mismo vehículo para otras autorizaciones
            HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                estado=EstadoHabilitacion.VIGENTE
            ).exclude(autorizacion=self.tramite.autorizacion).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                motivo=f'Baja por nueva habilitación en trámite {self.tramite.numero_expediente}'
            )

            habilitacion = HabilitacionVehicular.objects.create(
                vehiculo=vehiculo,
                autorizacion=self.tramite.autorizacion,
                fecha_inicio=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Incremento de flota - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                # Datos TUC (ya registrados en vt durante la aprobación)
                numero_tuc=vt.numero_tuc,
                fecha_expedicion_tuc=vt.fecha_expedicion_tuc,
                fecha_autorizacion_transportista=vt.fecha_autorizacion_transportista,
                fecha_expiracion_transportista=vt.fecha_expiracion_transportista,
                creado_por=self.usuario
            )
            
            self.resultado['entidades_creadas'].append({
                'tipo': 'Habilitación Vehicular',
                'id': habilitacion.id,
                'descripcion': f'Habilitación para {vehiculo.placa} (TUC: {vt.numero_tuc})'
            })
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Vehículo',
            'id': vehiculo.id,
            'descripcion': f'{vehiculo.placa} - {vehiculo.marca} {vehiculo.modelo}'
        })

    def _crear_vehiculo_y_habilitacion(self, datos):
        """Crea o actualiza un vehículo y su habilitación a partir de datos JSON."""
        # Buscar si el vehículo ya existe por placa
        placa_normalizada = datos.get('placa', '').upper().replace('-', '').replace(' ', '')
        vehiculo = Vehiculo.objects.filter(placa=placa_normalizada).first()
        
        if vehiculo:
            # Actualizar vehículo existente
            vehiculo.empresa_propietaria = self.tramite.empresa
            vehiculo.marca = datos.get('marca', '')
            vehiculo.modelo = datos.get('modelo', '')
            vehiculo.anio_fabricacion = datos.get('anio_fabricacion')
            vehiculo.color = datos.get('color', '')
            vehiculo.numero_serie = datos.get('numero_serie', '')
            vehiculo.numero_motor = datos.get('numero_motor', '')
            vehiculo.capacidad_sentados = datos.get('capacidad_sentados')
            vehiculo.peso_bruto = datos.get('peso_bruto')
            # En JSON fallback, intentamos obtener por ID si viene
            if datos.get('categoria_id'):
                vehiculo.categoria_id = datos.get('categoria_id')
            if datos.get('carroceria_id'):
                vehiculo.carroceria_id = datos.get('carroceria_id')
            vehiculo.estado = EstadoVehiculo.HABILITADO
            vehiculo.numero_tiv = datos.get('numero_tiv', '')
            vehiculo.fecha_venc_soat = self._parse_date(datos.get('fecha_venc_soat'))
            vehiculo.fecha_venc_citv = self._parse_date(datos.get('fecha_venc_citv'))
            vehiculo.autorizacion_principal = self.tramite.autorizacion
            
            # Actualizar datos de resolución
            if self.tramite.numero_resolucion:
                vehiculo.numero_resolucion = self.tramite.numero_resolucion
            if self.tramite.fecha_resolucion:
                vehiculo.fecha_resolucion = self.tramite.fecha_resolucion
            if self.tramite.archivo_resolucion:
                vehiculo.archivo_resolucion = self.tramite.archivo_resolucion
                
            vehiculo.save()
        else:
            # Crear el vehículo
            vehiculo = Vehiculo.objects.create(
                placa=placa_normalizada,
                empresa_propietaria=self.tramite.empresa,
                marca=datos.get('marca', ''),
                modelo=datos.get('modelo', ''),
                anio_fabricacion=datos.get('anio_fabricacion'),
                color=datos.get('color', ''),
                numero_serie=datos.get('numero_serie', ''),
                numero_motor=datos.get('numero_motor', ''),
                capacidad_sentados=datos.get('capacidad_sentados'),
                peso_bruto=datos.get('peso_bruto'),
                categoria_id=datos.get('categoria_id'),
                carroceria_id=datos.get('carroceria_id'),
                estado=EstadoVehiculo.HABILITADO,
                numero_tiv=datos.get('numero_tiv', ''),
                fecha_venc_soat=self._parse_date(datos.get('fecha_venc_soat')),
                fecha_venc_citv=self._parse_date(datos.get('fecha_venc_citv')),
                autorizacion_principal=self.tramite.autorizacion,
                numero_resolucion=self.tramite.numero_resolucion,
                fecha_resolucion=self.tramite.fecha_resolucion,
                archivo_resolucion=self.tramite.archivo_resolucion,
                creado_por=self.usuario
            )
        
        # Vincular al trámite
        self.tramite.vehiculo = vehiculo
        self.tramite.save()
        
        # Crear habilitación vehicular si hay autorización
        if self.tramite.autorizacion:
            # Dar de baja habilitaciones anteriores
            HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo,
                estado=EstadoHabilitacion.VIGENTE
            ).exclude(autorizacion=self.tramite.autorizacion).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                motivo=f'Baja por nueva habilitación en trámite {self.tramite.numero_expediente}'
            )

            habilitacion = HabilitacionVehicular.objects.create(
                vehiculo=vehiculo,
                autorizacion=self.tramite.autorizacion,
                fecha_inicio=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Incremento de flota - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                # Datos TUC
                numero_tuc=datos.get('numero_tuc', ''),
                fecha_expedicion_tuc=self._parse_date(datos.get('fecha_expedicion_tuc')),
                fecha_autorizacion_transportista=self._parse_date(datos.get('fecha_autorizacion_transportista')),
                fecha_expiracion_transportista=self._parse_date(datos.get('fecha_expiracion_transportista')),
                creado_por=self.usuario
            )
            
            self.resultado['entidades_creadas'].append({
                'tipo': 'Habilitación Vehicular',
                'id': habilitacion.id,
                'descripcion': f'Habilitación para {vehiculo.placa}'
            })
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Vehículo',
            'id': vehiculo.id,
            'descripcion': f'{vehiculo.placa} - {vehiculo.marca} {vehiculo.modelo}'
        })

    # ========== SUSTITUCIÓN DE VEHÍCULO ==========
    def _procesar_sustitucion_vehiculo(self):
        """Sustituye vehículos desde VehiculoTramite."""
        vehiculos_tramite = self.tramite.vehiculos_tramite.all()
        
        if not vehiculos_tramite.exists():
            # Fallback a datos JSON
            datos = self.datos.datos_json.get('vehiculo', {})
            self._sustituir_vehiculo_json(datos)
        else:
            for vt in vehiculos_tramite:
                self._sustituir_vehiculo_vt(vt)
        
        self.resultado['mensaje'] = f'Se procesaron {len(self.resultado["entidades_creadas"])} entidades correctamente.'

    def _sustituir_vehiculo_vt(self, vt):
        """Sustituye un vehículo a partir de VehiculoTramite."""
        vehiculo_saliente = vt.vehiculo_existente
        
        if vehiculo_saliente:
            vehiculo_saliente.estado = EstadoVehiculo.BAJA
            vehiculo_saliente.save()
            
            # Obtener la fecha de resolución del Trámite
            fecha_fin_baja = self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date()
            motivo_baja = f'Sustitución por Resolución N° {self.tramite.numero_resolucion}' if self.tramite.numero_resolucion else f'Sustitución - Trámite {self.tramite.numero_expediente}'
            
            # Dar de baja las habilitaciones activas con la fecha de la resolución
            HabilitacionVehicular.objects.filter(
                vehiculo=vehiculo_saliente,
                estado=EstadoHabilitacion.VIGENTE
            ).update(
                estado=EstadoHabilitacion.BAJA,
                fecha_fin=fecha_fin_baja,
                motivo=motivo_baja
            )
        
        # Crear el nuevo vehículo
        vehiculo_nuevo = Vehiculo.objects.create(
            placa=vt.placa_nueva.upper(),
            empresa_propietaria=self.tramite.empresa,
            marca=vt.marca,
            modelo=vt.modelo,
            anio_fabricacion=vt.anio_fabricacion,
            color=vt.color,
            numero_serie=vt.numero_serie,
            numero_motor=vt.numero_motor,
            capacidad_sentados=vt.capacidad_pasajeros,
            peso_bruto=vt.peso_bruto,
            categoria=vt.categoria,
            carroceria=vt.carroceria,
            estado=EstadoVehiculo.HABILITADO,
            numero_tiv=vt.numero_tarjeta_propiedad,
            fecha_venc_soat=vt.fecha_venc_soat,
            fecha_venc_citv=vt.fecha_venc_citv,
            autorizacion_principal=self.tramite.autorizacion,
            vehiculo_sustituido=vehiculo_saliente,
            numero_resolucion=self.tramite.numero_resolucion,
            fecha_resolucion=self.tramite.fecha_resolucion,
            archivo_resolucion=self.tramite.archivo_resolucion,
            creado_por=self.usuario
        )
        
        # Actualizar referencia
        vt.vehiculo_creado = vehiculo_nuevo
        vt.estado_proceso = 'APROBADO'
        vt.save()
        
        # Crear habilitación para el nuevo vehículo
        if self.tramite.autorizacion:
            habilitacion = HabilitacionVehicular.objects.create(
                vehiculo=vehiculo_nuevo,
                autorizacion=self.tramite.autorizacion,
                fecha_inicio=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Sustitución de {vehiculo_saliente.placa if vehiculo_saliente else "N/A"} - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                # Datos TUC
                numero_tuc=vt.numero_tuc,
                fecha_expedicion_tuc=vt.fecha_expedicion_tuc,
                fecha_autorizacion_transportista=vt.fecha_autorizacion_transportista,
                fecha_expiracion_transportista=vt.fecha_expiracion_transportista,
                creado_por=self.usuario
            )
            
            self.resultado['entidades_creadas'].append({
                'tipo': 'Habilitación Vehicular (Nueva)',
                'id': habilitacion.id,
                'descripcion': f'Habilitación para {vehiculo_nuevo.placa} (TUC: {vt.numero_tuc})'
            })
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Vehículo (Nuevo)',
            'id': vehiculo_nuevo.id,
            'descripcion': f'{vehiculo_nuevo.placa} sustituyó a {vehiculo_saliente.placa if vehiculo_saliente else "N/A"}'
        })

    def _sustituir_vehiculo_json(self, datos):
        """Método original para compatibilidad."""
        # Dar de baja al vehículo saliente
        vehiculo_saliente_id = datos.get('vehiculo_saliente')
        vehiculo_saliente = None
        
        if vehiculo_saliente_id:
            vehiculo_saliente = Vehiculo.objects.filter(id=vehiculo_saliente_id).first()
            if vehiculo_saliente:
                vehiculo_saliente.estado = EstadoVehiculo.BAJA
                vehiculo_saliente.save()
                
                # Dar de baja las habilitaciones activas
                HabilitacionVehicular.objects.filter(
                    vehiculo=vehiculo_saliente,
                    estado=EstadoHabilitacion.VIGENTE
                ).update(
                    estado=EstadoHabilitacion.BAJA,
                    fecha_fin=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                    motivo=f'Sustitución - Trámite {self.tramite.numero_expediente}'
                )
        
        # Crear el nuevo vehículo
        vehiculo_nuevo = Vehiculo.objects.create(
            placa=datos.get('placa', '').upper(),
            empresa_propietaria=self.tramite.empresa,
            marca=datos.get('marca', ''),
            modelo=datos.get('modelo', ''),
            anio_fabricacion=datos.get('anio_fabricacion'),
            color=datos.get('color', ''),
            numero_serie=datos.get('numero_serie', ''),
            numero_motor=datos.get('numero_motor', ''),
            capacidad_sentados=datos.get('capacidad_sentados'),
            categoria_id=datos.get('categoria_id'),
            carroceria_id=datos.get('carroceria_id'),
            estado=EstadoVehiculo.HABILITADO,
            numero_tiv=datos.get('numero_tiv', ''),
            fecha_venc_soat=self._parse_date(datos.get('fecha_venc_soat')),
            fecha_venc_citv=self._parse_date(datos.get('fecha_venc_citv')),
            autorizacion_principal=self.tramite.autorizacion,
            vehiculo_sustituido=vehiculo_saliente,
            numero_resolucion=self.tramite.numero_resolucion,
            fecha_resolucion=self.tramite.fecha_resolucion,
            archivo_resolucion=self.tramite.archivo_resolucion,
            creado_por=self.usuario
        )
        
        # Vincular al trámite
        self.tramite.vehiculo = vehiculo_nuevo
        self.tramite.save()
        
        # Crear habilitación para el nuevo vehículo
        if self.tramite.autorizacion:
            HabilitacionVehicular.objects.create(
                vehiculo=vehiculo_nuevo,
                autorizacion=self.tramite.autorizacion,
                fecha_inicio=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Sustitución de {vehiculo_saliente.placa if vehiculo_saliente else "N/A"} - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                # Datos TUC
                numero_tuc=datos.get('numero_tuc', ''),
                fecha_expedicion_tuc=self._parse_date(datos.get('fecha_expedicion_tuc')),
                fecha_autorizacion_transportista=self._parse_date(datos.get('fecha_autorizacion_transportista')),
                fecha_expiracion_transportista=self._parse_date(datos.get('fecha_expiracion_transportista')),
                creado_por=self.usuario
            )
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Vehículo (Nuevo)',
            'id': vehiculo_nuevo.id,
            'descripcion': f'{vehiculo_nuevo.placa} sustituyó a {vehiculo_saliente.placa if vehiculo_saliente else "N/A"}'
        })

    # ========== BAJA DE VEHÍCULO ==========
    def _procesar_baja_vehiculo(self):
        """Da de baja vehículos desde VehiculoTramite."""
        vehiculos_tramite = self.tramite.vehiculos_tramite.all()
        
        if not vehiculos_tramite.exists():
            # Fallback a datos JSON
            datos = self.datos.datos_json.get('baja_vehiculo', {})
            vehiculo = self.tramite.vehiculo
            if vehiculo:
                self._dar_baja_vehiculo(vehiculo, datos.get('motivo_baja'))
        else:
            for vt in vehiculos_tramite:
                if vt.vehiculo_existente:
                    self._dar_baja_vehiculo(vt.vehiculo_existente, vt.observaciones)
                    vt.estado_proceso = 'APROBADO'
                    vt.save()
        
        self.resultado['mensaje'] = f'Se procesaron {len(self.resultado["entidades_creadas"])} bajas de vehículos.'

    
    def _dar_baja_vehiculo(self, vehiculo, motivo=None):
        """Lógica común para dar de baja un vehículo."""

        # 1) Actualizar estado y datos de resolución del vehículo
        vehiculo.estado = EstadoVehiculo.BAJA
        if self.tramite.fecha_resolucion:
            vehiculo.fecha_resolucion = self.tramite.fecha_resolucion
        if self.tramite.numero_resolucion:
            vehiculo.numero_resolucion = self.tramite.numero_resolucion

        # OJO: durante procesamiento de trámites los signals están desactivados
        vehiculo.save()

        # 2) Cerrar habilitaciones vigentes manualmente
        fecha_fin = self.tramite.fecha_resolucion or timezone.now().date()
        motivo_baja = (
            motivo
            or (
                f'Baja por Resolución N° {self.tramite.numero_resolucion}'
                if self.tramite.numero_resolucion
                else 'Baja por trámite'
            )
        )

        HabilitacionVehicular.objects.filter(
            vehiculo=vehiculo,
            estado=EstadoHabilitacion.VIGENTE
        ).update(
            estado=EstadoHabilitacion.BAJA,
            fecha_fin=fecha_fin,
            motivo=motivo_baja
        )

        self.resultado['entidades_creadas'].append({
            'tipo': 'Vehículo (Baja)',
            'id': vehiculo.id,
            'descripcion': f'{vehiculo.placa} dado de baja'
        })
        
    # ========== HABILITACIÓN DE CONDUCTOR ==========
    def _procesar_habilitacion_conductor(self):
        """Crea o habilita conductores desde ConductorTramite."""
        conductores_tramite = self.tramite.conductores_tramite.all()
        
        if not conductores_tramite.exists():
            # Fallback a datos JSON
            datos = self.datos.datos_json.get('conductor', {})
            if not datos:
                raise ValueError('No hay conductores registrados en el trámite.')
            self._habilitar_conductor_json(datos)
        else:
            for ct in conductores_tramite:
                self._habilitar_conductor_ct(ct)
        
        self.resultado['mensaje'] = f'Se procesaron {len(self.resultado["entidades_creadas"])} habilitaciones de conductores.'

    def _habilitar_conductor_ct(self, ct):
        """Habilita un conductor a partir de ConductorTramite."""
        if ct.conductor_existente:
            conductor = ct.conductor_existente
        else:
            # Fallback: si el CT no trae conductor pero el JSON sí lo indica
            conductor = None
            try:
                datos = self.datos.datos_json.get('conductor', {}) if self.datos else {}
            except Exception:
                datos = {}

            conductor_id = datos.get('conductor_existente')
            if conductor_id:
                conductor = Conductor.objects.filter(id=conductor_id).first()
                if conductor:
                    ct.conductor_existente = conductor
                    if not ct.dni:
                        ct.dni = conductor.dni
                    ct.save()

            # Buscar si ya existe un conductor con ese DNI en el sistema
            if not conductor:
                conductor = Conductor.objects.filter(dni=ct.dni).first()
            
            if conductor:
                # Si existe, actualizamos sus datos con los del trámite
                conductor.nombres = ct.nombres or conductor.nombres
                conductor.apellido_paterno = ct.apellido_paterno or conductor.apellido_paterno
                conductor.apellido_materno = ct.apellido_materno or conductor.apellido_materno
                if ct.fecha_nacimiento:
                    conductor.fecha_nacimiento = ct.fecha_nacimiento
                conductor.direccion = ct.direccion or conductor.direccion
                conductor.telefono = ct.telefono or conductor.telefono
                conductor.email = ct.email or conductor.email
                conductor.licencia_numero = ct.licencia_numero or conductor.licencia_numero
                conductor.licencia_categoria = ct.licencia_categoria or conductor.licencia_categoria
                if ct.licencia_fecha_emision:
                    conductor.licencia_fecha_emision = ct.licencia_fecha_emision
                if ct.licencia_fecha_vencimiento:
                    conductor.licencia_fecha_vencimiento = ct.licencia_fecha_vencimiento
                conductor.estado = EstadoConductor.ACTIVO
                
                # Actualizar datos de resolución
                if self.tramite.numero_resolucion:
                    conductor.numero_resolucion = self.tramite.numero_resolucion
                if self.tramite.fecha_resolucion:
                    conductor.fecha_resolucion = self.tramite.fecha_resolucion
                if self.tramite.archivo_resolucion:
                    conductor.archivo_resolucion = self.tramite.archivo_resolucion
                    
                conductor.save()
                
                self.resultado['entidades_creadas'].append({
                    'tipo': 'Conductor (Actualizado)',
                    'id': conductor.id,
                    'descripcion': f'{conductor.nombre_completo}'
                })
            else:
                if not ct.fecha_nacimiento:
                    raise ValueError('Fecha de nacimiento es obligatoria para crear conductor nuevo.')
                # Crear nuevo conductor si no existe
                conductor = Conductor.objects.create(
                    empresa=self.tramite.empresa,
                    dni=ct.dni,
                    nombres=ct.nombres,
                    apellido_paterno=ct.apellido_paterno,
                    apellido_materno=ct.apellido_materno,
                    fecha_nacimiento=ct.fecha_nacimiento,
                    direccion=ct.direccion,
                    telefono=ct.telefono,
                    email=ct.email,
                    licencia_numero=ct.licencia_numero,
                    licencia_categoria=ct.licencia_categoria,
                    licencia_fecha_emision=ct.licencia_fecha_emision,
                    licencia_fecha_vencimiento=ct.licencia_fecha_vencimiento,
                    estado=EstadoConductor.ACTIVO,
                    numero_resolucion=self.tramite.numero_resolucion,
                    fecha_resolucion=self.tramite.fecha_resolucion,
                    archivo_resolucion=self.tramite.archivo_resolucion,
                    creado_por=self.usuario
                )
                
                self.resultado['entidades_creadas'].append({
                    'tipo': 'Conductor (Nuevo)',
                    'id': conductor.id,
                    'descripcion': f'{conductor.nombre_completo}'
                })
        
        # Actualizar referencia
        ct.conductor_creado = conductor
        ct.estado_proceso = 'APROBADO'
        ct.save()
        
        # Crear habilitación del conductor
        if self.tramite.autorizacion:
            habilitacion = HabilitacionConductor.objects.create(
                conductor=conductor,
                empresa=self.tramite.empresa,
                autorizacion=self.tramite.autorizacion,
                fecha_inicio=timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Habilitación - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                creado_por=self.usuario
            )
            
            self.resultado['entidades_creadas'].append({
                'tipo': 'Habilitación Conductor',
                'id': habilitacion.id,
                'descripcion': f'Habilitación para {conductor.nombre_completo}'
            })

    def _habilitar_conductor_json(self, datos):
        """Método original para compatibilidad."""
        usar_existente = datos.get('usar_conductor_existente', False)
        
        if usar_existente:
            # Usar conductor existente
            conductor_id = datos.get('conductor_existente')
            conductor = Conductor.objects.filter(id=conductor_id).first()
            
            if not conductor:
                raise ValueError('No se encontró el conductor seleccionado.')
        else:
            # Buscar si ya existe un conductor con ese DNI en el sistema
            dni = datos.get('dni', '')
            conductor = Conductor.objects.filter(dni=dni).first()
            
            if conductor:
                # Si existe, actualizamos sus datos con los del trámite
                conductor.nombres = datos.get('nombres', '')
                conductor.apellido_paterno = datos.get('apellido_paterno', '')
                conductor.apellido_materno = datos.get('apellido_materno', '')
                parsed_fn = self._parse_date(datos.get('fecha_nacimiento'))
                if parsed_fn:
                    conductor.fecha_nacimiento = parsed_fn
                conductor.direccion = datos.get('direccion', '')
                conductor.telefono = datos.get('telefono', '')
                conductor.email = datos.get('email', '')
                conductor.licencia_numero = datos.get('licencia_numero', '')
                conductor.licencia_categoria = datos.get('licencia_categoria', '')
                parsed_emision = self._parse_date(datos.get('licencia_fecha_emision'))
                if parsed_emision:
                    conductor.licencia_fecha_emision = parsed_emision
                parsed_venc = self._parse_date(datos.get('licencia_fecha_vencimiento'))
                if parsed_venc:
                    conductor.licencia_fecha_vencimiento = parsed_venc
                conductor.estado = EstadoConductor.ACTIVO
                
                # Actualizar datos de resolución
                if self.tramite.numero_resolucion:
                    conductor.numero_resolucion = self.tramite.numero_resolucion
                if self.tramite.fecha_resolucion:
                    conductor.fecha_resolucion = self.tramite.fecha_resolucion
                if self.tramite.archivo_resolucion:
                    conductor.archivo_resolucion = self.tramite.archivo_resolucion
                    
                conductor.save()
                
                self.resultado['entidades_creadas'].append({
                    'tipo': 'Conductor (Actualizado)',
                    'id': conductor.id,
                    'descripcion': f'{conductor.nombre_completo}'
                })
            else:
                if not self._parse_date(datos.get('fecha_nacimiento')):
                    raise ValueError('Fecha de nacimiento es obligatoria para crear conductor nuevo.')
                # Crear nuevo conductor si no existe
                conductor = Conductor.objects.create(
                    empresa=self.tramite.empresa,
                    dni=dni,
                    nombres=datos.get('nombres', ''),
                    apellido_paterno=datos.get('apellido_paterno', ''),
                    apellido_materno=datos.get('apellido_materno', ''),
                    fecha_nacimiento=self._parse_date(datos.get('fecha_nacimiento')),
                    direccion=datos.get('direccion', ''),
                    telefono=datos.get('telefono', ''),
                    email=datos.get('email', ''),
                    licencia_numero=datos.get('licencia_numero', ''),
                    licencia_categoria=datos.get('licencia_categoria', ''),
                    licencia_fecha_emision=self._parse_date(datos.get('licencia_fecha_emision')),
                    licencia_fecha_vencimiento=self._parse_date(datos.get('licencia_fecha_vencimiento')),
                    estado=EstadoConductor.ACTIVO,
                    numero_resolucion=self.tramite.numero_resolucion,
                    fecha_resolucion=self.tramite.fecha_resolucion,
                    archivo_resolucion=self.tramite.archivo_resolucion,
                    creado_por=self.usuario
                )
                
                self.resultado['entidades_creadas'].append({
                    'tipo': 'Conductor (Nuevo)',
                    'id': conductor.id,
                    'descripcion': f'{conductor.nombre_completo}'
                })
        
        # Vincular al trámite
        self.tramite.conductor = conductor
        self.tramite.save()
        
        # Crear habilitación del conductor
        if self.tramite.autorizacion:
            habilitacion = HabilitacionConductor.objects.create(
                conductor=conductor,
                empresa=self.tramite.empresa,
                autorizacion=self.tramite.autorizacion,
                fecha_inicio=timezone.now().date(),
                estado=EstadoHabilitacion.VIGENTE,
                motivo=f'Habilitación - Trámite {self.tramite.numero_expediente}',
                tramite_origen=self.tramite,
                creado_por=self.usuario
            )
            
            self.resultado['entidades_creadas'].append({
                'tipo': 'Habilitación Conductor',
                'id': habilitacion.id,
                'descripcion': f'Habilitación para {conductor.nombre_completo}'
            })

    # ========== BAJA DE CONDUCTOR ==========
    def _procesar_baja_conductor(self):
        """Da de baja conductores desde ConductorTramite."""
        conductores_tramite = self.tramite.conductores_tramite.all()
        
        if not conductores_tramite.exists():
            # Fallback a datos JSON
            datos = self.datos.datos_json.get('baja_conductor', {})
            conductor = self.tramite.conductor
            if conductor:
                self._dar_baja_conductor(conductor, datos.get('motivo_baja'))
        else:
            for ct in conductores_tramite:
                if ct.conductor_existente:
                    self._dar_baja_conductor(ct.conductor_existente, ct.observaciones)
                    ct.estado_proceso = 'APROBADO'
                    ct.save()
        
        self.resultado['mensaje'] = f'Se procesaron {len(self.resultado["entidades_creadas"])} bajas de conductores.'

    def _dar_baja_conductor(self, conductor, motivo=None):
        """Lógica común para dar de baja un conductor."""
        # Dar de baja las habilitaciones activas del conductor en esta empresa
        habilitaciones = HabilitacionConductor.objects.filter(
            conductor=conductor,
            empresa=self.tramite.empresa,
            estado=EstadoHabilitacion.VIGENTE
        )
        
        habilitaciones.update(
            estado=EstadoHabilitacion.BAJA,
            fecha_fin=self.tramite.fecha_resolucion if self.tramite.fecha_resolucion else timezone.now().date(),
            motivo=motivo or f'Baja - Trámite {self.tramite.numero_expediente}'
        )
        
        self.resultado['entidades_creadas'].append({
            'tipo': 'Conductor (Baja Habilitación)',
            'id': conductor.id,
            'descripcion': f'Habilitación de {conductor.nombre_completo} dada de baja'
        })


def procesar_tramite_aprobado(tramite, usuario):
    """
    Función de conveniencia para procesar un trámite aprobado.
    
    Args:
        tramite: Instancia del trámite aprobado
        usuario: Usuario que procesa el trámite
    
    Returns:
        dict: Resultado del procesamiento
    """
    procesador = TramiteProcesador(tramite, usuario)
    return procesador.procesar()
