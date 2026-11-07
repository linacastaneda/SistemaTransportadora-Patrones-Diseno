"""EstadoEnvio: estado concreto del seguimiento de guías."""
from __future__ import annotations
from abc import ABC, abstractmethod
from encomiendas.dominio.errores import ErrorNegocio

class EstadoEnvio(ABC):
    codigo: str
    etiqueta: str
    acciones: tuple[str, ...]

    def _rechazar(self, accion):
        raise ErrorNegocio(
            "TRANSICION_INVALIDA", f"No se puede {accion} una guía en estado {self.etiqueta}.", 409
        )

    @abstractmethod
    def despachar(self, guia, ctx):
        self._rechazar("despachar")

    @abstractmethod
    def recibir_destino(self, guia, ctx):
        self._rechazar("registrar la llegada de")

    @abstractmethod
    def entregar(self, guia, ctx, receptor):
        self._rechazar("entregar")
