"""ValidarCapacidad: participante del patrón Chain of Responsibility."""
from __future__ import annotations
import re
from encomiendas.dominio.modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion
from .validador_envio import ValidadorEnvio

class ValidarCapacidad(ValidadorEnvio):
    nombre = "Capacidad de carga"

    def validar(self, ctx):
        s, v = ctx.solicitud, ctx.viaje
        error = None
        if v is None:
            error = "No se puede determinar la capacidad del viaje."
        elif ctx.peso_ocupado_g + s.peso_g > v.peso_maximo_g:
            error = "El peso del paquete supera la capacidad disponible del viaje."
        elif ctx.volumen_ocupado_cm3 + s.volumen_cm3 > v.volumen_maximo_cm3:
            error = "El volumen del paquete supera la capacidad disponible del viaje."
        return self._resolver(ctx, "CAPACIDAD", error)
