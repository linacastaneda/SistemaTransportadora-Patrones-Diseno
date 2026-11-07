"""Caso de uso ServicioConsultas, capa de negocio MVC."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

from werkzeug.security import check_password_hash, generate_password_hash

from encomiendas.aplicacion.dominio.cadena import crear_cadena
from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.dominio.modelos import (
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
