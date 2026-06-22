"""
URLs para el módulo de notificaciones.
"""

from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Vista de lista de notificaciones
    path('', views.NotificacionesListView.as_view(), name='lista'),
    
    # APIs para notificaciones
    path('api/no-leidas/', views.NotificacionesNoLeidasAPI.as_view(), name='api_no_leidas'),
    path('api/marcar-leida/<int:pk>/', views.MarcarNotificacionLeidaAPI.as_view(), name='api_marcar_leida'),
    path('api/marcar-todas-leidas/', views.MarcarTodasLeidasAPI.as_view(), name='api_marcar_todas'),
]
