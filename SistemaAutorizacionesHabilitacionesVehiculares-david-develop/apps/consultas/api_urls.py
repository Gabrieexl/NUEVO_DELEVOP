"""
URLs de API para consultas.
"""

from django.urls import path
from .api_views import ConsultaPlacaAPIView, VerificarAPIKeyView

app_name = 'consultas_api'

urlpatterns = [
    path('placa/<str:placa>/', ConsultaPlacaAPIView.as_view(), name='api_consulta_placa'),
    path('verificar-key/', VerificarAPIKeyView.as_view(), name='api_verificar_key'),
]
