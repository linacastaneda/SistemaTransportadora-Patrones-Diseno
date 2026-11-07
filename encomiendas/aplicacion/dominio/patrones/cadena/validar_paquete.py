"""ValidarPaquete: participante del patrón Chain of Responsibility."""
from __future__ import annotations
import re
from encomiendas.dominio.modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion
from .validador_envio import ValidadorEnvio

class ValidarPaquete(ValidadorEnvio):
    nombre = "Características del paquete"

    def validar(self, ctx):
        s, p = ctx.solicitud, ctx.politica
        error = None
        if not 3 <= len(s.descripcion.strip()) <= 250 or len(s.observaciones) > 500:
            error = "Indica una descripción de 3 a 250 caracteres y observaciones de hasta 500."
        elif type(s.peso_g) is not int or not 0 < s.peso_g <= p.peso_maximo_g:
            error = f"El peso debe ser mayor que cero y no superar {p.peso_maximo_g / 1000:g} kg."
        elif any(
            type(x) is not int or not 0 < x <= p.dimension_maxima_cm
            for x in (s.largo_cm, s.ancho_cm, s.alto_cm)
        ):
            error = f"Cada dimensión debe ser un entero entre 1 y {p.dimension_maxima_cm} cm."
        elif (
            type(s.valor_centavos) is not int
            or not 0 <= s.valor_centavos <= p.valor_maximo_centavos
        ):
            error = "El valor declarado está fuera del límite permitido."
        return self._resolver(ctx, "PAQUETE", error)
