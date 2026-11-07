"""Puerto RepositorioVentas: abstracción de la capa de datos."""
from __future__ import annotations
from abc import ABC, abstractmethod

class RepositorioVentas(ABC):
    @abstractmethod
    def obtener(self, identificador):
        raise NotImplementedError
