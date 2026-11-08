from datetime import datetime, timedelta
from decimal import Decimal
import os
from pathlib import Path
import secrets
import sqlite3
from zoneinfo import ZoneInfo

import click
from flask import Flask, render_template

from .aplicacion.servicios import (
    ServicioAcceso,
    ServicioRegistroEncomienda,
    ServicioSeguimiento,
    ServicioViajes,
    ServicioConsultas,
)
from .aplicacion.dominio.errores import ErrorNegocio
from .aplicacion.dominio.estados import TIPOS_ESTADO
from .aplicacion.dominio.modelos import PoliticaPaquete
from .datos.sqlite import UnidadTrabajoSqlite, inicializar
from .datos.demo import sembrar_demo


def clave_local(carpeta):
    ruta = carpeta / "secret.key"
    try:
        descriptor = os.open(ruta, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return ruta.read_text(encoding="ascii").strip()
    #Una clave persistente mantiene válidas las sesiones después de reiniciar el proceso local.
    valor = secrets.token_hex(32)
    with os.fdopen(descriptor, "w") as archivo:
        archivo.write(valor)
    return valor


def create_app(config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="presentacion/templates",
        static_folder="presentacion/static",
    )
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "ENCOMIENDAS_DB", str(Path(app.instance_path) / "encomiendas.sqlite3")
        ),
        SECRET_KEY=os.environ.get("ENCOMIENDAS_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("ENCOMIENDAS_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=64 * 1024,
        POLITICA_PAQUETE=PoliticaPaquete(),
    )
    app.config.from_pyfile("config.py", silent=True)
    if config:
        app.config.update(config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = clave_local(Path(app.instance_path))
    crear_uow = lambda: UnidadTrabajoSqlite(app.config["DATABASE"], app.config.get("DB_TIMEOUT", 5))
    from .aplicacion.operaciones_anteriores import ServicioOperaciones
    app.extensions["servicios"] = dict(
        acceso=ServicioAcceso(crear_uow),
        registro=ServicioRegistroEncomienda(crear_uow, politica=app.config["POLITICA_PAQUETE"]),
        seguimiento=ServicioSeguimiento(crear_uow),
        viajes=ServicioViajes(crear_uow),
        operaciones=ServicioOperaciones(crear_uow),
        consultas=ServicioConsultas(crear_uow),
    )
    from .presentacion.rutas import web, csrf_token

    app.register_blueprint(web)
    from .presentacion.operaciones_anteriores import operaciones
    app.register_blueprint(operaciones, url_prefix="/operaciones")
    app.jinja_env.globals.update(
        csrf_token=csrf_token,
        estados={k: c.etiqueta for k, c in TIPOS_ESTADO.items()},
        politica=app.config["POLITICA_PAQUETE"],
    )

    @app.template_filter("dinero")
    def dinero(centavos):
        return "$ " + f"{Decimal(centavos)/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @app.template_filter("cantidad")
    def cantidad(valor, escala=1):
        #Se muestran todas las cifras útiles: un cm³ no debe verse como cero m³.
        texto = format(Decimal(valor) / Decimal(escala), "f")
        if "." in texto:
            texto = texto.rstrip("0").rstrip(".")
        return texto.replace(".", ",")

    @app.template_filter("fecha_local")
    def fecha_local(valor):
        fecha = datetime.fromisoformat(valor)
        if fecha.tzinfo is not None:
            fecha = fecha.astimezone(ZoneInfo("America/Bogota"))
        return fecha.strftime("%d/%m/%Y" if len(valor) == 10 else "%d/%m/%Y %H:%M")

    @app.template_filter("fecha")
    def fecha(valor):
        return (
            datetime.fromisoformat(valor)
            .astimezone(ZoneInfo("America/Bogota"))
            .strftime("%d/%m/%Y %H:%M")
        )

    @app.after_request
    def proteger_respuesta(respuesta):
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "same-origin"
        respuesta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if not respuesta.mimetype.startswith(
            ("image/", "text/css", "text/javascript", "application/javascript")
        ):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    @app.errorhandler(ErrorNegocio)
    def error_negocio(error):
        return render_template("error.html", error=error), error.estado_http

    @app.errorhandler(404)
    def no_encontrado(error):
        return (
            render_template(
                "error.html",
                error=ErrorNegocio("NO_ENCONTRADO", "La página solicitada no existe.", 404),
            ),
            404,
        )

    @app.errorhandler(413)
    def cuerpo_grande(error):
        return (
            render_template(
                "error.html",
                error=ErrorNegocio(
                    "FORMULARIO_EXTENSO", "La solicitud supera el tamaño permitido.", 413
                ),
            ),
            413,
        )

    @app.errorhandler(sqlite3.OperationalError)
    def error_base(error):
        app.logger.exception("No se pudo completar la operación de persistencia.")
        return (
            render_template(
                "error.html",
                error=ErrorNegocio(
                    "BASE_NO_DISPONIBLE",
                    "No se puede acceder a los datos. Verifica la inicialización y vuelve a intentar.",
                    503,
                ),
            ),
            503,
        )

    @app.cli.command("init-db")
    def init_db():
        inicializar(app.config["DATABASE"])
        click.echo("Esquema preparado. Se conservaron los datos existentes.")

    @app.cli.command("seed-demo")
    def seed_demo():
        sembrar_demo(crear_uow, os.environ.get("ENCOMIENDAS_CLAVE_DEMO", "Demo2026!"))
        click.echo("Datos de demostración disponibles. No se reiniciaron las cuentas existentes.")

    @app.cli.command("preparar-demo")
    def preparar_demo():
        inicializar(app.config["DATABASE"])
        sembrar_demo(crear_uow, os.environ.get("ENCOMIENDAS_CLAVE_DEMO", "Demo2026!"))
        click.echo("Aplicación preparada. Inicia con: python -m flask --app run run")

    return app
