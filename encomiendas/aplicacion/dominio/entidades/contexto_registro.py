"""Entidad ContextoRegistro. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

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
