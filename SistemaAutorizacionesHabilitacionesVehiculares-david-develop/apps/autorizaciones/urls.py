"""
URLs para la app autorizaciones.
"""

from django.urls import path
from . import views

app_name = 'autorizaciones'

urlpatterns = [
    path('', views.AutorizacionListView.as_view(), name='lista'),
    path('crear/', views.AutorizacionCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.AutorizacionDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.AutorizacionUpdateView.as_view(), name='editar'),
    path('exportar/', views.AutorizacionExportView.as_view(), name='exportar'),
]
