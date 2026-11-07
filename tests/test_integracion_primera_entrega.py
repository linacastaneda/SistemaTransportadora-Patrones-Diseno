"""Pruebas de funcionalidades adaptadas del proyecto Java al sistema Flask."""
import pytest

from encomiendas.aplicacion.operaciones_anteriores import (
    ProgramacionViaje, RegistroPago,
)
from encomiendas.dominio.errores import ErrorNegocio


def test_programar_viaje_comparte_repositorio_con_encomiendas(servicios, uow):
    with uow() as u:
        sucursales = [s["id"] for s in u.consultas.sucursales()]
    assert len(sucursales) >= 2
    origen, destino = sucursales[:2]
    nuevo = ProgramacionViaje(
        "INTEGRACION-301", origen, destino, "2026-11-15T08:30",
        "ABC123", "Conductor de prueba", "Ayudante de prueba", 20000, 200000,
    )
    identificador = servicios["operaciones"].programar_viaje(2, nuevo)
    with uow() as u:
        viaje = u.viajes.obtener(identificador)
        assert viaje is not None
        assert viaje.codigo == "INTEGRACION-301"
        assert viaje.recibe_carga
        assert viaje.peso_maximo_g == 20000


def test_trayecto_identico_rechazado(servicios, uow):
    with uow() as u:
        sucursal = u.consultas.sucursales()[0]["id"]
    datos = ProgramacionViaje(
        "INTEGRACION-302", sucursal, sucursal, "2026-11-15T08:30",
        "ABC123", "Conductor", "Ayudante", 10000, 200000,
    )
    with pytest.raises(ErrorNegocio) as exc:
        servicios["operaciones"].programar_viaje(2, datos)
    assert exc.value.codigo == "TRAYECTO_INVALIDO"


def test_pago_saldado_actualiza_venta_original(servicios, uow):
    with uow() as u:
        venta = u.ventas.obtener(25)
        pendiente = venta.total_centavos - venta.pagado_centavos
    assert pendiente > 0
    servicios["operaciones"].registrar_pago(
        2, RegistroPago(25, "TRANSFERENCIA", "REF-NUEVA-25", pendiente)
    )
    with uow() as u:
        venta = u.ventas.obtener(25)
        assert venta.pagado_centavos == venta.total_centavos
    with pytest.raises(ErrorNegocio) as exc:
        servicios["operaciones"].registrar_pago(
            2, RegistroPago(25, "TRANSFERENCIA", "REF-EXTRA-25", 1)
        )
    assert exc.value.codigo == "SALDO_INVALIDO"


def test_pago_por_encima_del_saldo_no_se_registra(servicios, uow):
    with uow() as u:
        venta = u.ventas.obtener(25)
        saldo = venta.total_centavos - venta.pagado_centavos
    with pytest.raises(ErrorNegocio) as exc:
        servicios["operaciones"].registrar_pago(
            2, RegistroPago(25, "EFECTIVO", "REF-EXCESO", saldo + 1)
        )
    assert exc.value.codigo == "SALDO_INVALIDO"
