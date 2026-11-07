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


