"""Entidad SolicitudRegistro. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

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
