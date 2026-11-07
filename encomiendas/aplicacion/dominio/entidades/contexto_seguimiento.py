"""Entidad ContextoSeguimiento. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ContextoSeguimiento:
    viaje: Viaje
    empleado: Empleado
