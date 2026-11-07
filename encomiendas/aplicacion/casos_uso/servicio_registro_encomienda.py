"""Caso de uso ServicioRegistroEncomienda, capa de negocio MVC."""
from __future__ import annotations
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


from encomiendas.aplicacion.utilidades import ahora_utc, exigir_actor, exigir_acceso
from .registro_confirmado import RegistroConfirmado

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
