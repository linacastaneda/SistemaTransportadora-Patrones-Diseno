"""ValidarPersonas: participante del patrón Chain of Responsibility."""
from __future__ import annotations
import re
from encomiendas.aplicacion.dominio.modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion
from .validador_envio import ValidadorEnvio

class ValidarPersonas(ValidadorEnvio):
    nombre = "Personas y contacto"

    def validar(self, ctx):
        s = ctx.solicitud
        error = None
        for etiqueta, nombre, documento, telefono in (
            ("remitente", s.remitente_nombre, s.remitente_documento, s.remitente_telefono),
            (
                "destinatario",
                s.destinatario_nombre,
                s.destinatario_documento,
                s.destinatario_telefono,
            ),
        ):
            if not 3 <= len(nombre.strip()) <= 120:
                error = f"El nombre del {etiqueta} debe tener entre 3 y 120 caracteres."
                break
            if not re.fullmatch(r"[A-Za-z0-9.\-]{3,24}", documento):
                error = f"El documento del {etiqueta} no tiene un formato válido."
                break
            if (
                not re.fullmatch(r"[+0-9 ()\-]{7,25}", telefono)
                or len(re.sub(r"\D", "", telefono)) < 7
            ):
                error = f"El teléfono del {etiqueta} no es válido."
                break
        if error is None and not 5 <= len(s.direccion_entrega.strip()) <= 180:
            error = "La dirección de entrega debe tener entre 5 y 180 caracteres."
        return self._resolver(ctx, "PERSONAS", error)
