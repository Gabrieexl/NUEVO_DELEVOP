"""
Tests del modelo Autorizacion.
"""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from apps.autorizaciones.models import Autorizacion
from apps.configuracion.models import TipoServicio
from .factories import (
    AutorizacionFactory,
    AutorizacionVencidaFactory,
    AutorizacionSuspendidaFactory,
    AutorizacionCanceladaFactory,
)


@pytest.mark.django_db
class TestAutorizacionModel:
    """Tests para el modelo Autorizacion."""
    
    def test_crear_autorizacion(self):
        """Test: Crear una autorización básica."""
        autorizacion = AutorizacionFactory()
        assert autorizacion.pk is not None
        assert autorizacion.empresa is not None
    
    def test_autorizacion_str(self):
        """Test: Representación string de la autorización."""
        autorizacion = AutorizacionFactory(
            numero_resolucion='001-2025-GR-MDD'
        )
        assert '001-2025-GR-MDD' in str(autorizacion)
    
    def test_numero_resolucion_unique(self):
        """Test: Número de resolución debe ser único."""
        AutorizacionFactory(numero_resolucion='001-2025-GR-MDD')
        with pytest.raises(Exception):
            AutorizacionFactory(numero_resolucion='001-2025-GR-MDD')
    
    def test_estado_vigente_por_defecto(self):
        """Test: Estado por defecto es VIGENTE."""
        autorizacion = AutorizacionFactory()
        assert autorizacion.estado == 'VIGENTE'
    
    def test_autorizacion_vencida(self):
        """Test: Crear autorización vencida."""
        autorizacion = AutorizacionVencidaFactory()
        assert autorizacion.estado == 'VENCIDA'
    
    def test_autorizacion_suspendida(self):
        """Test: Crear autorización suspendida."""
        autorizacion = AutorizacionSuspendidaFactory()
        assert autorizacion.estado == 'SUSPENDIDA'
    
    def test_autorizacion_cancelada(self):
        """Test: Crear autorización cancelada."""
        autorizacion = AutorizacionCanceladaFactory()
        assert autorizacion.estado == 'CANCELADA'
    
    def test_fechas_vigencia_validas(self):
        """Test: Fecha fin debe ser mayor a fecha inicio."""
        tipo_servicio, _ = TipoServicio.objects.get_or_create(
            codigo='REGULAR',
            defaults={'nombre': 'Regular', 'descripcion': 'Servicio regular'}
        )
        with pytest.raises(ValidationError):
            autorizacion = Autorizacion(
                numero_resolucion='TEST-001',
                fecha_resolucion=date.today(),
                fecha_inicio_vigencia=date.today(),
                fecha_fin_vigencia=date.today() - timedelta(days=1),  # Fecha inválida
                ambito='MADRE_DE_DIOS',
                tipo_servicio=tipo_servicio,
                descripcion_rutas='Test'
            )
            autorizacion.full_clean()
    
    def test_timestamps_automaticos(self):
        """Test: Timestamps se crean automáticamente."""
        autorizacion = AutorizacionFactory()
        assert autorizacion.fecha_creacion is not None
        assert autorizacion.fecha_actualizacion is not None
    
    def test_relacion_empresa(self):
        """Test: Relación con empresa funciona correctamente."""
        autorizacion = AutorizacionFactory()
        assert autorizacion.empresa is not None
        assert autorizacion.empresa.estado == 'ACTIVA'


@pytest.mark.django_db
class TestAutorizacionQueryset:
    """Tests para el queryset de autorizaciones."""
    
    def test_filtrar_vigentes(self):
        """Test: Filtrar autorizaciones vigentes."""
        AutorizacionFactory.create_batch(3)
        AutorizacionVencidaFactory.create_batch(2)
        
        vigentes = Autorizacion.objects.filter(estado='VIGENTE')
        assert vigentes.count() == 3
    
    def test_filtrar_vencidas(self):
        """Test: Filtrar autorizaciones vencidas."""
        AutorizacionFactory.create_batch(3)
        AutorizacionVencidaFactory.create_batch(2)
        
        vencidas = Autorizacion.objects.filter(estado='VENCIDA')
        assert vencidas.count() == 2
    
    def test_filtrar_por_empresa(self):
        """Test: Filtrar autorizaciones por empresa."""
        autorizacion = AutorizacionFactory()
        AutorizacionFactory.create_batch(2)  # Otras autorizaciones
        
        result = Autorizacion.objects.filter(empresa=autorizacion.empresa)
        assert result.count() == 1
    
    def test_filtrar_por_tipo_servicio(self):
        """Test: Filtrar autorizaciones por tipo de servicio."""
        tipo_regular, _ = TipoServicio.objects.get_or_create(
            codigo='REGULAR',
            defaults={'nombre': 'Regular', 'descripcion': 'Servicio regular'}
        )
        tipo_especial, _ = TipoServicio.objects.get_or_create(
            codigo='ESPECIAL',
            defaults={'nombre': 'Especial', 'descripcion': 'Servicio especial'}
        )
        AutorizacionFactory.create_batch(3, tipo_servicio=tipo_regular)
        AutorizacionFactory.create_batch(2, tipo_servicio=tipo_especial)
        
        regulares = Autorizacion.objects.filter(tipo_servicio=tipo_regular)
        assert regulares.count() == 3
