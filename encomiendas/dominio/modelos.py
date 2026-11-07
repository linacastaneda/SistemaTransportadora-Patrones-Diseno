from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .estados import EstadoEnvio


@dataclass(frozen=True)
class Empleado:
    id: int
    nombre: str
    correo: str
    rol: str
    sucursal_id: int
    activo: bool


@dataclass(frozen=True)
class Viaje:
    id: int
    codigo: str
    origen_id: int
    destino_id: int
    peso_maximo_g: int
    volumen_maximo_cm3: int
    activo: bool
    recibe_carga: bool
    vehiculo_activo: bool
    conductor: str
    ayudante: str
    salida_autorizada: bool
    llegada_registrada: bool


@dataclass(frozen=True)
class Venta:
    id: int
    referencia: str
    origen_id: int
    destino_id: int
    remitente_documento: str
    destinatario_documento: str
    total_centavos: int
    pagado_centavos: int
    activa: bool
    vinculada: bool


@dataclass(frozen=True)
class SolicitudRegistro:
    #Enteros en gramos y centavos evitan redondeos al comparar capacidad y valores monetarios.
    venta_id: int
    viaje_id: int
    origen_id: int
    destino_id: int
    remitente_nombre: str
    remitente_documento: str
    remitente_telefono: str
    destinatario_nombre: str
    destinatario_documento: str
    destinatario_telefono: str
    direccion_entrega: str
    descripcion: str
    peso_g: int
    largo_cm: int
    ancho_cm: int
    alto_cm: int
    valor_centavos: int
    observaciones: str = ""

    @property
    def volumen_cm3(self) -> int:
        return self.largo_cm * self.ancho_cm * self.alto_cm


@dataclass(frozen=True)
class PoliticaPaquete:
    peso_maximo_g: int = 100_000
    dimension_maxima_cm: int = 200
    valor_maximo_centavos: int = 10_000_000_000


@dataclass(frozen=True)
class ContextoRegistro:
    #Una instantánea por solicitud evita que los manejadores compartan datos entre peticiones.
    solicitud: SolicitudRegistro
    venta: Venta | None
    viaje: Viaje | None
    peso_ocupado_g: int
    volumen_ocupado_cm3: int
    sucursales_activas: frozenset[int]
    politica: PoliticaPaquete


@dataclass(frozen=True)
class PasoValidacion:
    nombre: str
    aprobado: bool
    mensaje: str


@dataclass(frozen=True)
class ResultadoValidacion:
    aprobado: bool
    codigo: str
    mensaje: str
    pasos: tuple[PasoValidacion, ...]


@dataclass(frozen=True)
class Receptor:
    nombre: str
    documento: str
    constancia: str


@dataclass(frozen=True)
class ContextoSeguimiento:
    viaje: Viaje
    empleado: Empleado


@dataclass
class GuiaEnvio:
    id: int
    numero: str
    viaje_id: int
    origen_id: int
    destino_id: int
    version: int
    estado: "EstadoEnvio"

    def despachar(self, ctx: ContextoSeguimiento) -> None:
        self.estado.despachar(self, ctx)

    def recibir_destino(self, ctx: ContextoSeguimiento) -> None:
        self.estado.recibir_destino(self, ctx)

    def entregar(self, ctx: ContextoSeguimiento, receptor: Receptor) -> None:
        self.estado.entregar(self, ctx, receptor)

    def _cambiar_estado(self, nuevo: "EstadoEnvio") -> None:
        #Solo los estados del dominio sustituyen esta referencia; la vista envía una acción.
        self.estado = nuevo
