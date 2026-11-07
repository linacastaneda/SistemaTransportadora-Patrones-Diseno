from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

from werkzeug.security import check_password_hash, generate_password_hash

from encomiendas.dominio.cadena import crear_cadena
from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.dominio.modelos import (
    ContextoRegistro,
    ContextoSeguimiento,
    PoliticaPaquete,
    Receptor,
)


def ahora_utc():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def exigir_actor(uow, actor_id, coordinador=False):
    actor = uow.empleados.obtener(actor_id)
    if actor is None or not actor.activo:
        raise ErrorNegocio(
            "SESION_INVALIDA", "La cuenta no está activa. Inicia sesión nuevamente.", 401
        )
    if coordinador and actor.rol != "coordinador":
        raise ErrorNegocio("SIN_PERMISO", "Esta operación requiere el perfil de coordinación.", 403)
    return actor


def exigir_acceso(actor, guia):
    if guia is None:
        raise ErrorNegocio("NO_ENCONTRADO", "La guía solicitada no existe.", 404)
    if actor.rol != "coordinador" and actor.sucursal_id not in (guia.origen_id, guia.destino_id):
        raise ErrorNegocio("SIN_PERMISO", "La guía no pertenece a tu sucursal.", 403)


class ServicioAcceso:
    def __init__(self, crear_uow):
        self.crear_uow = crear_uow
        self._hash_ausente = generate_password_hash("cuenta-inexistente-no-utilizable")

    def autenticar(self, correo, clave):
        with self.crear_uow() as u:
            r = u.empleados.por_correo(correo.strip().lower())
            valida = check_password_hash(r["clave_hash"] if r else self._hash_ausente, clave)
            if r is None or not valida or not r["activo"]:
                raise ErrorNegocio(
                    "ACCESO_INVALIDO", "Correo o contraseña incorrectos, o cuenta inactiva.", 401
                )
            return u.empleados.obtener(r["id"])

    def actor(self, identificador):
        with self.crear_uow() as u:
            return exigir_actor(u, identificador)


@dataclass(frozen=True)
class RegistroConfirmado:
    guia_id: int
    numero: str
    repetido: bool = False


