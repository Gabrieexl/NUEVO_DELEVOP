import pytest
import requests
from django.utils import timezone
from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import Vehiculo, HabilitacionVehicular
from apps.configuracion.models import Carroceria, TipoServicio, CategoriaVehiculo
from apps.autorizaciones.models import Autorizacion
from apps.consultas.models import APIKey

@pytest.mark.django_db
def test_api_consulta_placa(live_server):
    # Crear datos para la consulta
    cat_m3 = CategoriaVehiculo.objects.create(codigo="M3", nombre="Categoría M3")
    tipo_v = Carroceria.objects.create(codigo="BUS", nombre="Bus", descripcion="Bus", categoria=cat_m3)
    tipo_s = TipoServicio.objects.create(nombre="REGULAR", descripcion="Servicio Regular")
    empresa = EmpresaTransporte.objects.create(
        ruc="20987654321",
        razon_social="Transportes API S.A.",
        domicilio_fiscal="Av. API 456",
        representante_legal="Juan API",
        dni_representante="87654321"
    )
    autorizacion = Autorizacion.objects.create(
        empresa=empresa,
        numero_resolucion="RES-API-001",
        fecha_resolucion=timezone.now().date(),
        fecha_inicio_vigencia=timezone.now().date(),
        fecha_fin_vigencia=timezone.now().date() + timezone.timedelta(days=365),
        ambito="MADRE_DE_DIOS",
        tipo_servicio=tipo_s,
        estado="VIGENTE"
    )
    vehiculo = Vehiculo.objects.create(
        placa="API-123",
        empresa_propietaria=empresa,
        marca="Toyota",
        modelo="Coaster",
        anio_fabricacion=2021,
        capacidad_sentados=25,
        carroceria=tipo_v
    )
    HabilitacionVehicular.objects.create(
        vehiculo=vehiculo,
        autorizacion=autorizacion,
        fecha_inicio=timezone.now().date(),
        estado='VIGENTE',
        numero_tuc="TUC-API-001"
    )

    # Crear API Key
    api_key = APIKey.objects.create(
        nombre="Test Key",
        clave="test-api-key-123",
        activa=True,
        limite_diario=100,
        fecha_expiracion=timezone.now().date() + timezone.timedelta(days=30)
    )

    # Realizar consulta API
    url = f"{live_server.url}/api/consulta/placa/API-123/"
    headers = {"X-API-Key": "test-api-key-123"}
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["placa"] == "API123"
    assert data["empresa"]["razon_social"] == "Transportes API S.A."
    assert data["habilitacion_vehicular"]["estado"] == "Vigente"
    assert data["autorizacion"]["numero_resolucion"] == "RES-API-001"

@pytest.mark.django_db
def test_api_consulta_placa_sin_key(live_server):
    url = f"{live_server.url}/api/consulta/placa/API-999/"
    response = requests.get(url)
    # Debería fallar o retornar 401/403 dependiendo de la config
    # Según api_views.py: permission_classes = [AllowAny] pero authentication_classes = [APIKeyAuthentication]
    # Si no hay key, authenticate devuelve None.
    # Si devuelve None, request.user es AnonymousUser.
    # Si la vista no requiere permisos adicionales, podría pasar?
    # Revisando api_views.py:
    # def get(self, request, placa):
    #    # Validar que tenga API Key
    #    if not getattr(request, 'api_key', None):
    #        return Response({'error': 'API Key requerida'}, status=status.HTTP_401_UNAUTHORIZED)
    
    assert response.status_code == 401
