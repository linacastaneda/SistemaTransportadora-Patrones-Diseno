"""EnDestino: estado concreto del seguimiento de guías."""
from __future__ import annotations
import re
from .estado_envio import EstadoEnvio
from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from .entregado import Entregado

class EnDestino(EstadoEnvio):
    codigo, etiqueta, acciones = "EN_DESTINO", "En destino", ("entregar",)

    def despachar(self, guia, ctx):
        super().despachar(guia, ctx)

    def recibir_destino(self, guia, ctx):
        super().recibir_destino(guia, ctx)

    def entregar(self, guia, ctx, receptor):
        if not 3 <= len(receptor.nombre.strip()) <= 120 or not re.fullmatch(
            r"[A-Za-z0-9.\-]{3,24}", receptor.documento
        ):
            raise ErrorNegocio(
                "RECEPTOR_INVALIDO", "Indica el nombre y documento de quien recibe la encomienda."
            )
        if not 5 <= len(receptor.constancia.strip()) <= 300:
            raise ErrorNegocio(
                "CONSTANCIA_INVALIDA",
                "La constancia de entrega debe tener entre 5 y 300 caracteres.",
            )
        guia._cambiar_estado(Entregado())
