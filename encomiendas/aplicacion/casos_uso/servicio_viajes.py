"""Caso de uso ServicioViajes, capa de negocio MVC."""
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
