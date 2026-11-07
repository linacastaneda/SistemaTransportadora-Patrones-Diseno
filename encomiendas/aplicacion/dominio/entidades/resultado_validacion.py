"""Entidad ResultadoValidacion. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ResultadoValidacion:
    aprobado: bool
    codigo: str
    mensaje: str
    pasos: tuple[PasoValidacion, ...]
