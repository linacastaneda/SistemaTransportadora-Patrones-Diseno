"""Entidad PasoValidacion. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PasoValidacion:
    nombre: str
    aprobado: bool
    mensaje: str
