import pytest


def test_login_incorrecto_y_sesion_valida(client, login):
    assert client.get("/guias").status_code == 302
    assert login(clave="incorrecta").status_code == 401
    assert login().status_code == 302
    assert client.get("/").status_code == 200


@pytest.mark.parametrize(
    "ruta",
    [
        "/",
        "/guias",
        "/guias/nueva",
        "/guias/nueva?venta_id=21",
        "/guias/1",
        "/guias/4/imprimir",
        "/viajes",
        "/ventas",
    ],
)
def test_paginas_autenticadas(client, login, ruta):
    login()
    respuesta = client.get(ruta)
    assert respuesta.status_code == 200
    assert "text/html" in respuesta.content_type
    assert respuesta.headers["X-Frame-Options"] == "DENY"


def test_csrf_requerido_incluso_en_login(client):
    assert (
        client.post(
            "/login", data={"correo": "coordinador@demo.local", "clave": "Demo2026!"}
        ).status_code
        == 400
    )


def test_cuenta_desactivada_pierde_sesion(client, login, uow):
    login()
    with uow() as u:
        u.db.execute("UPDATE empleados SET activo=0 WHERE id=2")
    assert client.get("/guias").status_code == 302


def test_recorrido_http_registro_y_todos_los_estados(client, login, post, formulario):
    login()
    respuesta = post("/guias/nueva", formulario())
    assert respuesta.status_code == 302
    detalle = respuesta.headers["Location"]
    assert post(detalle + "/acciones/despachar", {"version": "1"}).status_code == 302
    assert post("/viajes/3/llegada").status_code == 302
    assert post(detalle + "/acciones/recibir_destino", {"version": "2"}).status_code == 302
    assert (
        post(
            detalle + "/acciones/entregar",
            {
                "version": "3",
                "receptor_nombre": "Ana Gómez",
                "receptor_documento": "123456789",
                "constancia": "Recibido a conformidad.",
            },
        ).status_code
        == 302
    )
    html = client.get(detalle).get_data(as_text=True)
    assert "Recibido a conformidad." in html
    assert "Ana Gómez" in html


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("peso_kg", "NaN"),
        ("peso_kg", "0.0001"),
        ("largo_cm", "1.5"),
        ("venta_id", "mal"),
        ("valor_declarado", "1.001"),
    ],
)
def test_formato_invalido_no_pierde_token(client, login, post, formulario, campo, valor):
    login()
    datos = formulario(**{campo: valor})
    respuesta = post("/guias/nueva", datos)
    assert respuesta.status_code == 400
    assert datos["token"] in respuesta.get_data(as_text=True)


def test_error_cadena_muestra_pasos_y_conserva_formulario(login, post, formulario):
    login()
    respuesta = post("/guias/nueva", formulario(peso_kg="11"))
    assert respuesta.status_code == 422
    html = respuesta.get_data(as_text=True)
    assert "supera la capacidad" in html
    assert "Libros de oficina" in html


def test_contenido_html_escapado(client, login, post, formulario):
    login()
    respuesta = post("/guias/nueva", formulario(descripcion="<script>alert(1)</script>"))
    html = client.get(respuesta.headers["Location"]).get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_identidad_del_actor_se_toma_de_sesion(client, login, post, formulario, uow):
    login("operador@demo.local")
    respuesta = post("/guias/nueva", formulario(actor_id="2", creado_por="2"))
    assert respuesta.status_code == 302
    with uow() as u:
        assert u.db.execute("SELECT creado_por FROM guias WHERE venta_id=21").fetchone()[0] == 1


@pytest.mark.parametrize("buscar", ["' OR 1=1 --", "%", "_"])
def test_busqueda_parametrizada_y_literal(client, login, buscar):
    login()
    respuesta = client.get("/guias", query_string={"q": buscar})
    assert respuesta.status_code == 200
    assert "GE-0000001" not in respuesta.get_data(as_text=True)


def test_reinicializar_y_sembrar_no_borran_operaciones(app, registrar, servicios):
    guia_id = registrar().guia_id
    runner = app.test_cli_runner()
    for comando in ("init-db", "seed-demo", "preparar-demo"):
        resultado = runner.invoke(args=[comando])
        assert resultado.exit_code == 0, resultado.output
    assert servicios["consultas"].detalle(2, guia_id)["numero"] == "GE-0000005"


def test_cierre_de_sesion(client, login, post):
    login()
    assert post("/salir").status_code == 302
    assert client.get("/").status_code == 302
