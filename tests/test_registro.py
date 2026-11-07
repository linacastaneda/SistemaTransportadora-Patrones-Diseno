from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import secrets
import threading

import pytest

from encomiendas.aplicacion.dominio.cadena import ValidarPersonas, ValidarPaquete
from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from encomiendas.datos.sqlite import SqliteEventos


def test_registro_atomico_con_traza_y_estado_inicial(registrar, servicios, uow):
    registro = registrar()
    guia = servicios["consultas"].detalle(1, registro.guia_id)
    assert guia["estado"] == "RECIBIDO"
    assert guia["version"] == 1
    assert len(guia["pasos"]) == 5
    assert all(p["aprobado"] for p in guia["pasos"])
    assert len(guia["eventos"]) == 1
    with uow() as u:
        assert u.viajes.consultar_carga(3) == (8000, 24000)


@pytest.mark.parametrize(
    "cambios,codigo,pasos",
    [
        ({"remitente_nombre": ""}, "PERSONAS", 1),
        ({"destinatario_telefono": "--- ----"}, "PERSONAS", 1),
        ({"peso_g": 0}, "PAQUETE", 2),
        ({"peso_g": True}, "PAQUETE", 2),
        ({"largo_cm": 201}, "PAQUETE", 2),
        ({"valor_centavos": -1}, "PAQUETE", 2),
        ({"viaje_id": 999}, "TRAYECTO", 3),
        ({"destino_id": 2}, "TRAYECTO", 3),
        ({"remitente_documento": "OTRO-123"}, "PAGO", 4),
        ({"peso_g": 10001}, "CAPACIDAD", 5),
        ({"largo_cm": 200, "ancho_cm": 200, "alto_cm": 200}, "CAPACIDAD", 5),
    ],
)
def test_cadena_se_detiene_sin_escrituras(registrar, uow, cambios, codigo, pasos):
    with pytest.raises(ErrorNegocio) as exc:
        registrar(**cambios)
    assert exc.value.codigo == codigo
    assert len(exc.value.pasos) == pasos
    assert not exc.value.pasos[-1].aprobado
    with uow() as u:
        assert u.db.execute("SELECT COUNT(*) FROM guias").fetchone()[0] == 4
        assert u.viajes.consultar_carga(3) == (0, 0)


@pytest.mark.parametrize("venta_id", [25, 26])
def test_pago_ausente_o_parcial_rechazado(registrar, venta_id):
    with pytest.raises(ErrorNegocio, match="suma de los pagos"):
        registrar(venta_id=venta_id, viaje_id=1)


def test_pagos_invalidos_no_cuentan(registrar, uow):
    with uow() as u:
        u.db.execute("UPDATE pagos SET valido=0 WHERE venta_id=21")
    with pytest.raises(ErrorNegocio, match="suma de los pagos"):
        registrar()


def test_venta_solo_admite_una_guia(registrar):
    registrar()
    with pytest.raises(ErrorNegocio, match="ya está vinculada"):
        registrar()


def test_reintento_mismo_token_no_duplica(servicios, solicitud, uow):
    datos, token = solicitud(), secrets.token_hex(16)
    primero = servicios["registro"].registrar(1, datos, token)
    segundo = servicios["registro"].registrar(1, datos, token)
    assert primero.guia_id == segundo.guia_id
    assert segundo.repetido
    with uow() as u:
        assert (
            u.db.execute(
                "SELECT COUNT(*) FROM eventos WHERE guia_id=?", (primero.guia_id,)
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize("otro_actor", [False, True])
def test_token_no_admite_otro_actor_o_contenido(servicios, solicitud, otro_actor):
    datos, token = solicitud(), secrets.token_hex(16)
    servicios["registro"].registrar(1, datos, token)
    with pytest.raises(ErrorNegocio) as exc:
        servicios["registro"].registrar(
            2 if otro_actor else 1,
            datos if otro_actor else replace(datos, descripcion="Otra descripción"),
            token,
        )
    assert exc.value.codigo == "TOKEN_REUTILIZADO"


def test_error_ultimo_paso_revierte_toda_la_transaccion(monkeypatch, registrar, uow):
    def fallar(*args, **kwargs):
        raise RuntimeError("Fallo simulado al escribir la bitácora")

    monkeypatch.setattr(SqliteEventos, "agregar", fallar)
    with pytest.raises(RuntimeError):
        registrar()
    with uow() as u:
        assert u.db.execute("SELECT COUNT(*) FROM guias").fetchone()[0] == 4
        assert u.viajes.consultar_carga(3) == (0, 0)


def test_dos_conexiones_compiten_por_ultimo_cupo(servicios, solicitud, uow):
    barrera = threading.Barrier(2)

    def competir(venta):
        datos = solicitud(venta_id=venta)
        barrera.wait(timeout=5)
        try:
            servicios["registro"].registrar(1, datos, secrets.token_hex(16))
            return "APROBADO"
        except ErrorNegocio as exc:
            return exc.codigo

    with ThreadPoolExecutor(max_workers=2) as equipo:
        resultados = list(equipo.map(competir, (21, 22)))
    assert sorted(resultados) == ["APROBADO", "CAPACIDAD"]
    with uow() as u:
        assert u.viajes.consultar_carga(3) == (8000, 24000)
        assert u.db.execute("SELECT COUNT(*) FROM guias WHERE viaje_id=3").fetchone()[0] == 1


def test_cadena_rechaza_ciclos():
    primero, segundo = ValidarPersonas(), ValidarPaquete()
    primero.enlazar(segundo)
    with pytest.raises(ValueError, match="ciclos"):
        segundo.enlazar(primero)


def test_origen_fuera_de_sucursal_rechazado(servicios, solicitud):
    with pytest.raises(ErrorNegocio) as exc:
        servicios["registro"].registrar(3, solicitud(), secrets.token_hex(16))
    assert exc.value.estado_http == 403
