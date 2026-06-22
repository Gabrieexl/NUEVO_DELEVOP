from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.autorizaciones.models import Autorizacion
from apps.configuracion.models import Carroceria, CategoriaVehiculo
from apps.empresas.models import EmpresaTransporte
from apps.vehiculos.models import HabilitacionVehicular, Vehiculo
from utils.constants import Roles


class VehiculoDetailViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='adminvehiculo',
            password='secret123',
            dni='87654321',
            rol=Roles.ADMIN_SISTEMA,
        )
        self.client.force_login(self.user)

        self.categoria, _ = CategoriaVehiculo.objects.get_or_create(
            codigo='M2',
            defaults={'nombre': 'Categoría M2'}
        )
        self.carroceria, _ = Carroceria.objects.get_or_create(
            codigo='COUPE',
            defaults={
                'nombre': 'Coupé',
                'descripcion': 'Vehículo tipo coupé',
                'categoria': self.categoria,
            }
        )
        self.empresa = EmpresaTransporte.objects.create(
            ruc='10700809426',
            razon_social='EMPRESA DE PRUEBA 001',
            nombre_comercial='EMPRESA DE PRUEBA 001',
            domicilio_fiscal='Av. Demo 123',
            provincia='Tambopata',
            distrito='Tambopata',
            representante_legal='Representante Demo',
            dni_representante='11112222',
            estado='ACTIVA',
        )
        self.autorizacion = Autorizacion.objects.create(
            empresa=self.empresa,
            numero_resolucion='3562-2025-GOREMAD-GRI/DRTC',
            fecha_resolucion=date(2025, 3, 23),
            fecha_inicio_vigencia=date(2025, 3, 23),
            fecha_fin_vigencia=date(2030, 3, 23),
            ambito='MADRE_DE_DIOS',
            estado='VIGENTE',
            descripcion_rutas='Ruta demo',
        )

    def test_detalle_vehiculo_en_baja_no_muestra_habilitacion_vigente_debajo(self):
        vehiculo = Vehiculo.objects.create(
            placa='MBN302',
            empresa_propietaria=self.empresa,
            autorizacion_principal=self.autorizacion,
            marca='TOYOTA',
            modelo='SUZUKI',
            anio_fabricacion=2019,
            capacidad_sentados=7,
            categoria=self.categoria,
            carroceria=self.carroceria,
            estado='BAJA',
            numero_resolucion='124-GOREMAD/DRTC',
        )

        HabilitacionVehicular.objects.create(
            vehiculo=vehiculo,
            autorizacion=self.autorizacion,
            fecha_inicio=date(2026, 3, 23),
            fecha_fin=date(2026, 3, 23),
            estado='BAJA',
            motivo='Vehículo pasó a estado Baja',
        )
        HabilitacionVehicular.objects.create(
            vehiculo=vehiculo,
            autorizacion=self.autorizacion,
            fecha_inicio=date(2026, 3, 23),
            estado='VIGENTE',
            motivo='Registro legado inconsistente',
        )

        response = self.client.get(
            reverse('vehiculos:detalle', kwargs={'pk': vehiculo.pk})
        )

        self.assertEqual(response.status_code, 200)
        habilitaciones = response.context['habilitaciones']
        self.assertEqual(len(habilitaciones), 1)
        self.assertEqual(habilitaciones[0].estado_mostrar, 'BAJA')