class ServicioRegistroEncomienda:
    def __init__(self, crear_uow, politica=None, reloj=ahora_utc):
        self.crear_uow, self.reloj = crear_uow, reloj
        self.politica = politica or PoliticaPaquete()
        self.cadena = crear_cadena()

    def registrar(self, actor_id, solicitud, token):
        if not re.fullmatch(r"[a-f0-9]{32}", token or ""):
            raise ErrorNegocio(
                "TOKEN_INVALIDO", "El formulario no es válido. Abre un nuevo registro.", 400
            )
        #La huella vincula el reintento al mismo contenido y al mismo empleado.
        huella = hashlib.sha256(
            json.dumps(asdict(solicitud), sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        with self.crear_uow() as u:
            u.iniciar()
            actor = exigir_actor(u, actor_id)
            if actor.rol != "coordinador" and actor.sucursal_id != solicitud.origen_id:
                raise ErrorNegocio(
                    "SIN_PERMISO", "Solo puedes registrar envíos desde tu sucursal.", 403
                )
            existente = u.guias.por_token(token)
            if existente:
                if existente["creado_por"] != actor.id or existente["huella"] != huella:
                    raise ErrorNegocio(
                        "TOKEN_REUTILIZADO",
                        "Este formulario ya fue utilizado con otros datos. Abre un nuevo registro.",
                        409,
                    )
                return RegistroConfirmado(existente["id"], existente["numero"], True)
            peso, volumen = u.viajes.consultar_carga(solicitud.viaje_id)
            ctx = ContextoRegistro(
                solicitud,
                u.ventas.obtener(solicitud.venta_id),
                u.viajes.obtener(solicitud.viaje_id),
                peso,
                volumen,
                frozenset(s["id"] for s in u.consultas.sucursales()),
                self.politica,
            )
            resultado = self.cadena.validar(ctx)
            if not resultado.aprobado:
                raise ErrorNegocio(resultado.codigo, resultado.mensaje, 422, resultado.pasos)
            fecha = self.reloj()
            guia = u.guias.guardar(solicitud, actor.id, token, huella, fecha, resultado.pasos)
            u.asignaciones.guardar(guia.id, solicitud)
            u.eventos.agregar(guia.id, None, "RECIBIDO", "registrar", actor.id, fecha)
            u.confirmar()
            return RegistroConfirmado(guia.id, guia.numero)


class ServicioSeguimiento:
    def __init__(self, crear_uow, reloj=ahora_utc):
        self.crear_uow, self.reloj = crear_uow, reloj

    def despachar(self, actor_id, guia_id, version):
        self._operar(actor_id, guia_id, version, "despachar")

    def recibir_destino(self, actor_id, guia_id, version):
        self._operar(actor_id, guia_id, version, "recibir_destino")

    def entregar(self, actor_id, guia_id, version, receptor: Receptor):
        self._operar(actor_id, guia_id, version, "entregar", receptor)

    def _operar(self, actor_id, guia_id, version, accion, receptor=None):
        with self.crear_uow() as u:
            u.iniciar()
            actor = exigir_actor(u, actor_id, coordinador=True)
            guia = u.guias.obtener(guia_id)
            exigir_acceso(actor, guia)
            if type(version) is not int or guia.version != version:
                raise ErrorNegocio(
                    "CONFLICTO_VERSION",
                    "La guía cambió en otra sesión. Actualiza la página antes de continuar.",
                    409,
                )
            viaje = u.viajes.obtener(guia.viaje_id)
            if viaje is None:
                raise ErrorNegocio("VIAJE_INVALIDO", "No se encontró el viaje asociado.", 409)
            ctx, anterior = ContextoSeguimiento(viaje, actor), guia.estado.codigo
            #La selección traduce una operación del caso de uso; no decide según el estado.
            if accion == "entregar":
                guia.entregar(ctx, receptor)
            elif accion == "despachar":
                guia.despachar(ctx)
            else:
                guia.recibir_destino(ctx)
            u.guias.actualizar_con_version(guia, version)
            if accion == "despachar":
                u.viajes.cerrar_carga(viaje.id)
            u.eventos.agregar(
                guia.id, anterior, guia.estado.codigo, accion, actor.id, self.reloj(), receptor
            )
            u.confirmar()


class ServicioViajes:
    def __init__(self, crear_uow, reloj=ahora_utc):
        self.crear_uow, self.reloj = crear_uow, reloj

    def operar(self, actor_id, viaje_id, accion):
        with self.crear_uow() as u:
            u.iniciar()
            actor = exigir_actor(u, actor_id, coordinador=True)
            v = u.viajes.obtener(viaje_id)
            if v is None:
                raise ErrorNegocio("NO_ENCONTRADO", "El viaje no existe.", 404)
            if accion == "autorizar":
                if (
                    not (v.activo and v.vehiculo_activo and v.conductor and v.ayudante)
                    or v.llegada_registrada
                ):
                    raise ErrorNegocio(
                        "VIAJE_NO_APTO",
                        "Revisa vehículo, tripulación y situación del viaje antes de autorizar.",
                    )
                if v.salida_autorizada:
                    raise ErrorNegocio("YA_AUTORIZADO", "La salida ya estaba autorizada.", 409)
                u.viajes.autorizar(v.id)
            elif accion == "llegada":
                if v.llegada_registrada:
                    raise ErrorNegocio("YA_REGISTRADA", "La llegada ya está registrada.", 409)
                if (
                    not v.activo
                    or not v.salida_autorizada
                    or not u.viajes.total_guias(v.id)
                    or u.viajes.pendientes(v.id)
                ):
                    raise ErrorNegocio(
                        "DESPACHO_PENDIENTE",
                        "Despacha todas las guías asignadas antes de registrar la llegada del viaje.",
                    )
                u.viajes.registrar_llegada(v.id)
            else:
                raise ErrorNegocio("ACCION_INVALIDA", "La operación solicitada no existe.", 400)
            u.viajes.anotar(v.id, accion, actor.id, self.reloj())
            u.confirmar()


class ServicioConsultas:
    def __init__(self, crear_uow):
        self.crear_uow = crear_uow

    def catalogos(self, actor_id):
        with self.crear_uow() as u:
            a = exigir_actor(u, actor_id)
            sucursal = None if a.rol == "coordinador" else a.sucursal_id
            viajes = [
                v
                for v in u.consultas.viajes()
                if sucursal is None or sucursal in (v["origen_id"], v["destino_id"])
            ]
            return dict(
                sucursales=u.consultas.sucursales(),
                viajes=viajes,
                ventas=u.consultas.ventas(sucursal),
            )

    def listar(self, actor_id, buscar="", estado="", pagina=1, limite=15):
        with self.crear_uow() as u:
            a = exigir_actor(u, actor_id)
            return u.consultas.listar_guias(
                None if a.rol == "coordinador" else a.sucursal_id, buscar, estado, pagina, limite
            )

    def indicadores(self, actor_id):
        with self.crear_uow() as u:
            a = exigir_actor(u, actor_id)
            return u.consultas.indicadores(None if a.rol == "coordinador" else a.sucursal_id)

    def detalle(self, actor_id, guia_id):
        with self.crear_uow() as u:
            a = exigir_actor(u, actor_id)
            guia = u.guias.obtener(guia_id)
            exigir_acceso(a, guia)
            datos = u.consultas.detalle(guia_id)
            datos["acciones"] = guia.estado.acciones if a.rol == "coordinador" else ()
            return datos
