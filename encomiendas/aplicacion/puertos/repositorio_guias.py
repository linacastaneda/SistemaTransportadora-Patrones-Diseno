"""Puerto RepositorioGuias: abstracción de la capa de datos."""
from __future__ import annotations
from abc import ABC, abstractmethod

class RepositorioGuias(ABC):
    @abstractmethod
    def obtener(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def guardar(self, solicitud, actor_id, token, huella, fecha, pasos):
        raise NotImplementedError

    @abstractmethod
    def actualizar_con_version(self, guia, version):
        raise NotImplementedError

    @abstractmethod
    def por_token(self, token):
        raise NotImplementedError
