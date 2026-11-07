"""Entregado: estado concreto del seguimiento de guías."""
from __future__ import annotations
import re
from .estado_envio import EstadoEnvio
from encomiendas.dominio.errores import ErrorNegocio

class Entregado(EstadoEnvio):
    codigo, etiqueta, acciones = "ENTREGADO", "Entregado", ()

    def despachar(self, guia, ctx):
        super().despachar(guia, ctx)

    def recibir_destino(self, guia, ctx):
        super().recibir_destino(guia, ctx)

    def entregar(self, guia, ctx, receptor):
        super().entregar(guia, ctx, receptor)
