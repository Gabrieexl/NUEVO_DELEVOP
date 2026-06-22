from datetime import date, timedelta

import pytest

from apps.autorizaciones.tests.factories import AutorizacionFactory
from apps.empresas.tests.factories import EmpresaTransporteFactory
from apps.vehiculos.models import HabilitacionVehicular
from apps.vehiculos.tests.factories import VehiculoBajaFactory, VehiculoHabilitadoFactory
from utils.constants import (
    EstadoAutorizacion,
    EstadoEmpresa,
    EstadoHabilitacion,
    EstadoVehiculo,
    TagsBajaAutomatica,
)


@pytest.mark.django_db
def test_empresa_inactiva_suspenda_y_reactive_solo_vehiculos_afectados():
    empresa = EmpresaTransporteFactory(estado=EstadoEmpresa.ACTIVA)
    autorizacion = AutorizacionFactory(
        empresa=empresa,
        estado=EstadoAutorizacion.VIGENTE,
        fecha_inicio_vigencia=date.today() - timedelta(days=30),
        fecha_fin_vigencia=date.today() + timedelta(days=30),
    )
    vehiculo_habilitado = VehiculoHabilitadoFactory(
        empresa_propietaria=empresa,
        autorizacion_principal=autorizacion,
        observaciones="Vehículo operativo",
    )
    vehiculo_baja = VehiculoBajaFactory(
        empresa_propietaria=empresa,
        autorizacion_principal=autorizacion,
        observaciones="Baja previa por trámite",
    )

    HabilitacionVehicular.objects.create(
        vehiculo=vehiculo_habilitado,
        autorizacion=autorizacion,
        fecha_inicio=date.today() - timedelta(days=10),
        estado=EstadoHabilitacion.VIGENTE,
        motivo="Habilitación vigente",
    )

    empresa.estado = EstadoEmpresa.INACTIVA
    empresa.save()

    autorizacion.refresh_from_db()
    vehiculo_habilitado.refresh_from_db()
    vehiculo_baja.refresh_from_db()

    assert autorizacion.estado == EstadoAutorizacion.SUSPENDIDA
    assert TagsBajaAutomatica.AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA in autorizacion.observaciones
    assert vehiculo_habilitado.estado == EstadoVehiculo.NO_HABILITADO
    assert TagsBajaAutomatica.NO_HABILITADO_POR_EMPRESA_INACTIVA in vehiculo_habilitado.observaciones
    assert vehiculo_baja.estado == EstadoVehiculo.BAJA

    empresa.estado = EstadoEmpresa.ACTIVA
    empresa.save()

    autorizacion.refresh_from_db()
    vehiculo_habilitado.refresh_from_db()
    vehiculo_baja.refresh_from_db()

    assert autorizacion.estado == EstadoAutorizacion.VIGENTE
    assert TagsBajaAutomatica.AUT_SUSPENDIDA_POR_EMPRESA_INACTIVA not in autorizacion.observaciones
    assert vehiculo_habilitado.estado == EstadoVehiculo.HABILITADO
    assert TagsBajaAutomatica.NO_HABILITADO_POR_EMPRESA_INACTIVA not in vehiculo_habilitado.observaciones
    assert vehiculo_baja.estado == EstadoVehiculo.BAJA