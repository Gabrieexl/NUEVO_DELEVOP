"""
Servicios para consultas.
"""

from django.utils import timezone
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.conductores.models import HabilitacionConductor
from utils.constants import EstadoHabilitacion
from django.db.models import Case, When, IntegerField

class ConsultaPlacaService:
    """
    Servicio para consulta de información por placa.
    """
    
    @staticmethod
    def consultar_placa(placa, autorizacion_id=None):
        """
        Consulta toda la información asociada a una placa.
        
        Args:
            placa: Placa del vehículo a consultar
            autorizacion_id: ID de la autorización para filtrar (opcional)
            
        Returns:
            dict: Diccionario con toda la información o None si no existe
        """
        placa = placa.upper()

        # Buildear filtro base
        habilitacion_filter = {
            'vehiculo__placa': placa,
            'estado': EstadoHabilitacion.VIGENTE
        }
        
        # Si se especifica autorización, filtrar por ella
        if autorizacion_id:
            habilitacion_filter['autorizacion_id'] = autorizacion_id

        # Si hay duplicados de placa, priorizar el vehiculo con habilitacion vigente mas reciente.
        habilitacion_vigente = (
            HabilitacionVehicular.objects.filter(**habilitacion_filter)
            .select_related('vehiculo')
            .order_by('-fecha_inicio', '-id')
            .first()
        )

        if habilitacion_vigente:
            vehiculo = (
                Vehiculo.objects.select_related('empresa_propietaria', 'autorizacion_principal')
                .filter(id=habilitacion_vigente.vehiculo_id)
                .first()
            )
        else:
            vehiculo = (
                Vehiculo.objects.select_related('empresa_propietaria', 'autorizacion_principal')
                .filter(placa=placa)
                .annotate(
                    prioridad_estado=Case(
                        When(estado='HABILITADO', then=0),
                        When(estado='PROPUESTO', then=1),
                        When(estado='NO_HABILITADO', then=2),
                        When(estado='BAJA', then=3),
                        default=9,
                        output_field=IntegerField(),
                    )
                )
                .order_by('prioridad_estado', '-id')
                .first()
            )
        if not vehiculo:
            return None
        
        historial_habilitaciones = HabilitacionVehicular.objects.filter(
            vehiculo__placa=vehiculo.placa
        ).select_related(
            'vehiculo__empresa_propietaria',
            'autorizacion__empresa'
        ).order_by('-fecha_inicio', '-id')

        resultado = {
            'placa': vehiculo.placa,
            'vehiculo': ConsultaPlacaService._serializar_vehiculo(vehiculo),
            'empresa': None,
            'autorizacion': None,
            'habilitacion_vehicular': None,
            'historial_empresas': [
                ConsultaPlacaService._serializar_historial_empresa(h)
                for h in historial_habilitaciones
            ],
            'conductores_habilitados': [],
            'fecha_consulta': timezone.now(),
            'mensaje': ''
        }
        
        # Información de la empresa
        if vehiculo.empresa_propietaria:
            resultado['empresa'] = ConsultaPlacaService._serializar_empresa(
                vehiculo.empresa_propietaria
            )
        
        # Información de la autorización
        # Buscar habilitación vehicular vigente (Fuente de verdad)
        # Si se especificó autorización, respetar ese filtro
        habilitacion_filter = {
            'vehiculo': vehiculo,
            'estado': EstadoHabilitacion.VIGENTE
        }
        if autorizacion_id:
            habilitacion_filter['autorizacion_id'] = autorizacion_id
            
        habilitacion_vigente = HabilitacionVehicular.objects.filter(
            **habilitacion_filter
        ).select_related('autorizacion').first()
        
        # Si se especificó autorización pero no hay habilitación para esa autorización, retornar None
        if autorizacion_id and not habilitacion_vigente:
            return None
        
        if habilitacion_vigente:
            resultado['autorizacion'] = ConsultaPlacaService._serializar_autorizacion(
                habilitacion_vigente.autorizacion
            )
            resultado['habilitacion_vehicular'] = ConsultaPlacaService._serializar_habilitacion_vehicular(
                habilitacion_vigente
            )
        elif vehiculo.autorizacion_principal:
            # Si tiene autorización principal pero no habilitación vigente, mostramos la autorización
            # pero NO inventamos una habilitación. El estado del vehículo indicará si está habilitado o no.
            resultado['autorizacion'] = ConsultaPlacaService._serializar_autorizacion(
                vehiculo.autorizacion_principal
            )
            
            # Si el vehículo está habilitado en su maestro pero no tiene registro de habilitación,
            # es una inconsistencia, pero respetamos el dato maestro para el mensaje.
            # No creamos estructura 'habilitacion_vehicular' falsa.

        # Conductores habilitados para esa autorización/empresa
        if resultado['autorizacion'] and vehiculo.empresa_propietaria:
            # Obtener el ID de la autorización
            aut_id = None
            if habilitacion_vigente:
                aut_id = habilitacion_vigente.autorizacion_id
            elif vehiculo.autorizacion_principal:
                aut_id = vehiculo.autorizacion_principal_id
            
            if aut_id:
                conductores = HabilitacionConductor.objects.filter(
                    empresa=vehiculo.empresa_propietaria,
                    autorizacion_id=aut_id,
                    estado=EstadoHabilitacion.VIGENTE
                ).select_related('conductor')
                
                resultado['conductores_habilitados'] = [
                    ConsultaPlacaService._serializar_conductor_habilitado(h)
                    for h in conductores
                ]
        
        # Generar mensaje de estado
        resultado['mensaje'] = ConsultaPlacaService._generar_mensaje_estado(resultado)
        
        return resultado
    
    @staticmethod
    def _serializar_vehiculo(vehiculo):
        """Serializa datos del vehículo."""
        return {
            'placa': vehiculo.placa,
            'estado': vehiculo.estado,
            'estado_display': vehiculo.get_estado_display(),
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'anio_fabricacion': vehiculo.anio_fabricacion,
            'categoria': vehiculo.categoria.nombre if vehiculo.categoria else '-',
            'categoria_id': vehiculo.categoria.id if vehiculo.categoria else None,
            'carroceria': vehiculo.carroceria.nombre if vehiculo.carroceria else '-',
            'carroceria_id': vehiculo.carroceria.id if vehiculo.carroceria else None,
            'capacidad_sentados': vehiculo.capacidad_sentados,
            'color': vehiculo.color,
            'numero_motor': vehiculo.numero_motor,
            'numero_serie': vehiculo.numero_serie,
            'peso_bruto': str(vehiculo.peso_bruto) if vehiculo.peso_bruto else '',
            'numero_tiv': vehiculo.numero_tiv or '',
            'fecha_venc_soat': vehiculo.fecha_venc_soat,
            'fecha_venc_citv': vehiculo.fecha_venc_citv,
            'numero_resolucion': vehiculo.numero_resolucion or '',
            'fecha_resolucion': vehiculo.fecha_resolucion,
        }
    
    @staticmethod
    def _serializar_empresa(empresa):
        """Serializa datos de la empresa."""
        return {
            'ruc': empresa.ruc,
            'razon_social': empresa.razon_social,
            'nombre_comercial': empresa.nombre_comercial or '',
            'estado': empresa.get_estado_display(),
            'domicilio_fiscal': empresa.domicilio_fiscal
        }
    
    @staticmethod
    def _serializar_autorizacion(autorizacion):
        """Serializa datos de la autorización."""
        return {
            'id': autorizacion.id,
            'numero_resolucion': autorizacion.numero_resolucion,
            'estado': autorizacion.get_estado_display(),
            'tipo_servicio': autorizacion.tipo_servicio.nombre if autorizacion.tipo_servicio else '-',
            'ambito': autorizacion.ambito,
            'fecha_inicio_vigencia': autorizacion.fecha_inicio_vigencia,
            'fecha_fin_vigencia': autorizacion.fecha_fin_vigencia,
            'descripcion_rutas': autorizacion.descripcion_rutas
        }
    
    @staticmethod
    @staticmethod
    def _serializar_habilitacion_vehicular(habilitacion):
        """Serializa datos de habilitación vehicular."""
        return {
            'estado': habilitacion.estado,
            'estado_display': habilitacion.get_estado_display(),
            'fecha_inicio': habilitacion.fecha_inicio,
            'fecha_fin': habilitacion.fecha_fin,
            'motivo': habilitacion.motivo or '',
            'numero_tuc': habilitacion.numero_tuc or '',
            'fecha_expedicion_tuc': habilitacion.fecha_expedicion_tuc,
            'fecha_autorizacion_transportista': habilitacion.fecha_autorizacion_transportista,
            'fecha_expiracion_transportista': habilitacion.fecha_expiracion_transportista
        }
    
    @staticmethod
    def _serializar_historial_empresa(habilitacion):
        """Serializa una fila del historial del vehículo por empresa."""
        empresa = None
        if habilitacion.autorizacion and habilitacion.autorizacion.empresa:
            empresa = habilitacion.autorizacion.empresa
        elif habilitacion.vehiculo and habilitacion.vehiculo.empresa_propietaria:
            empresa = habilitacion.vehiculo.empresa_propietaria

        return {
            'empresa': empresa.razon_social if empresa else 'Sin empresa registrada',
            'ruc': empresa.ruc if empresa else '',
            'estado': habilitacion.get_estado_display(),
            'fecha_inicio': habilitacion.fecha_inicio,
            'fecha_fin': habilitacion.fecha_fin,
            'numero_tuc': habilitacion.numero_tuc or '',
            'numero_resolucion': (
                habilitacion.autorizacion.numero_resolucion
                if habilitacion.autorizacion else ''
            ),
            'es_vigente': habilitacion.estado == EstadoHabilitacion.VIGENTE,
            'motivo': habilitacion.motivo or '',
        }

    @staticmethod
    def _serializar_conductor_habilitado(habilitacion):
        """Serializa datos de conductor habilitado."""
        conductor = habilitacion.conductor
        return {
            'dni': conductor.dni,
            'nombre_completo': conductor.nombre_completo,
            'licencia_categoria': conductor.licencia_categoria,
            'licencia_fecha_vencimiento': conductor.licencia_fecha_vencimiento,
            'estado_habilitacion': habilitacion.get_estado_display(),
            'fecha_inicio_habilitacion': habilitacion.fecha_inicio,
            'fecha_fin_habilitacion': habilitacion.fecha_fin
        }
    
    @staticmethod
    def _generar_mensaje_estado(resultado):
        """Genera un mensaje descriptivo del estado."""
        if not resultado['empresa']:
            return "Vehículo sin empresa asociada"
        
        if not resultado['autorizacion']:
            return "Vehículo sin autorización vigente"
        
        if not resultado['habilitacion_vehicular']:
            return "Vehículo sin habilitación vehicular vigente"
        
        # Verificar documentos vencidos
        vehiculo = resultado['vehiculo']
        hoy = timezone.now().date()
        alertas = []
        
        if vehiculo.get('fecha_venc_soat') and vehiculo['fecha_venc_soat'] < hoy:
            alertas.append("SOAT vencido")
        
        if vehiculo.get('fecha_venc_citv') and vehiculo['fecha_venc_citv'] < hoy:
            alertas.append("CITV vencida")
        
        if alertas:
            return f"ALERTA: {', '.join(alertas)}"
        
        return "Vehículo habilitado para el servicio"


