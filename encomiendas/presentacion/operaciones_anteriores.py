"""Presentación de los procesos recuperados de la primera entrega.
El controlador HTTP no valida reglas de negocio ni ejecuta SQL.
"""
from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.operaciones_anteriores import (
    ProgramacionViaje, RegistroPago,
)

operaciones = Blueprint("operaciones", __name__)


def entero(campo: str) -> int:
    try:
        return int(request.form.get(campo, ""))
    except (ValueError, TypeError) as exc:
        raise ErrorNegocio("CAMPO_INVALIDO", f"El campo {campo} debe ser un número entero.", 422) from exc


def servicio():
    return current_app.extensions["servicios"]["operaciones"]


@operaciones.get("/")
def inicio():
    catalogos = current_app.extensions["servicios"]["consultas"].catalogos(g.actor.id)
    return render_template("operaciones.html", **catalogos, error=None)


@operaciones.post("/viajes")
def programar_viaje():
    try:
        datos = ProgramacionViaje(
            codigo=request.form.get("codigo", "").strip(),
            origen_id=entero("origen_id"), destino_id=entero("destino_id"),
            fecha_salida=request.form.get("fecha_salida", ""),
            placa=request.form.get("placa", ""),
            conductor=request.form.get("conductor", ""),
            ayudante=request.form.get("ayudante", ""),
            peso_maximo_g=entero("peso_maximo_g"),
            volumen_maximo_cm3=entero("volumen_maximo_cm3"),
        )
        identificador = servicio().programar_viaje(g.actor.id, datos)
        flash(f"Viaje {identificador} programado.", "exito")
        return redirect(url_for("web.viajes"))
    except ErrorNegocio as error:
        catalogos = current_app.extensions["servicios"]["consultas"].catalogos(g.actor.id)
        return render_template("operaciones.html", **catalogos, error=error), error.estado_http


@operaciones.post("/pagos")
def registrar_pago():
    try:
        datos = RegistroPago(
            venta_id=entero("venta_id"),
            medio=request.form.get("medio", "").strip().upper(),
            referencia=request.form.get("referencia", "").strip(),
            importe_centavos=entero("importe_centavos"),
        )
        servicio().registrar_pago(g.actor.id, datos)
        flash("Pago registrado; la venta actualiza su saldo.", "exito")
        return redirect(url_for("web.ventas"))
    except ErrorNegocio as error:
        catalogos = current_app.extensions["servicios"]["consultas"].catalogos(g.actor.id)
        return render_template("operaciones.html", **catalogos, error=error), error.estado_http
