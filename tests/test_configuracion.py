import secrets

import pytest

from encomiendas import create_app
from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.dominio.modelos import PoliticaPaquete
from encomiendas.persistencia.sqlite import UnidadTrabajoSqlite
from encomiendas.aplicacion.servicios import ServicioRegistroEncomienda


def test_politica_configurada_se_aplica_al_servicio_y_vista(app, solicitud):
    otra = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "prueba-configuracion",
            "DATABASE": app.config["DATABASE"],
            "POLITICA_PAQUETE": PoliticaPaquete(peso_maximo_g=5000),
        }
    )
    with pytest.raises(ErrorNegocio) as exc:
        otra.extensions["servicios"]["registro"].registrar(1, solicitud(), secrets.token_hex(16))
    assert exc.value.codigo == "PAQUETE"
    assert otra.jinja_env.globals["politica"].peso_maximo_g == 5000


def test_base_ocupada_permite_reintento(app, uow, solicitud):
    servicio = ServicioRegistroEncomienda(
        lambda: UnidadTrabajoSqlite(app.config["DATABASE"], timeout=0.01)
    )
    datos, token = solicitud(), secrets.token_hex(16)
    with uow() as bloqueo:
        bloqueo.iniciar()
        with pytest.raises(ErrorNegocio) as exc:
            servicio.registrar(1, datos, token)
        assert exc.value.codigo == "BASE_OCUPADA"
    assert servicio.registrar(1, datos, token).numero == "GE-0000005"
