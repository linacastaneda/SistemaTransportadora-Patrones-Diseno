from abc import ABC, abstractmethod
import re

from .errores import ErrorNegocio


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


class Recibido(EstadoEnvio):
    codigo, etiqueta, acciones = "RECIBIDO", "Recibido", ("despachar",)

    def despachar(self, guia, ctx):
        v = ctx.viaje
        if (
            not (
                v.activo
                and v.vehiculo_activo
                and v.conductor
                and v.ayudante
                and v.salida_autorizada
            )
            or v.llegada_registrada
        ):
            raise ErrorNegocio(
                "SALIDA_NO_AUTORIZADA",
                "El viaje requiere vehículo activo, tripulación y salida autorizada; no debe haber llegado.",
            )
        guia._cambiar_estado(EnTransito())

    def recibir_destino(self, guia, ctx):
        super().recibir_destino(guia, ctx)

    def entregar(self, guia, ctx, receptor):
        super().entregar(guia, ctx, receptor)


class EnTransito(EstadoEnvio):
    codigo, etiqueta, acciones = "EN_TRANSITO", "En tránsito", ("recibir_destino",)

    def despachar(self, guia, ctx):
        super().despachar(guia, ctx)

    def recibir_destino(self, guia, ctx):
        if not ctx.viaje.llegada_registrada or ctx.viaje.destino_id != guia.destino_id:
            raise ErrorNegocio(
                "LLEGADA_NO_REGISTRADA",
                "Primero registra la llegada del viaje a la sucursal de destino.",
            )
        guia._cambiar_estado(EnDestino())

    def entregar(self, guia, ctx, receptor):
        super().entregar(guia, ctx, receptor)


class EnDestino(EstadoEnvio):
    codigo, etiqueta, acciones = "EN_DESTINO", "En destino", ("entregar",)

    def despachar(self, guia, ctx):
        super().despachar(guia, ctx)

    def recibir_destino(self, guia, ctx):
        super().recibir_destino(guia, ctx)

    def entregar(self, guia, ctx, receptor):
        if not 3 <= len(receptor.nombre.strip()) <= 120 or not re.fullmatch(
            r"[A-Za-z0-9.\-]{3,24}", receptor.documento
        ):
            raise ErrorNegocio(
                "RECEPTOR_INVALIDO", "Indica el nombre y documento de quien recibe la encomienda."
            )
        if not 5 <= len(receptor.constancia.strip()) <= 300:
            raise ErrorNegocio(
                "CONSTANCIA_INVALIDA",
                "La constancia de entrega debe tener entre 5 y 300 caracteres.",
            )
        guia._cambiar_estado(Entregado())


class Entregado(EstadoEnvio):
    codigo, etiqueta, acciones = "ENTREGADO", "Entregado", ()

    def despachar(self, guia, ctx):
        super().despachar(guia, ctx)

    def recibir_destino(self, guia, ctx):
        super().recibir_destino(guia, ctx)

    def entregar(self, guia, ctx, receptor):
        super().entregar(guia, ctx, receptor)


#El registro solo reconstruye objetos persistidos; las decisiones viven en cada estado.
TIPOS_ESTADO = {c.codigo: c for c in (Recibido, EnTransito, EnDestino, Entregado)}


def cargar_estado(codigo):
    if codigo not in TIPOS_ESTADO:
        raise ValueError(f"Estado persistido desconocido: {codigo}")
    return TIPOS_ESTADO[codigo]()
