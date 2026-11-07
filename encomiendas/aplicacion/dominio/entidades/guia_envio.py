"""Entidad GuiaEnvio. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class GuiaEnvio:
    id: int
    numero: str
    viaje_id: int
    origen_id: int
    destino_id: int
    version: int
    estado: "EstadoEnvio"

    def despachar(self, ctx: ContextoSeguimiento) -> None:
        self.estado.despachar(self, ctx)

    def recibir_destino(self, ctx: ContextoSeguimiento) -> None:
        self.estado.recibir_destino(self, ctx)

    def entregar(self, ctx: ContextoSeguimiento, receptor: Receptor) -> None:
        self.estado.entregar(self, ctx, receptor)

    def _cambiar_estado(self, nuevo: "EstadoEnvio") -> None:
        #Solo los estados del dominio sustituyen esta referencia; la vista envía una acción.
        self.estado = nuevo
