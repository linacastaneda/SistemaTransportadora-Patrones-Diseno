from decimal import Decimal

import pytest


@pytest.fixture
def viaje_form():
    return dict(
        codigo="VIAJE-PRUEBA", origen_id="1", destino_id="2",
        fecha_salida="2026-11-15T08:30", placa="ABC123",
        conductor="María López", ayudante="Luis Ruiz",
        peso_maximo_kg="1250,125", volumen_maximo_m3="0,123456",
    )


@pytest.fixture
def pago_form():
    return dict(venta_id="25", medio="TRANSFERENCIA", referencia="PAGO-PRUEBA", importe_cop="123,45")


def test_viaje_http_convierte_unidades_y_comparte_catalogo(client, login, post, uow, viaje_form):
    login()
    assert post("/operaciones/viajes", viaje_form).status_code == 302
    with uow() as u:
        fila = u.db.execute("SELECT * FROM viajes WHERE codigo='VIAJE-PRUEBA'").fetchone()
        assert fila["peso_maximo_g"] == 1250125
        assert fila["volumen_maximo_cm3"] == 123456
        assert fila["salida_autorizada"] == 0
        assert fila["recibe_carga"] == 1
    assert "VIAJE-PRUEBA" in client.get("/guias/nueva").text
    html = client.get("/viajes").text
    assert "1250,125 kg" in html and "0,123456 m³" in html


@pytest.mark.parametrize("campo,valor,codigo", [
    ("peso_maximo_kg", "1.0001", 400),
    ("volumen_maximo_m3", "0.0000001", 400),
    ("peso_maximo_kg", "NaN", 400),
    ("peso_maximo_kg", "-2", 422),
    ("destino_id", "1", 422),
    ("codigo", "invalido!", 422),
])
def test_viaje_rechazado_conserva_formulario_sin_escrituras(login, post, uow, viaje_form, campo, valor, codigo):
    login()
    with uow() as u:
        antes = u.db.execute("SELECT COUNT(*) FROM viajes").fetchone()[0]
    viaje_form[campo] = valor
    respuesta = post("/operaciones/viajes", viaje_form)
    assert respuesta.status_code == codigo
    assert 'value="María López"' in respuesta.text
    assert 'value="2026-11-15T08:30"' in respuesta.text
    assert 'role="alert"' in respuesta.text
    with uow() as u:
        assert u.db.execute("SELECT COUNT(*) FROM viajes").fetchone()[0] == antes


def test_pago_http_centavos_exactos_y_duplicado(login, post, uow, pago_form):
    login()
    assert post("/operaciones/pagos", pago_form).status_code == 302
    repetido = post("/operaciones/pagos", pago_form)
    assert repetido.status_code == 409 and "PAGO_DUPLICADO" in repetido.text
    assert 'value="123,45"' in repetido.text
    with uow() as u:
        pagos = u.db.execute("SELECT importe_centavos FROM pagos WHERE referencia='TRANSFERENCIA-PAGO-PRUEBA'").fetchall()
        assert len(pagos) == 1 and pagos[0][0] == 12345


@pytest.mark.parametrize("importe,codigo", [("0.001", 400), ("Infinity", 400), ("0", 422), ("999999", 422)])
def test_pago_invalido_no_redondea_ni_pierde_datos(login, post, uow, pago_form, importe, codigo):
    login()
    pago_form["importe_cop"] = importe
    respuesta = post("/operaciones/pagos", pago_form)
    assert respuesta.status_code == codigo
    assert 'value="PAGO-PRUEBA"' in respuesta.text
    assert f'value="{importe}"' in respuesta.text
    with uow() as u:
        assert u.ventas.obtener(25).pagado_centavos == 0


@pytest.mark.parametrize("ruta", ["/operaciones/viajes", "/operaciones/pagos"])
def test_operador_no_accede_a_formularios_ni_escribe(client, login, post, ruta):
    login("operador@demo.local")
    assert client.get(ruta).status_code == 403
    assert post(ruta, {"actor_id": "2"}).status_code == 403
    assert ruta not in client.get("/").text
    assert ruta not in client.get("/viajes").text
    assert ruta not in client.get("/ventas").text


