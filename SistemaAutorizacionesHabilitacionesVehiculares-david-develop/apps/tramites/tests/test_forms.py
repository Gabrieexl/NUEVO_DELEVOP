import pytest

from apps.configuracion.models import Carroceria, CategoriaVehiculo
from apps.tramites.forms import ConductorTramiteForm, VehiculoTramiteForm, VehiculoTUCForm
from apps.tramites.models import VehiculoTramite
from apps.tramites.tests.factories import (
    TramiteAutorizacionInicialFactory,
    TramiteFactory,
    TramiteIncrementoFlotaFactory,
)
from utils.constants import EstadoConductor, TipoTramite


@pytest.mark.django_db
class TestVehiculoTUCForm:
    def test_incremento_flota_numero_tuc_y_expedicion_son_editables_y_opcionales(self):
        tramite = TramiteIncrementoFlotaFactory()
        vehiculo_tramite = VehiculoTramite.objects.create(
            tramite=tramite,
            placa_nueva='ABC123',
        )

        form = VehiculoTUCForm(instance=vehiculo_tramite)

        assert form.fields['numero_tuc'].required is False
        assert form.fields['fecha_expedicion_tuc'].required is False
        assert 'readonly' not in form.fields['numero_tuc'].widget.attrs
        assert 'readonly' not in form.fields['fecha_expedicion_tuc'].widget.attrs

        bound_form = VehiculoTUCForm(
            data={
                'numero_tuc': '',
                'fecha_expedicion_tuc': '',
                'fecha_autorizacion_transportista': '2026-01-01',
                'fecha_expiracion_transportista': '2027-01-01',
            },
            instance=vehiculo_tramite,
        )

        assert bound_form.is_valid(), bound_form.errors

    def test_autorizacion_inicial_numero_tuc_y_expedicion_son_editables_y_opcionales(self):
        tramite = TramiteAutorizacionInicialFactory()
        vehiculo_tramite = VehiculoTramite.objects.create(
            tramite=tramite,
            placa_nueva='AI1234',
        )

        form = VehiculoTUCForm(instance=vehiculo_tramite)

        assert form.fields['numero_tuc'].required is False
        assert form.fields['fecha_expedicion_tuc'].required is False
        assert 'readonly' not in form.fields['numero_tuc'].widget.attrs
        assert 'readonly' not in form.fields['fecha_expedicion_tuc'].widget.attrs

        bound_form = VehiculoTUCForm(
            data={
                'numero_tuc': 'TUC-AI-001',
                'fecha_expedicion_tuc': '2026-01-01',
                'fecha_autorizacion_transportista': '2026-01-01',
                'fecha_expiracion_transportista': '2027-01-01',
            },
            instance=vehiculo_tramite,
        )

        assert bound_form.is_valid(), bound_form.errors

    def test_otros_tramites_mantienen_numero_tuc_y_expedicion_requeridos(self):
        tramite = TramiteFactory(tipo_tramite=TipoTramite.SUSTITUCION_VEHICULO)
        vehiculo_tramite = VehiculoTramite.objects.create(
            tramite=tramite,
            placa_nueva='XYZ789',
        )

        form = VehiculoTUCForm(instance=vehiculo_tramite)

        assert form.fields['numero_tuc'].required is True
        assert form.fields['fecha_expedicion_tuc'].required is True
        assert form.fields['numero_tuc'].widget.attrs.get('readonly') is True
        assert form.fields['fecha_expedicion_tuc'].widget.attrs.get('readonly') is True


@pytest.mark.django_db
class TestVehiculoTramiteForm:
    def test_incremento_flota_limpia_campos_no_permitidos_y_conserva_categoria(self):
        tramite = TramiteIncrementoFlotaFactory()
        categoria, _ = CategoriaVehiculo.objects.get_or_create(
            codigo='M1',
            defaults={'nombre': 'Categoría M1'},
        )
        carroceria, _ = Carroceria.objects.get_or_create(
            categoria=categoria,
            codigo='CONV',
            defaults={'nombre': 'Convertible'},
        )

        form = VehiculoTramiteForm(
            data={
                'placa_nueva': 'ABC-123',
                'marca': 'TOYOTA',
                'modelo': 'HIACE',
                'anio_fabricacion': '2026',
                'categoria': str(categoria.pk),
                'carroceria': str(carroceria.pk),
                'capacidad_pasajeros': '7',
                'peso_bruto': '76546',
                'fecha_venc_soat': '2028-02-20',
                'color': 'Blanco',
                'numero_serie': 'SERIE-1',
                'numero_motor': 'MOTOR-1',
                'numero_tarjeta_propiedad': 'TIV-1',
                'fecha_venc_citv': '2028-03-20',
                'numero_tuc': 'TUC-1',
                'fecha_expedicion_tuc': '2026-01-01',
                'fecha_autorizacion_transportista': '2026-01-01',
                'fecha_expiracion_transportista': '2027-01-01',
                'observaciones': 'No debe guardarse',
            },
            tramite=tramite,
        )

        assert form.is_valid(), form.errors
        assert form.cleaned_data['categoria'] == categoria
        assert form.cleaned_data['color'] == ''
        assert form.cleaned_data['numero_serie'] == ''
        assert form.cleaned_data['numero_motor'] == ''
        assert form.cleaned_data['numero_tarjeta_propiedad'] == ''
        assert form.cleaned_data['fecha_venc_citv'] is None
        assert form.cleaned_data['numero_tuc'] == ''


@pytest.mark.django_db
class TestConductorTramiteForm:
    def test_incremento_flota_muestra_estado_inactivo_en_proceso(self):
        tramite = TramiteIncrementoFlotaFactory()
        form = ConductorTramiteForm(tramite=tramite)

        assert form.fields['estado'].initial == EstadoConductor.INACTIVO
        assert form.fields['estado'].disabled is True
