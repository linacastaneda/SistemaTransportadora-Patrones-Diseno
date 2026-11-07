from datetime import datetime
from zoneinfo import ZoneInfo
import hmac
import secrets

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.dominio.estados import TIPOS_ESTADO
from encomiendas.dominio.modelos import Receptor
from .formularios import entero, leer_solicitud

web = Blueprint("web", __name__)


def servicios():
    return current_app.extensions["servicios"]


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(32)
    return session["csrf"]


@web.before_app_request
def verificar_solicitud():
    g.actor = None
    if request.endpoint == "static":
        return
    if request.method == "POST":
        esperado, recibido = session.get("csrf", ""), request.form.get("csrf_token", "")
        if not esperado or not hmac.compare_digest(esperado, recibido):
            raise ErrorNegocio(
                "CSRF_INVALIDO",
                "El formulario expiró o no es válido. Recarga la página e intenta nuevamente.",
                400,
            )
    if session.get("actor_id") is not None:
        try:
            g.actor = servicios()["acceso"].actor(session["actor_id"])
        except ErrorNegocio:
            session.clear()
    if request.endpoint not in ("web.login", "web.salud", None) and g.actor is None:
        return redirect(url_for("web.login"))


@web.get("/salud")
def salud():
    return {"estado": "ok"}


@web.route("/login", methods=["GET", "POST"])
def login():
    if g.actor:
        return redirect(url_for("web.inicio"))
    error = None
    if request.method == "POST":
        try:
            actor = servicios()["acceso"].autenticar(
                request.form.get("correo", "")[:254], request.form.get("clave", "")
            )
            session.clear()
            session["actor_id"] = actor.id
            session.permanent = True
            return redirect(url_for("web.inicio"))
        except ErrorNegocio as exc:
            error = exc
    return render_template("login.html", error=error), error.estado_http if error else 200


@web.post("/salir")
def salir():
    session.clear()
    return redirect(url_for("web.login"))


@web.get("/")
def inicio():
    consulta = servicios()["consultas"]
    guias, total = consulta.listar(g.actor.id, limite=6)
    catalogos = consulta.catalogos(g.actor.id)
    return render_template(
        "inicio.html",
        guias=guias,
        total=total,
        indicadores=consulta.indicadores(g.actor.id),
        viajes=catalogos["viajes"],
        fecha_hoy=datetime.now(ZoneInfo("America/Bogota")).strftime("%d/%m/%Y"),
    )


@web.get("/guias")
def guias():
    buscar = request.args.get("q", "").strip()[:100]
    estado = request.args.get("estado", "")
    if estado and estado not in TIPOS_ESTADO:
        raise ErrorNegocio("ESTADO_INVALIDO", "El filtro de estado no es válido.", 400)
    pagina = max(1, min(entero(request.args.get("pagina", "1"), "Página"), 100000))
    filas, total = servicios()["consultas"].listar(g.actor.id, buscar, estado, pagina)
    return render_template(
        "guias.html",
        guias=filas,
        total=total,
        pagina=pagina,
        paginas=max(1, (total + 14) // 15),
        buscar=buscar,
        estado=estado,
    )


@web.route("/guias/nueva", methods=["GET", "POST"])
def nueva():
    catalogos = servicios()["consultas"].catalogos(g.actor.id)
    valores = (
        dict(request.form)
        if request.method == "POST"
        else dict(venta_id=request.args.get("venta_id", ""), token=secrets.token_hex(16))
    )
    error = None
    if request.method == "POST":
        try:
            resultado = servicios()["registro"].registrar(
                g.actor.id, leer_solicitud(request.form), request.form.get("token", "")
            )
            flash(
                (
                    "La guía ya estaba registrada; se muestra la operación original."
                    if resultado.repetido
                    else f"Guía {resultado.numero} registrada correctamente."
                ),
                "exito",
            )
            return redirect(url_for("web.detalle", guia_id=resultado.guia_id))
        except ErrorNegocio as exc:
            error = exc
    disponibles = [
        v
        for v in catalogos["ventas"]
        if not v["guia_numero"] or str(v["id"]) == str(valores.get("venta_id"))
    ]
    if request.method == "GET":
        elegida = next(
            (v for v in disponibles if str(v["id"]) == str(valores.get("venta_id"))), None
        )
        if elegida:
            valores.update(
                {
                    k: elegida[k]
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
            )
    return render_template(
        "nueva.html", **catalogos, disponibles=disponibles, valores=valores, error=error
    ), (error.estado_http if error else 200)


@web.get("/guias/<int:guia_id>")
def detalle(guia_id):
    return render_template(
        "detalle.html",
        guia=servicios()["consultas"].detalle(g.actor.id, guia_id),
        error=None,
        impresion=False,
    )


@web.get("/guias/<int:guia_id>/imprimir")
def imprimir(guia_id):
    return render_template(
        "detalle.html",
        guia=servicios()["consultas"].detalle(g.actor.id, guia_id),
        error=None,
        impresion=True,
    )


@web.post("/guias/<int:guia_id>/acciones/<accion>")
def transicion(guia_id, accion):
    try:
        seguimiento = servicios()["seguimiento"]
        version = entero(request.form.get("version"), "Versión")
        if accion == "entregar":
            receptor = Receptor(
                *(
                    request.form.get(k, "").strip()
                    for k in ("receptor_nombre", "receptor_documento", "constancia")
                )
            )
            seguimiento.entregar(g.actor.id, guia_id, version, receptor)
        elif accion == "despachar":
            seguimiento.despachar(g.actor.id, guia_id, version)
        elif accion == "recibir_destino":
            seguimiento.recibir_destino(g.actor.id, guia_id, version)
        else:
            raise ErrorNegocio("ACCION_INVALIDA", "La operación solicitada no existe.", 400)
    except ErrorNegocio as error:
        guia = servicios()["consultas"].detalle(g.actor.id, guia_id)
        return (
            render_template("detalle.html", guia=guia, error=error, impresion=False),
            error.estado_http,
        )
    flash("El seguimiento se actualizó correctamente.", "exito")
    return redirect(url_for("web.detalle", guia_id=guia_id))


@web.get("/viajes")
def viajes():
    return render_template("viajes.html", **servicios()["consultas"].catalogos(g.actor.id))


@web.post("/viajes/<int:viaje_id>/<accion>")
def operar_viaje(viaje_id, accion):
    servicios()["viajes"].operar(g.actor.id, viaje_id, accion)
    flash("La operación del viaje quedó registrada.", "exito")
    return redirect(url_for("web.viajes"))


@web.get("/ventas")
def ventas():
    return render_template("ventas.html", **servicios()["consultas"].catalogos(g.actor.id))