@pytest.mark.parametrize("ruta", ["/operaciones/viajes", "/operaciones/pagos"])
def test_operaciones_exigen_csrf(client, login, ruta):
    login()
    assert client.post(ruta, data={}).status_code == 400


@pytest.mark.parametrize("ruta", ["/operaciones/viajes", "/operaciones/pagos", "/operaciones/pagos?venta_id=25"])
def test_formularios_coordinacion(client, login, ruta):
    login()
    respuesta = client.get(ruta)
    assert respuesta.status_code == 200
    assert "Sistema de transporte y encomiendas" in respuesta.text
    assert 'name="csrf_token"' in respuesta.text


def test_catalogo_pago_muestra_solo_ventas_que_admiten_abonos(client, login, uow):
    login()
    assert 'value="25"' in client.get("/operaciones/pagos").text
    with uow() as u:
        u.db.execute("UPDATE ventas SET activa=0 WHERE id IN (25,26)")
    html = client.get("/operaciones/pagos").text
    assert "No hay ventas disponibles" in html
    assert 'value="25"' not in html and 'value="26"' not in html


def test_inyeccion_en_error_se_muestra_como_texto(login, post, viaje_form):
    login()
    contenido = '"><script>alert(1)</script>'
    viaje_form.update(codigo=contenido)
    html = post("/operaciones/viajes", viaje_form).text
    assert contenido not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_saldar_y_programar_permite_registrar_misma_venta(client, login, post, uow, viaje_form, formulario, solicitud):
    login()
    with uow() as u:
        venta = u.ventas.obtener(25)
        saldo = venta.total_centavos - venta.pagado_centavos
    assert post("/operaciones/pagos", dict(venta_id="25", medio="EFECTIVO", referencia="CIERRE-25", importe_cop=str(Decimal(saldo)/100))).status_code == 302
    assert "VE-0025" not in client.get("/ventas?estado=pendientes").text
    assert "VE-0025" in client.get("/ventas?estado=listas").text
    viaje_form.update(peso_maximo_kg="100", volumen_maximo_m3="1")
    assert post("/operaciones/viajes", viaje_form).status_code == 302
    with uow() as u:
        viaje_id = u.db.execute("SELECT id FROM viajes WHERE codigo='VIAJE-PRUEBA'").fetchone()[0]
    venta = solicitud(venta_id=25, viaje_id=viaje_id)
    datos = formulario(venta_id="25", viaje_id=str(viaje_id))
    for campo in ("origen_id", "destino_id", "remitente_nombre", "remitente_documento", "remitente_telefono", "destinatario_nombre", "destinatario_documento", "destinatario_telefono", "direccion_entrega"):
        datos[campo] = getattr(venta, campo)
    respuesta = post("/guias/nueva", datos)
    assert respuesta.status_code == 302
    detalle = respuesta.headers["Location"]
    assert post(detalle + "/acciones/despachar", {"version": "1"}).status_code == 422
    assert post(f"/viajes/{viaje_id}/autorizar").status_code == 302
    assert post(detalle + "/acciones/despachar", {"version": "1"}).status_code == 302
    assert post(f"/viajes/{viaje_id}/llegada").status_code == 302
    assert post(detalle + "/acciones/recibir_destino", {"version": "2"}).status_code == 302
    assert post(detalle + "/acciones/entregar", {"version": "3", "receptor_nombre": "Ana Gómez", "receptor_documento": "123456789", "constancia": "Recibido conforme."}).status_code == 302
    assert "Recibido conforme." in client.get(detalle + "/imprimir").text


def test_inicio_respeta_ambito_y_filtros(client, login):
    login("medellin@demo.local")
    assert "VE-0025" not in client.get("/").text
    assert "VE-0025" not in client.get("/ventas?estado=pendientes").text
    assert "V-003" not in client.get("/viajes?estado=abiertos").text
    assert client.get("/ventas?estado=inventado").status_code == 400
    assert client.get("/viajes?estado=inventado").status_code == 400


def test_fecha_programada_no_depende_de_zona_del_equipo(app):
    assert app.jinja_env.filters["fecha_local"]("2026-11-15T08:30") == "15/11/2026 08:30"
    assert app.jinja_env.filters["fecha_local"]("2026-11-15") == "15/11/2026"
    assert app.jinja_env.filters["cantidad"](1, 1000000) == "0,000001"