class ConsultaConductorService:
    """
    Servicio para consulta de información por DNI de conductor.
    """
    
    @staticmethod
    def consultar_conductor(dni):
        """
        Consulta toda la información asociada a un conductor por DNI.
        
        Args:
            dni: DNI del conductor a consultar
            
        Returns:
            dict: Diccionario con toda la información o None si no existe
        """
        from apps.conductores.models import Conductor
        
        try:
            conductor = Conductor.objects.select_related(
                'empresa'
            ).get(dni=dni)
        except Conductor.DoesNotExist:
            return None
        
        resultado = {
            'dni': conductor.dni,
            'conductor': ConsultaConductorService._serializar_conductor(conductor),
            'empresa': None,
            'habilitacion_vigente': None,
            'historial_habilitaciones': [],
            'fecha_consulta': timezone.now(),
            'mensaje': ''
        }
        
        # Información de la empresa donde está registrado
        if conductor.empresa:
            resultado['empresa'] = ConsultaConductorService._serializar_empresa(
                conductor.empresa
            )
        
        # Habilitaciones del conductor
        habilitaciones = HabilitacionConductor.objects.filter(
            conductor=conductor
        ).select_related('empresa', 'autorizacion').order_by('-fecha_inicio')
        
        for hab in habilitaciones:
            hab_serializada = ConsultaConductorService._serializar_habilitacion(hab)
            resultado['historial_habilitaciones'].append(hab_serializada)
            
            # Si es vigente y no tenemos una asignada aún, la ponemos como principal
            if hab.esta_vigente and not resultado['habilitacion_vigente']:
                resultado['habilitacion_vigente'] = hab_serializada
        
        # Generar mensaje de estado
        resultado['mensaje'] = ConsultaConductorService._generar_mensaje_estado(resultado)
        
        return resultado
    
    @staticmethod
    def _serializar_conductor(conductor):
        """Serializa datos del conductor."""
        return {
            'dni': conductor.dni,
            'nombre_completo': conductor.nombre_completo,
            'nombres': conductor.nombres,
            'apellido_paterno': conductor.apellido_paterno,
            'apellido_materno': conductor.apellido_materno,
            'fecha_nacimiento': conductor.fecha_nacimiento,
            'edad': conductor.edad,
            'licencia': {
                'numero': conductor.licencia_numero,
                'categoria': conductor.licencia_categoria,
                'fecha_emision': conductor.licencia_fecha_emision,
                'fecha_vencimiento': conductor.licencia_fecha_vencimiento,
                'vigente': conductor.licencia_vigente,
            },
            'numero_resolucion': conductor.numero_resolucion or '',
            'fecha_resolucion': conductor.fecha_resolucion,
            'estado': conductor.get_estado_display(),
            'estado_raw': conductor.estado,  # Añadido para lógica de bloqueo
            'telefono': conductor.telefono or '',
            'email': conductor.email or '',
        }
    
    @staticmethod
    def _serializar_empresa(empresa):
        """Serializa datos de la empresa."""
        return {
            'ruc': empresa.ruc,
            'razon_social': empresa.razon_social,
            'nombre_comercial': empresa.nombre_comercial or '',
            'estado': empresa.get_estado_display(),
            'domicilio_fiscal': empresa.domicilio_fiscal
        }
    
    @staticmethod
    def _serializar_habilitacion(habilitacion):
        """Serializa datos de habilitación del conductor."""
        return {
            'empresa': {
                'ruc': habilitacion.empresa.ruc,
                'razon_social': habilitacion.empresa.razon_social,
                'estado' : habilitacion.empresa.get_estado_display(),
                'estado_raw': habilitacion.empresa.estado,
            } if habilitacion.empresa else None,
            'autorizacion': {
                'numero_resolucion': habilitacion.autorizacion.numero_resolucion,
                'estado': habilitacion.autorizacion.estado,
                'estado_display': habilitacion.autorizacion.get_estado_display(),
                'tipo_servicio': habilitacion.autorizacion.tipo_servicio.nombre if habilitacion.autorizacion.tipo_servicio else '',
                'ambito': habilitacion.autorizacion.ambito
            } if habilitacion.autorizacion else None,
            'estado': habilitacion.estado,
            'estado_display': habilitacion.get_estado_display(),
            'fecha_inicio': habilitacion.fecha_inicio,
            'fecha_fin': habilitacion.fecha_fin,
            'esta_vigente': habilitacion.esta_vigente,
            'motivo': habilitacion.motivo or ''
        }
    
    @staticmethod
    def _generar_mensaje_estado(resultado):
        """Genera un mensaje descriptivo del estado."""
        conductor = resultado['conductor']
        
        if not resultado.get('empresa'):
            return "Conductor sin empresa asociada"
        
        # Verificar licencia vencida
        if not conductor['licencia'].get('vigente', True):
            return "ALERTA: Licencia de conducir VENCIDA"
        
        # Verificar si tiene habilitación vigente
        if resultado.get('habilitacion_vigente'):
             return "Conductor con habilitación VIGENTE"
        
        return "Conductor SIN habilitación vigente"
