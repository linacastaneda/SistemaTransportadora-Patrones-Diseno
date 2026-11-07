"""Caso de uso ServicioSeguimiento, capa de negocio MVC."""
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
