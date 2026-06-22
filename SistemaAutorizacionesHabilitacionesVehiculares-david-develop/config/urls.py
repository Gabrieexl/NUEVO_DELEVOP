"""
URL configuration for config project.

https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Importar vista pública de consulta de trámite
from apps.consultas.views import ConsultaTramiteView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # =============================================
    # CONSULTA PÚBLICA DE TRÁMITE (sin autenticación)
    # =============================================
    path('consulta-tramite/', ConsultaTramiteView.as_view(), name='consulta_tramite_publica'),
    
    # Apps del sistema (requieren autenticación)
    path('usuarios/', include('apps.usuarios.urls')),
    path('empresas/', include('apps.empresas.urls')),
    path('autorizaciones/', include('apps.autorizaciones.urls')),
    path('vehiculos/', include('apps.vehiculos.urls')),
    path('conductores/', include('apps.conductores.urls')),
    path('tramites/', include('apps.tramites.urls')),
    path('consulta/', include('apps.consultas.urls')),  # Consulta por placa (para inspectores)
    path('configuracion/', include('apps.configuracion.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('notificaciones/', include('apps.notificaciones.urls')),  # Sistema de notificaciones
    path('documentacion/', include('apps.documentacion.urls')),
    
    # API de consultas
    path('api/consulta/', include('apps.consultas.api_urls')),
    
    # Redirección de la raíz al dashboard
    path('', lambda request: redirect('usuarios:dashboard')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Personalización del admin
admin.site.site_header = 'DRTC - Sistema de Autorizaciones'
admin.site.site_title = 'DRTC Admin'
admin.site.index_title = 'Administración del Sistema'

