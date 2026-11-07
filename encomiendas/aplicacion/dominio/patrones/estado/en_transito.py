"""EnTransito: estado concreto del seguimiento de guías."""
from __future__ import annotations
import re
from .estado_envio import EstadoEnvio
from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from .en_destino import EnDestino

class EnTransito(EstadoEnvio):
    codigo, etiqueta, acciones = "EN_TRANSITO", "En tránsito", ("recibir_destino",)

    def despachar(self, guia, ctx):
        super().despachar(guia, ctx)

    def recibir_destino(self, guia, ctx):
        if not ctx.viaje.llegada_registrada or ctx.viaje.destino_id != guia.destino_id:
            raise ErrorNegocio(
                "LLEGADA_NO_REGISTRADA",
                "Primero registra la llegada del viaje a la sucursal de destino.",
            )
        guia._cambiar_estado(EnDestino())

    def entregar(self, guia, ctx, receptor):
        super().entregar(guia, ctx, receptor)
