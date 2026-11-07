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


class RepositorioVentas(ABC):
    @abstractmethod
    def obtener(self, identificador):
        raise NotImplementedError


class RepositorioAsignaciones(ABC):
    @abstractmethod
    def guardar(self, guia_id, solicitud):
        raise NotImplementedError


class RepositorioEventos(ABC):
    @abstractmethod
    def agregar(self, guia_id, anterior, nuevo, accion, actor_id, fecha, receptor=None):
        raise NotImplementedError


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
