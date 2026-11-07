"""ValidarTrayecto: participante del patrón Chain of Responsibility."""
from __future__ import annotations
import re
from encomiendas.aplicacion.dominio.modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion
from .validador_envio import ValidadorEnvio

class ValidarTrayecto(ValidadorEnvio):
    nombre = "Trayecto y viaje"

    def validar(self, ctx):
        s, v = ctx.solicitud, ctx.viaje
        error = None
        if s.origen_id == s.destino_id or not {s.origen_id, s.destino_id}.issubset(
            ctx.sucursales_activas
        ):
            error = "Selecciona dos sucursales activas y diferentes."
        elif v is None or not v.activo or not v.recibe_carga or v.llegada_registrada:
            error = "El viaje no está disponible para recibir encomiendas."
        elif (v.origen_id, v.destino_id) != (s.origen_id, s.destino_id):
            error = "El viaje seleccionado no corresponde al origen y destino del envío."
        return self._resolver(ctx, "TRAYECTO", error)
