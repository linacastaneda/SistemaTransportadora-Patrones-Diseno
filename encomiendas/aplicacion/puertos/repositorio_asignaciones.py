"""Puerto RepositorioAsignaciones: abstracción de la capa de datos."""
from __future__ import annotations
from abc import ABC, abstractmethod

class RepositorioAsignaciones(ABC):
    @abstractmethod
    def guardar(self, guia_id, solicitud):
        raise NotImplementedError
