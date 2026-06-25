from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'fiscalizacion'

router = DefaultRouter()
router.register(r'actas', views.ActaViewSet, basename='actas')

urlpatterns = [
    path('', views.FiscalizacionIndexView.as_view(), name='index'),
    path('api/', include(router.urls)),
    path('api/estadisticas/', views.estadisticas_api, name='api_estadisticas'),
]
