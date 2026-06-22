"""
Serializers para la API de consultas.
"""

from rest_framework import serializers


class VehiculoConsultaSerializer(serializers.Serializer):
    """Serializer para datos de vehículo en consulta."""
    placa = serializers.CharField()
    marca = serializers.CharField()
    modelo = serializers.CharField()
    anio_fabricacion = serializers.IntegerField()
    categoria = serializers.CharField(allow_null=True)
    carroceria = serializers.CharField(source='carroceria.nombre', allow_null=True)
    capacidad_sentados = serializers.IntegerField()
    numero_tiv = serializers.CharField(allow_blank=True)
    fecha_venc_soat = serializers.DateField(allow_null=True)
    fecha_venc_citv = serializers.DateField(allow_null=True)


class EmpresaConsultaSerializer(serializers.Serializer):
    """Serializer para datos de empresa en consulta."""
    ruc = serializers.CharField()
    razon_social = serializers.CharField()
    nombre_comercial = serializers.CharField(allow_blank=True)
    estado = serializers.CharField()
    domicilio_fiscal = serializers.CharField()


class AutorizacionConsultaSerializer(serializers.Serializer):
    """Serializer para datos de autorización en consulta."""
    numero_resolucion = serializers.CharField()
    estado = serializers.CharField()
    tipo_servicio = serializers.CharField()
    ambito = serializers.CharField()
    fecha_inicio_vigencia = serializers.DateField()
    fecha_fin_vigencia = serializers.DateField()
    descripcion_rutas = serializers.CharField()


class HabilitacionVehicularConsultaSerializer(serializers.Serializer):
    """Serializer para datos de habilitación vehicular."""
    estado = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField(allow_null=True)
    motivo = serializers.CharField(allow_blank=True)
    numero_tuc = serializers.CharField(allow_blank=True)
    fecha_expedicion_tuc = serializers.DateField(allow_null=True)
    fecha_autorizacion_transportista = serializers.DateField(allow_null=True)
    fecha_expiracion_transportista = serializers.DateField(allow_null=True)

class HistorialEmpresaVehiculoSerializer(serializers.Serializer):
    """Serializer para historial del vehículo por empresa."""
    empresa = serializers.CharField()
    ruc = serializers.CharField(allow_blank=True)
    estado = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField(allow_null=True)
    numero_tuc = serializers.CharField(allow_blank=True)
    numero_resolucion = serializers.CharField(allow_blank=True)
    es_vigente = serializers.BooleanField()
    motivo = serializers.CharField(allow_blank=True)

class ConductorHabilitadoSerializer(serializers.Serializer):
    """Serializer para conductores habilitados."""
    dni = serializers.CharField()
    nombre_completo = serializers.CharField()
    licencia_categoria = serializers.CharField()
    licencia_fecha_vencimiento = serializers.DateField()
    estado_habilitacion = serializers.CharField()
    fecha_inicio_habilitacion = serializers.DateField()
    fecha_fin_habilitacion = serializers.DateField(allow_null=True)


class ConsultaPlacaResponseSerializer(serializers.Serializer):
    """Serializer para respuesta completa de consulta por placa."""
    placa = serializers.CharField()
    vehiculo = VehiculoConsultaSerializer()
    empresa = EmpresaConsultaSerializer(allow_null=True)
    autorizacion = AutorizacionConsultaSerializer(allow_null=True)
    habilitacion_vehicular = HabilitacionVehicularConsultaSerializer(allow_null=True)
    conductores_habilitados = ConductorHabilitadoSerializer(many=True)
    fecha_consulta = serializers.DateTimeField()
    mensaje = serializers.CharField(allow_blank=True)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de error."""
    error = serializers.BooleanField(default=True)
    codigo = serializers.CharField()
    mensaje = serializers.CharField()
    detalle = serializers.CharField(required=False, allow_blank=True)
