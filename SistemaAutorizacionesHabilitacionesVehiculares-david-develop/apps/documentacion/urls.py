from django.urls import path
from . import views

app_name = 'documentacion'

urlpatterns = [
    path('manuales/', views.ManualesListView.as_view(), name='index'),
    path('manuales/usuarios/', views.ManualUsuariosView.as_view(), name='usuarios'),
    path('manuales/configuracion/', views.ManualConfiguracionView.as_view(), name='configuracion'),
    path('manuales/reportes/', views.ManualReportesView.as_view(), name='reportes'),
    path('manuales/operativo/', views.ManualOperativoView.as_view(), name='operativo'),
]
