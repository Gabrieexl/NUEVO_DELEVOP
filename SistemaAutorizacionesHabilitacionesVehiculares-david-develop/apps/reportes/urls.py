"""
URLs del módulo de reportes.
"""

from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Página principal de reportes
    path('', views.ReportesIndexView.as_view(), name='index'),
    
    # Estadísticas con gráficos
    path('estadisticas/', views.EstadisticasView.as_view(), name='estadisticas'),
    
    # Reportes PDF
    path('pdf/empresas/', views.ReporteEmpresasPDFView.as_view(), name='pdf_empresas'),
    path('pdf/autorizaciones/', views.ReporteAutorizacionesPDFView.as_view(), name='pdf_autorizaciones'),
    path('pdf/vehiculos/', views.ReporteVehiculosPDFView.as_view(), name='pdf_vehiculos'),
    path('pdf/conductores/', views.ReporteConductoresPDFView.as_view(), name='pdf_conductores'),
    path('pdf/tramites/', views.ReporteTramitesPDFView.as_view(), name='pdf_tramites'),
    path('pdf/resoluciones/', views.ReporteResolucionesPDFView.as_view(), name='pdf_resoluciones'),
    path('pdf/vencimientos/', views.ReporteVencimientosPDFView.as_view(), name='pdf_vencimientos'),
    
    # Ficha completa de empresa
    path('ficha-empresa/', views.SeleccionarEmpresaFichaView.as_view(), name='seleccionar_empresa_ficha'),
    path('ficha-empresa/<int:pk>/', views.FichaEmpresaPDFView.as_view(), name='ficha_empresa'),
    
    # Exportación Excel
    path('excel/empresas/', views.ExportarEmpresasExcelView.as_view(), name='excel_empresas'),
    path('excel/autorizaciones/', views.ExportarAutorizacionesExcelView.as_view(), name='excel_autorizaciones'),
    path('excel/vehiculos/', views.ExportarVehiculosExcelView.as_view(), name='excel_vehiculos'),
    path('excel/conductores/', views.ExportarConductoresExcelView.as_view(), name='excel_conductores'),
    path('excel/tramites/', views.ExportarTramitesExcelView.as_view(), name='excel_tramites'),
]
