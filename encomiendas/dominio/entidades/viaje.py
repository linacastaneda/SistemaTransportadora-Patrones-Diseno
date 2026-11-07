"""Entidad Viaje. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

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
