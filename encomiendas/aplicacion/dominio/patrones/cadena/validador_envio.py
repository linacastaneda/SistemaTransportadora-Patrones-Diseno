"""ValidadorEnvio: participante del patrón Chain of Responsibility."""
from __future__ import annotations
from abc import ABC, abstractmethod
from encomiendas.dominio.modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion

class ValidadorEnvio(ABC):
    nombre = "Validación"

    def __init__(self):
        self._siguiente: ValidadorEnvio | None = None

    def enlazar(self, siguiente: "ValidadorEnvio") -> "ValidadorEnvio":
        #La cadena es una lista enlazada de manejadores, no una lista de funciones del controlador.
        actual = siguiente
        visitados = {id(self)}
        while actual is not None:
            if id(actual) in visitados:
                raise ValueError("La cadena no admite ciclos.")
            visitados.add(id(actual))
            actual = actual._siguiente
        self._siguiente = siguiente
        return siguiente

    @abstractmethod
    def validar(self, ctx: ContextoRegistro) -> ResultadoValidacion:
        raise NotImplementedError

    def _resolver(self, ctx, codigo, error=None):
        paso = PasoValidacion(self.nombre, error is None, error or "Conforme")
        if error:
            return ResultadoValidacion(False, codigo, error, (paso,))
        if self._siguiente is None:
            return ResultadoValidacion(True, "APROBADO", "Solicitud validada.", (paso,))
        resto = self._siguiente.validar(ctx)
        #Las tuplas conservan la traza de esta solicitud sin compartir acumuladores mutables.
        return ResultadoValidacion(
            resto.aprobado, resto.codigo, resto.mensaje, (paso,) + resto.pasos
        )
