"""
Autenticación por API Key para consultas externas.
"""

import time
from rest_framework import authentication, exceptions
from rest_framework.throttling import SimpleRateThrottle
from .models import APIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Autenticación mediante API Key en header.
    Header: X-API-Key: <clave>
    """
    keyword = 'X-API-Key'
    
    def authenticate(self, request):
        api_key = request.headers.get(self.keyword)
        
        if not api_key:
            return None  # Permite otros métodos de auth
        
        return self.authenticate_credentials(api_key, request)
    
    def authenticate_credentials(self, key, request):
        try:
            api_key_obj = APIKey.objects.get(clave=key)
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('API Key inválida')
        
        if not api_key_obj.esta_vigente():
            raise exceptions.AuthenticationFailed('API Key expirada o inactiva')
        
        if not api_key_obj.puede_consultar():
            raise exceptions.Throttled(
                detail='Límite diario de consultas alcanzado'
            )
        
        # Guardamos el objeto API Key en el request para uso posterior
        request.api_key = api_key_obj
        
        # Retornamos None como usuario y el api_key como auth
        return (None, api_key_obj)


class ConsultaRateThrottle(SimpleRateThrottle):
    """
    Throttling para consultas de API.
    Límite por IP para consultas no autenticadas.
    """
    scope = 'consultas'
    
    def get_cache_key(self, request, view):
        if hasattr(request, 'api_key'):
            # Para API Keys, usamos el ID de la key
            return f"throttle_apikey_{request.api_key.id}"
        
        # Para consultas sin API Key, usamos la IP
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class APIKeyPermission:
    """
    Verifica que la request tenga una API Key válida.
    """
    def has_permission(self, request, view):
        return hasattr(request, 'api_key') and request.api_key is not None


def get_client_ip(request):
    """Obtiene la IP del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
