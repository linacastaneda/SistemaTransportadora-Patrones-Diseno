#Las rutas conservan su prefijo para mantener los enlaces de la entrega anterior.
from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from .formularios import leer_pago, leer_programacion

operaciones = Blueprint("operaciones", __name__)

#La asociación relaciona una regla rechazada con los campos editables de la vista.
CAMPOS_ERROR = {
    "CODIGO_INVALIDO": ("codigo",),
    "VIAJE_DUPLICADO": ("codigo",),
    "FECHA_INVALIDA": ("fecha_salida",),
    "TRAYECTO_INVALIDO": ("origen_id", "destino_id"),
    "SUCURSAL_INVALIDA": ("origen_id", "destino_id"),
    "TRIPULACION_INVALIDA": ("placa", "conductor", "ayudante"),
    "CAPACIDAD_INVALIDA": ("peso_maximo_kg", "volumen_maximo_m3"),
    "MEDIO_INVALIDO": ("medio",),
    "REFERENCIA_INVALIDA": ("referencia",),
    "PAGO_DUPLICADO": ("referencia",),
    "VENTA_INVALIDA": ("venta_id",),
    "SALDO_INVALIDO": ("importe_cop",),
    "IMPORTE_INVALIDO": ("importe_cop",),
}


def servicios():
    return current_app.extensions["servicios"]


def exigir_coordinacion():
    #También se protege el acceso directo; el servicio vuelve a autorizar la escritura.
    if g.actor.rol != "coordinador":
        raise ErrorNegocio(
            "SIN_PERMISO", "Esta operación requiere el perfil de coordinación.", 403
        )


def formulario(tipo, valores, error=None):
    catalogos = servicios()["consultas"].catalogos(g.actor.id)
    pendientes = [
        v for v in catalogos["ventas"]
        if v["activa"] and not v["guia_numero"] and v["pagado_centavos"] < v["total_centavos"]
    ]
    elegida = next(
        (v for v in pendientes if str(v["id"]) == valores.get("venta_id")), None
    )
    return render_template(
        "operaciones.html", tipo=tipo, valores=valores, error=error,
        campos_error=CAMPOS_ERROR.get(error.codigo, ()) if error else (),
        pendientes=pendientes, elegida=elegida, **catalogos,
    ), error.estado_http if error else 200


@operaciones.get("/")
def inicio():
    return redirect(url_for("web.viajes"))


@operaciones.route("/viajes", methods=["GET", "POST"])
def programar_viaje():
    exigir_coordinacion()
    valores = dict(request.form) if request.method == "POST" else {}
    if request.method == "POST":
        try:
            servicios()["operaciones"].programar_viaje(g.actor.id, leer_programacion(valores))
        except ErrorNegocio as error:
            return formulario("viaje", valores, error)
        flash(f"Viaje {valores['codigo'].strip()} programado. Su salida queda por autorizar.", "exito")
        return redirect(url_for("web.viajes"))
    return formulario("viaje", valores)


@operaciones.route("/pagos", methods=["GET", "POST"])
def registrar_pago():
    exigir_coordinacion()
    valores = (
        dict(request.form) if request.method == "POST"
        else {"venta_id": request.args.get("venta_id", ""), "medio": "EFECTIVO"}
    )
    if request.method == "POST":
        try:
            servicios()["operaciones"].registrar_pago(g.actor.id, leer_pago(valores))
        except ErrorNegocio as error:
            return formulario("pago", valores, error)
        flash("Pago registrado. El saldo de la venta se actualizó correctamente.", "exito")
        return redirect(url_for("web.ventas"))
    return formulario("pago", valores)
