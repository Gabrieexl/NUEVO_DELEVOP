"""
URLs para la app conductores.
"""

from django.urls import path
from . import views

app_name = 'conductores'

urlpatterns = [
    path('', views.ConductorListView.as_view(), name='lista'),
    path('crear/', views.ConductorCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.ConductorDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.ConductorUpdateView.as_view(), name='editar'),
    path('exportar/', views.ConductorExportView.as_view(), name='exportar'),
    
    # Habilitaciones
    path('habilitaciones/', views.HabilitacionConductorListView.as_view(), name='habilitaciones'),
]
