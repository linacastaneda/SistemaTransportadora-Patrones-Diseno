"""Puerto RepositorioViajes: abstracción de la capa de datos."""
from __future__ import annotations
from abc import ABC, abstractmethod

class RepositorioViajes(ABC):
    @abstractmethod
    def obtener(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def consultar_carga(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def cerrar_carga(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def autorizar(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def registrar_llegada(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def pendientes(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def total_guias(self, identificador):
        raise NotImplementedError

    @abstractmethod
    def anotar(self, identificador, accion, actor_id, fecha):
        raise NotImplementedError
