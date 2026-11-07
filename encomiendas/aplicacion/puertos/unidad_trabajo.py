"""Puerto UnidadTrabajo: abstracción de la capa de datos."""
from __future__ import annotations
from abc import ABC, abstractmethod

class UnidadTrabajo(ABC):
    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, tipo, valor, traza):
        raise NotImplementedError

    @abstractmethod
    def iniciar(self):
        raise NotImplementedError

    @abstractmethod
    def confirmar(self):
        raise NotImplementedError

    @abstractmethod
    def revertir(self):
        raise NotImplementedError
