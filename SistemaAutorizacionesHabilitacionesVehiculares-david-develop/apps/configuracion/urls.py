"""
URLs para la app configuracion.
"""

from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    # Dashboard de configuración
    path('', views.ConfiguracionHomeView.as_view(), name='home'),
    
    # Tipos de Servicio
    path('tipos-servicio/', views.TipoServicioListView.as_view(), name='tiposervicio_lista'),
    path('tipos-servicio/crear/', views.TipoServicioCreateView.as_view(), name='tiposervicio_crear'),
    path('tipos-servicio/<int:pk>/editar/', views.TipoServicioUpdateView.as_view(), name='tiposervicio_editar'),
    path('tipos-servicio/<int:pk>/eliminar/', views.TipoServicioDeleteView.as_view(), name='tiposervicio_eliminar'),
    
    # Carrocerías
    path('carrocerias/', views.CarroceriaListView.as_view(), name='carroceria_lista'),
    path('carrocerias/crear/', views.CarroceriaCreateView.as_view(), name='carroceria_crear'),
    path('carrocerias/<int:pk>/editar/', views.CarroceriaUpdateView.as_view(), name='carroceria_editar'),
    path('carrocerias/<int:pk>/eliminar/', views.CarroceriaDeleteView.as_view(), name='carroceria_eliminar'),
    path('api/carrocerias/', views.GetCarroceriasView.as_view(), name='api_carrocerias'),
    
    # Rutas
    path('rutas/', views.RutaListView.as_view(), name='rutas_lista'),
    path('rutas/crear/', views.RutaCreateView.as_view(), name='rutas_crear'),
    path('rutas/modal/crear/', views.RutaCreateModalView.as_view(), name='rutas_crear_modal'),
    path('rutas/<int:pk>/', views.RutaDetailView.as_view(), name='rutas_detalle'),
    path('rutas/<int:pk>/modal/', views.RutaDetailModalView.as_view(), name='rutas_detalle_modal'),
    path('rutas/<int:pk>/editar/', views.RutaUpdateView.as_view(), name='rutas_editar'),
    path('rutas/<int:pk>/modal/editar/', views.RutaUpdateModalView.as_view(), name='rutas_editar_modal'),
    path('rutas/<int:pk>/eliminar/', views.RutaDeleteView.as_view(), name='rutas_eliminar'),
    
    # Frecuencias
    path('frecuencias/', views.FrecuenciaListView.as_view(), name='frecuencias_lista'),
    path('frecuencias/crear/', views.FrecuenciaCreateView.as_view(), name='frecuencias_crear'),
    path('frecuencias/modal/crear/', views.FrecuenciaCreateModalView.as_view(), name='frecuencias_crear_modal'),
    path('frecuencias/<int:pk>/', views.FrecuenciaDetailView.as_view(), name='frecuencias_detalle'),
    path('frecuencias/<int:pk>/modal/', views.FrecuenciaDetailModalView.as_view(), name='frecuencias_detalle_modal'),
    path('frecuencias/<int:pk>/editar/', views.FrecuenciaUpdateView.as_view(), name='frecuencias_editar'),
    path('frecuencias/<int:pk>/modal/editar/', views.FrecuenciaUpdateModalView.as_view(), name='frecuencias_editar_modal'),
    path('frecuencias/<int:pk>/eliminar/', views.FrecuenciaDeleteView.as_view(), name='frecuencias_eliminar'),
]
