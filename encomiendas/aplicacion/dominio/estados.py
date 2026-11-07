"""Fachada de compatibilidad: cada estado tiene su propio archivo."""
from .patrones.estado.estado_envio import EstadoEnvio
from .patrones.estado.recibido import Recibido
from .patrones.estado.en_transito import EnTransito
from .patrones.estado.en_destino import EnDestino
from .patrones.estado.entregado import Entregado
#El registro solo reconstruye objetos persistidos; las decisiones viven en cada estado.
TIPOS_ESTADO = {c.codigo: c for c in (Recibido, EnTransito, EnDestino, Entregado)}


def cargar_estado(codigo):
    if codigo not in TIPOS_ESTADO:
        raise ValueError(f"Estado persistido desconocido: {codigo}")
    return TIPOS_ESTADO[codigo]()
