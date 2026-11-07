"""Recibido: estado concreto del seguimiento de guías."""
from __future__ import annotations
import re
from .estado_envio import EstadoEnvio
from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from .en_transito import EnTransito

class Recibido(EstadoEnvio):
    codigo, etiqueta, acciones = "RECIBIDO", "Recibido", ("despachar",)

    def despachar(self, guia, ctx):
        v = ctx.viaje
        if (
            not (
                v.activo
                and v.vehiculo_activo
                and v.conductor
                and v.ayudante
                and v.salida_autorizada
            )
            or v.llegada_registrada
        ):
            raise ErrorNegocio(
                "SALIDA_NO_AUTORIZADA",
                "El viaje requiere vehículo activo, tripulación y salida autorizada; no debe haber llegado.",
            )
        guia._cambiar_estado(EnTransito())

    def recibir_destino(self, guia, ctx):
        super().recibir_destino(guia, ctx)

    def entregar(self, guia, ctx, receptor):
        super().entregar(guia, ctx, receptor)
