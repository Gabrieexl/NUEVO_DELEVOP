"""
Vistas API para consultas externas.
"""

import time
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .services import ConsultaPlacaService, ConsultaConductorService
from .serializers import ConsultaPlacaResponseSerializer, ErrorResponseSerializer
from .models import RegistroConsulta
from .authentication import APIKeyAuthentication, ConsultaRateThrottle, get_client_ip


class ConsultaPlacaAPIView(APIView):
    """
    API para consulta de información vehicular por placa.
    
    GET /api/consulta/placa/<placa>/
    
    Headers requeridos:
        X-API-Key: <clave_api>
    
    Respuesta exitosa (200):
    {
        "placa": "ABC123",
        "vehiculo": {...},
        "empresa": {...},
        "autorizacion": {...},
        "habilitacion_vehicular": {...},
        "conductores_habilitados": [...],
        "fecha_consulta": "2025-01-15T10:30:00Z",
        "mensaje": "Vehículo habilitado para el servicio"
    }
    
    Errores:
        401: API Key inválida o expirada
        404: Vehículo no encontrado
        429: Límite de consultas excedido
    """
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [AllowAny]  # La autenticación se maneja con API Key
    throttle_classes = [ConsultaRateThrottle]
    
    def get(self, request, placa):
        inicio = time.time()
        placa_normalizada = placa.replace('-', '').replace(' ', '').upper()
        
        # Validar que tenga API Key
        if not hasattr(request, 'api_key') or request.api_key is None:
            return Response(
                {
                    'error': True,
                    'codigo': 'AUTH_REQUIRED',
                    'mensaje': 'Se requiere una API Key válida',
                    'detalle': 'Incluya el header X-API-Key con su clave de acceso'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Realizar consulta
        resultado = ConsultaPlacaService.consultar_placa(placa_normalizada)
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        # Registrar consulta
        registro = RegistroConsulta.objects.create(
            api_key=request.api_key,
            placa_consultada=placa_normalizada,
            ip_origen=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            resultado_exitoso=resultado is not None,
            mensaje_error='' if resultado else 'Vehículo no encontrado',
            tiempo_respuesta_ms=tiempo_ms
        )
        
        # Registrar uso de API Key
        request.api_key.registrar_consulta()
        
        if resultado is None:
            return Response(
                {
                    'error': True,
                    'codigo': 'NOT_FOUND',
                    'mensaje': f'No se encontró información para la placa: {placa_normalizada}',
                    'detalle': 'Verifique que la placa esté correctamente escrita'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ConsultaPlacaResponseSerializer(resultado)
        return Response(serializer.data)


class VerificarAPIKeyView(APIView):
    """
    Endpoint para verificar el estado de una API Key.
    
    GET /api/consulta/verificar-key/
    
    Headers requeridos:
        X-API-Key: <clave_api>
    """
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        if not hasattr(request, 'api_key') or request.api_key is None:
            return Response(
                {
                    'error': True,
                    'codigo': 'INVALID_KEY',
                    'mensaje': 'API Key inválida o no proporcionada'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        api_key = request.api_key
        return Response({
            'valida': True,
            'nombre': api_key.nombre,
            'entidad': api_key.entidad,
            'activa': api_key.activa,
            'fecha_expiracion': api_key.fecha_expiracion,
            'limite_diario': api_key.limite_diario,
            'consultas_hoy': api_key.consultas_hoy,
            'consultas_restantes': (
                api_key.limite_diario - api_key.consultas_hoy 
                if api_key.limite_diario > 0 
                else 'Sin límite'
            ),
            'total_consultas': api_key.total_consultas
        })


class ConsultaConductorAPIView(APIView):
    """
    API para consulta de información de conductor por DNI.
    
    GET /api/consulta/conductor/<dni>/
    
    Headers requeridos:
        X-API-Key: <clave_api>
    
    Respuesta exitosa (200):
    {
        "conductor": {
            "dni": "12345678",
            "nombre_completo": "Juan Perez Garcia",
            "estado": "Activo",
            "licencia": {...}
        },
        "habilitacion_vigente": {...},
        "historial_habilitaciones": [...],
        "fecha_consulta": "2025-01-15T10:30:00Z",
        "mensaje": "Conductor habilitado en Transportes XYZ S.A.C."
    }
    
    Errores:
        401: API Key inválida o expirada
        404: Conductor no encontrado
        429: Límite de consultas excedido
    """
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [AllowAny]  # La autenticación se maneja con API Key
    throttle_classes = [ConsultaRateThrottle]
    
    def get(self, request, dni):
        inicio = time.time()
        # Normalizar DNI: solo números, 8 dígitos
        dni_normalizado = ''.join(c for c in dni if c.isdigit())
        
        # Validar formato
        if len(dni_normalizado) != 8:
            return Response(
                {
                    'error': True,
                    'codigo': 'INVALID_DNI',
                    'mensaje': 'El DNI debe tener exactamente 8 dígitos',
                    'detalle': f'DNI proporcionado: {dni}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga API Key
        if not hasattr(request, 'api_key') or request.api_key is None:
            return Response(
                {
                    'error': True,
                    'codigo': 'AUTH_REQUIRED',
                    'mensaje': 'Se requiere una API Key válida',
                    'detalle': 'Incluya el header X-API-Key con su clave de acceso'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Realizar consulta
        resultado = ConsultaConductorService.consultar_conductor(dni_normalizado)
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        # Registrar consulta (usamos el campo placa_consultada para el DNI)
        registro = RegistroConsulta.objects.create(
            api_key=request.api_key,
            placa_consultada=f'DNI:{dni_normalizado}',
            ip_origen=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            resultado_exitoso=resultado is not None,
            mensaje_error='' if resultado else 'Conductor no encontrado',
            tiempo_respuesta_ms=tiempo_ms
        )
        
        # Registrar uso de API Key
        request.api_key.registrar_consulta()
        
        if resultado is None:
            return Response(
                {
                    'error': True,
                    'codigo': 'NOT_FOUND',
                    'mensaje': f'No se encontró información para el DNI: {dni_normalizado}',
                    'detalle': 'Verifique que el DNI esté correctamente escrito'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(resultado)
