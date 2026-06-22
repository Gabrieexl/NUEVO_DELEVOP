"""
URLs para la app empresas.
"""

from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.EmpresaListView.as_view(), name='lista'),
    path('crear/', views.EmpresaCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.EmpresaDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.EmpresaUpdateView.as_view(), name='editar'),
    path('exportar/', views.EmpresaExportView.as_view(), name='exportar'),
]
