"""Caso de uso ServicioAcceso, capa de negocio MVC."""
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
