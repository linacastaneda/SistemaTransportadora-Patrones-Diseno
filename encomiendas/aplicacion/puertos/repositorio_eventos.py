"""Puerto RepositorioEventos: abstracción de la capa de datos."""
from __future__ import annotations
from abc import ABC, abstractmethod

class RepositorioEventos(ABC):
    @abstractmethod
    def agregar(self, guia_id, anterior, nuevo, accion, actor_id, fecha, receptor=None):
        raise NotImplementedError
