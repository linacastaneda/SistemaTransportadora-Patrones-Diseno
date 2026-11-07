from dataclasses import asdict
from pathlib import Path
import secrets
import shutil

import pytest

from encomiendas import create_app
from encomiendas.dominio.modelos import SolicitudRegistro
from encomiendas.persistencia.demo import sembrar_demo
from encomiendas.persistencia.sqlite import UnidadTrabajoSqlite, inicializar


@pytest.fixture(scope="session")
def base_demo(tmp_path_factory):
    ruta = tmp_path_factory.mktemp("plantilla") / "demo.sqlite3"
    inicializar(ruta)
    sembrar_demo(lambda: UnidadTrabajoSqlite(ruta))
    return ruta


@pytest.fixture
def app(tmp_path, base_demo):
    #Cada prueba trabaja sobre una copia; nunca abre la base usada por el navegador.
    ruta = tmp_path / "prueba.sqlite3"
    shutil.copyfile(base_demo, ruta)
    return create_app({"TESTING": True, "SECRET_KEY": "solo-para-pruebas", "DATABASE": str(ruta)})


@pytest.fixture
def uow(app):
    return lambda: UnidadTrabajoSqlite(app.config["DATABASE"])


@pytest.fixture
def servicios(app):
    return app.extensions["servicios"]


@pytest.fixture
def solicitud(uow):
    def crear(venta_id=21, viaje_id=3, **cambios):
        with uow() as u:
            venta = dict(u.db.execute("SELECT * FROM ventas WHERE id=?", (venta_id,)).fetchone())
        campos = {
            k: venta[k]
            for k in (
                "origen_id",
                "destino_id",
                "remitente_nombre",
                "remitente_documento",
                "remitente_telefono",
                "destinatario_nombre",
                "destinatario_documento",
                "destinatario_telefono",
                "direccion_entrega",
            )
        }
        campos.update(
            venta_id=venta_id,
            viaje_id=viaje_id,
            descripcion="Libros de oficina",
            peso_g=8000,
            largo_cm=40,
            ancho_cm=30,
            alto_cm=20,
            valor_centavos=15000000,
        )
        campos.update(cambios)
        return SolicitudRegistro(**campos)

    return crear


@pytest.fixture
def registrar(servicios, solicitud):
    def crear(**cambios):
        return servicios["registro"].registrar(1, solicitud(**cambios), secrets.token_hex(16))

    return crear


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def entrar(correo="coordinador@demo.local", clave="Demo2026!"):
        client.get("/login")
        with client.session_transaction() as sesion:
            token = sesion["csrf"]
        return client.post("/login", data={"correo": correo, "clave": clave, "csrf_token": token})

    return entrar


@pytest.fixture
def post(client):
    def enviar(url, datos=None, **opciones):
        client.get("/")
        with client.session_transaction() as sesion:
            token = sesion["csrf"]
        return client.post(url, data={**(datos or {}), "csrf_token": token}, **opciones)

    return enviar


@pytest.fixture
def formulario(solicitud):
    def crear(**cambios):
        datos = asdict(solicitud())
        datos.pop("peso_g")
        datos.pop("valor_centavos")
        datos.update(peso_kg="8", valor_declarado="150000", token=secrets.token_hex(16))
        datos.update(cambios)
        return datos

    return crear
