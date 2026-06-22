"""
URLs para la app consultas.
Consulta por placa requiere autenticación (para inspectores).
Consulta de trámite es pública y está en config/urls.py.
"""

from django.urls import path
from .views import ConsultaPlacaView, ConsultaInternaView, ConsultaConductorView, ConsultaPlacaInternaView, ConsultaDNIInternaView
from .api_views import ConsultaPlacaAPIView, VerificarAPIKeyView, ConsultaConductorAPIView

app_name = 'consultas'

urlpatterns = [
    # Consulta por placa (requiere login - para inspectores)
    path('placa/', ConsultaPlacaView.as_view(), name='consulta_placa'),
    
    # Consulta por conductor (requiere login - para inspectores)
    path('conductor/', ConsultaConductorView.as_view(), name='consulta_conductor'),
    
    # Consulta interna más detallada (requiere login)
    path('interna/', ConsultaInternaView.as_view(), name='consulta_interna'),
    
    # API interna para verificación de placa en formularios
    path('api/internal/placa/<str:placa>/', ConsultaPlacaInternaView.as_view(), name='api_internal_placa'),
    
    # API interna para verificación de DNI en formularios
    path('api/internal/dni/<str:dni>/', ConsultaDNIInternaView.as_view(), name='api_internal_dni'),
]

# URLs de API (se incluyen en config/urls.py bajo /api/)
api_urlpatterns = [
    path('placa/<str:placa>/', ConsultaPlacaAPIView.as_view(), name='api_consulta_placa'),
    path('conductor/<str:dni>/', ConsultaConductorAPIView.as_view(), name='api_consulta_conductor'),
    path('verificar-key/', VerificarAPIKeyView.as_view(), name='api_verificar_key'),
]
