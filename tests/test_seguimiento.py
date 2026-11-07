import sqlite3
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.dominio.modelos import Receptor
from encomiendas.persistencia.sqlite import SqliteEventos

RECEPTOR = Receptor("Ana Gómez", "123456789", "Paquete recibido en buen estado.")


def test_recorrido_completo_persistente(registrar, servicios, uow):
    guia_id = registrar().guia_id
    servicios["seguimiento"].despachar(2, guia_id, 1)
    servicios["viajes"].operar(2, 3, "llegada")
    servicios["seguimiento"].recibir_destino(2, guia_id, 2)
    servicios["seguimiento"].entregar(2, guia_id, 3, RECEPTOR)
    #Una nueva unidad de trabajo reconstruye el State; no depende del objeto de la petición anterior.
    with uow() as u:
        guia = u.guias.obtener(guia_id)
        assert guia.estado.codigo == "ENTREGADO"
        assert guia.version == 4
    detalle = servicios["consultas"].detalle(2, guia_id)
    assert [e["estado_nuevo"] for e in detalle["eventos"]] == [
        "RECIBIDO",
        "EN_TRANSITO",
        "EN_DESTINO",
        "ENTREGADO",
    ]
    assert detalle["eventos"][-1]["receptor_documento"] == RECEPTOR.documento
    assert detalle["acciones"] == ()


@pytest.mark.parametrize("accion", ["recibir_destino", "entregar"])
def test_no_se_saltan_estados(registrar, servicios, accion):
    guia_id = registrar().guia_id
    with pytest.raises(ErrorNegocio) as exc:
        metodo = getattr(servicios["seguimiento"], accion)
        metodo(2, guia_id, 1, *([RECEPTOR] if accion == "entregar" else []))
    assert exc.value.codigo == "TRANSICION_INVALIDA"
    assert servicios["consultas"].detalle(2, guia_id)["version"] == 1


def test_vista_desactualizada_no_repite_transicion(registrar, servicios):
    guia_id = registrar().guia_id
    servicios["seguimiento"].despachar(2, guia_id, 1)
    with pytest.raises(ErrorNegocio) as exc:
        servicios["seguimiento"].despachar(2, guia_id, 1)
    assert exc.value.codigo == "CONFLICTO_VERSION"


def test_salida_requiere_autorizacion(registrar, servicios):
    guia_id = registrar(venta_id=13, viaje_id=2).guia_id
    with pytest.raises(ErrorNegocio) as exc:
        servicios["seguimiento"].despachar(2, guia_id, 1)
    assert exc.value.codigo == "SALIDA_NO_AUTORIZADA"
    servicios["viajes"].operar(2, 2, "autorizar")
    servicios["seguimiento"].despachar(2, guia_id, 1)


def test_no_se_recibe_antes_de_llegar(registrar, servicios):
    guia_id = registrar().guia_id
    servicios["seguimiento"].despachar(2, guia_id, 1)
    with pytest.raises(ErrorNegocio) as exc:
        servicios["seguimiento"].recibir_destino(2, guia_id, 2)
    assert exc.value.codigo == "LLEGADA_NO_REGISTRADA"


def test_viaje_no_llega_con_guias_pendientes(registrar, servicios):
    registrar()
    with pytest.raises(ErrorNegocio) as exc:
        servicios["viajes"].operar(2, 3, "llegada")
    assert exc.value.codigo == "DESPACHO_PENDIENTE"


def test_despachar_cierra_carga_de_viaje(registrar, servicios):
    guia_id = registrar(peso_g=1000).guia_id
    servicios["seguimiento"].despachar(2, guia_id, 1)
    with pytest.raises(ErrorNegocio) as exc:
        registrar(venta_id=22, peso_g=1000)
    assert exc.value.codigo == "TRAYECTO"


@pytest.mark.parametrize(
    "receptor", [Receptor("", "123", "Conforme"), Receptor("Ana Gómez", "123456", "")]
)
def test_receptor_y_constancia_obligatorios(servicios, receptor):
    with pytest.raises(ErrorNegocio):
        servicios["seguimiento"].entregar(2, 3, 3, receptor)
    assert servicios["consultas"].detalle(2, 3)["estado"] == "EN_DESTINO"


@pytest.mark.parametrize("accion", ["despachar", "recibir_destino", "entregar"])
def test_entregado_es_terminal(servicios, accion):
    with pytest.raises(ErrorNegocio) as exc:
        getattr(servicios["seguimiento"], accion)(
            2, 4, 4, *([RECEPTOR] if accion == "entregar" else [])
        )
    assert exc.value.codigo == "TRANSICION_INVALIDA"


def test_operador_no_puede_cambiar_estado(registrar, servicios):
    guia_id = registrar().guia_id
    with pytest.raises(ErrorNegocio) as exc:
        servicios["seguimiento"].despachar(1, guia_id, 1)
    assert exc.value.estado_http == 403


def test_otra_sucursal_no_puede_leer(registrar, servicios):
    guia_id = registrar().guia_id
    with pytest.raises(ErrorNegocio) as exc:
        servicios["consultas"].detalle(3, guia_id)
    assert exc.value.estado_http == 403


def test_base_rechaza_salto_y_modificacion_de_historial(uow):
    with uow() as u:
        with pytest.raises(sqlite3.IntegrityError):
            u.db.execute("UPDATE guias SET estado='ENTREGADO' WHERE id=1")
        with pytest.raises(sqlite3.IntegrityError):
            u.db.execute("UPDATE eventos SET accion='otro' WHERE id=1")
        with pytest.raises(sqlite3.IntegrityError):
            u.db.execute("DELETE FROM eventos WHERE id=1")


def test_dos_sesiones_actualizan_misma_version(registrar, servicios):
    guia_id = registrar().guia_id
    barrera = threading.Barrier(2)

    def competir(_):
        barrera.wait(timeout=5)
        try:
            servicios["seguimiento"].despachar(2, guia_id, 1)
            return "APROBADO"
        except ErrorNegocio as exc:
            return exc.codigo

    with ThreadPoolExecutor(max_workers=2) as equipo:
        resultados = list(equipo.map(competir, (1, 2)))
    assert sorted(resultados) == ["APROBADO", "CONFLICTO_VERSION"]
    detalle = servicios["consultas"].detalle(2, guia_id)
    assert len(detalle["eventos"]) == 2


def test_fallo_bitacora_revierte_estado_y_cierre_de_carga(monkeypatch, registrar, servicios, uow):
    guia_id = registrar().guia_id

    def fallar(*args, **kwargs):
        raise RuntimeError("Fallo simulado en bitácora")

    monkeypatch.setattr(SqliteEventos, "agregar", fallar)
    with pytest.raises(RuntimeError):
        servicios["seguimiento"].despachar(2, guia_id, 1)
    with uow() as u:
        assert u.guias.obtener(guia_id).estado.codigo == "RECIBIDO"
        assert u.viajes.obtener(3).recibe_carga
