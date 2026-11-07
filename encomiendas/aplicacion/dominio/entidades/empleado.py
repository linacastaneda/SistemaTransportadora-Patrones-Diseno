"""Entidad Empleado. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Empleado:
    id: int
    nombre: str
    correo: str
    rol: str
    sucursal_id: int
    activo: bool
