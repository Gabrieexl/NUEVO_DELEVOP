from datetime import date, timedelta

import pytest

from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.vehiculos.tests.factories import VehiculoBajaFactory, VehiculoHabilitadoFactory
from utils.constants import EstadoAutorizacion, EstadoVehiculo, TagsBajaAutomatica


@pytest.mark.django_db
def test_autorizacion_vencida_y_vigente_rehabilita_solo_afectados():
    autorizacion = AutorizacionFactory(
        estado=EstadoAutorizacion.VIGENTE,
        fecha_inicio_vigencia=date.today() - timedelta(days=10),
        fecha_fin_vigencia=date.today() + timedelta(days=10),
    )
    vehiculo_habilitado = VehiculoHabilitadoFactory(
        empresa_propietaria=autorizacion.empresa,
        autorizacion_principal=autorizacion,
        observaciones="Disponible",
    )
    vehiculo_baja = VehiculoBajaFactory(
        empresa_propietaria=autorizacion.empresa,
        autorizacion_principal=autorizacion,
        observaciones="Baja anterior",
    )

    autorizacion.estado = EstadoAutorizacion.VENCIDA
    autorizacion.save()

    vehiculo_habilitado.refresh_from_db()
    vehiculo_baja.refresh_from_db()

    assert vehiculo_habilitado.estado == EstadoVehiculo.NO_HABILITADO
    assert TagsBajaAutomatica.NO_HABILITADO_POR_AUTORIZACION_VENCIDA in vehiculo_habilitado.observaciones
    assert vehiculo_baja.estado == EstadoVehiculo.BAJA

    autorizacion.estado = EstadoAutorizacion.VIGENTE
    autorizacion.save()

    vehiculo_habilitado.refresh_from_db()
    vehiculo_baja.refresh_from_db()

    assert vehiculo_habilitado.estado == EstadoVehiculo.HABILITADO
    assert TagsBajaAutomatica.NO_HABILITADO_POR_AUTORIZACION_VENCIDA not in vehiculo_habilitado.observaciones
    assert vehiculo_baja.estado == EstadoVehiculo.BAJA


@pytest.mark.django_db
def test_autorizacion_cancelada_baja_vehiculos_y_no_reactiva_al_volver_vigente():
    autorizacion = AutorizacionFactory(
        estado=EstadoAutorizacion.VIGENTE,
        fecha_inicio_vigencia=date.today() - timedelta(days=10),
        fecha_fin_vigencia=date.today() + timedelta(days=10),
    )
    vehiculo_habilitado = VehiculoHabilitadoFactory(
        empresa_propietaria=autorizacion.empresa,
        autorizacion_principal=autorizacion,
        observaciones="Operativo",
    )

    autorizacion.estado = EstadoAutorizacion.CANCELADA
    autorizacion.save()

    vehiculo_habilitado.refresh_from_db()
    assert vehiculo_habilitado.estado == EstadoVehiculo.BAJA
    assert TagsBajaAutomatica.BAJA_POR_CANCELACION_AUTORIZACION in vehiculo_habilitado.observaciones

    autorizacion.estado = EstadoAutorizacion.VIGENTE
    autorizacion.save()

    vehiculo_habilitado.refresh_from_db()
    assert vehiculo_habilitado.estado == EstadoVehiculo.BAJA