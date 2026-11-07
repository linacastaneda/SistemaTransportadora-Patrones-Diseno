"""Entidad Venta. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

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
