"""
URLs para la app tramites.
"""

from django.urls import path
from . import views

app_name = 'tramites'

urlpatterns = [
    # Listados
    path('', views.TramiteListView.as_view(), name='lista'),
    path('mis-tramites/', views.MisTramitesView.as_view(), name='mis_tramites'),
    path('pendientes/', views.TramitesPendientesView.as_view(), name='pendientes'),
    
    # CRUD
    path('crear/', views.TramiteCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.TramiteDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.TramiteUpdateView.as_view(), name='editar'),
    
    # Transiciones de estado
    path('<int:pk>/enviar-evaluacion/', views.EnviarEvaluacionView.as_view(), name='enviar_evaluacion'),
    path('<int:pk>/enviar-direccion-administrativa/', views.EnviarDireccionAdministrativaView.as_view(), name='enviar_direccion_administrativa'),
    path('<int:pk>/firmar-derivar-tecnico/', views.FirmarDerivarTecnicoView.as_view(), name='firmar_derivar_tecnico'),
    path('<int:pk>/aprobar-evaluacion/', views.AprobarEvaluacionView.as_view(), name='aprobar_evaluacion'),
    path('<int:pk>/enviar-direccion-general/', views.EnviarDireccionGeneralView.as_view(), name='enviar_direccion_general'),
    path('<int:pk>/observar/', views.ObservarTramiteView.as_view(), name='observar'),
    path('<int:pk>/observar-legal/', views.ObservarLegalView.as_view(), name='observar_legal'),
    path('<int:pk>/subsanar/', views.SubsanarTramiteView.as_view(), name='subsanar'),
    path('<int:pk>/enviar-legal/', views.EnviarLegalView.as_view(), name='enviar_legal'),
    path('<int:pk>/aprobar-legal/', views.AprobarLegalView.as_view(), name='aprobar_legal'),
    path('<int:pk>/aprobar/', views.AprobarTramiteView.as_view(), name='aprobar'),
    path('<int:pk>/denegar/', views.DenegarTramiteView.as_view(), name='denegar'),
    path('<int:pk>/cerrar/', views.CerrarTramiteView.as_view(), name='cerrar'),
    
    # Documentos
    path('<int:pk>/documentos/agregar/', views.AgregarDocumentoView.as_view(), name='agregar_documento'),
    path('<int:pk>/documentos/<int:doc_id>/descargar/', views.DocumentoDownloadView.as_view(), name='documento_descargar'),
    path('<int:pk>/documentos/<int:doc_id>/eliminar/', views.DocumentoDeleteView.as_view(), name='documento_eliminar'),
    
    # Recibos de Pago
    path('<int:pk>/recibos/', views.ReciboPagoListView.as_view(), name='recibos_lista'),
    path('<int:pk>/recibos/agregar/', views.ReciboPagoCreateView.as_view(), name='recibo_agregar'),
    path('recibos/<int:pk>/eliminar/', views.ReciboPagoDeleteView.as_view(), name='recibo_eliminar'),
    
    # Vehículos en Trámite
    path('<int:pk>/vehiculos/', views.VehiculoTramiteListView.as_view(), name='vehiculos_lista'),
    path('<int:pk>/vehiculos/agregar/', views.VehiculoTramiteCreateView.as_view(), name='vehiculo_agregar'),
    path('vehiculos/<int:pk>/editar/', views.VehiculoTramiteUpdateView.as_view(), name='vehiculo_editar'),
    path('vehiculos/<int:pk>/eliminar/', views.VehiculoTramiteDeleteView.as_view(), name='vehiculo_eliminar'),
    
    # Conductores en Trámite
    path('<int:pk>/conductores/', views.ConductorTramiteListView.as_view(), name='conductores_lista'),
    path('<int:pk>/conductores/agregar/', views.ConductorTramiteCreateView.as_view(), name='conductor_agregar'),
    path('conductores/<int:pk>/editar/', views.ConductorTramiteUpdateView.as_view(), name='conductor_editar'),
    path('conductores/<int:pk>/eliminar/', views.ConductorTramiteDeleteView.as_view(), name='conductor_eliminar'),
    
    # AJAX - Filtros en cascada
    path('ajax/autorizacion-por-empresa/<int:empresa_id>/', views.get_autorizacion_por_empresa, name='ajax_autorizacion_empresa'),
    path('ajax/vehiculos-por-empresa/<int:empresa_id>/', views.get_vehiculos_por_empresa, name='ajax_vehiculos_empresa'),
    path('ajax/conductores-por-empresa/<int:empresa_id>/', views.get_conductores_por_empresa, name='ajax_conductores_empresa'),
    
    # Exportar
    path('exportar/', views.TramiteExportView.as_view(), name='exportar'),
]
