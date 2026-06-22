"""
URLs para la app vehiculos.
"""

from django.urls import path
from . import views

app_name = 'vehiculos'

urlpatterns = [
    path('', views.VehiculoListView.as_view(), name='lista'),
    path('crear/', views.VehiculoCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.VehiculoDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.VehiculoUpdateView.as_view(), name='editar'),
    path('exportar/', views.VehiculoExportView.as_view(), name='exportar'),
    
    # Habilitaciones
    path('habilitaciones/', views.HabilitacionVehicularListView.as_view(), name='habilitaciones'),
]
