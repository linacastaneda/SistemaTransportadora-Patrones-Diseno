"""Entidad PoliticaPaquete. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PoliticaPaquete:
    peso_maximo_g: int = 100_000
    dimension_maxima_cm: int = 200
    valor_maximo_centavos: int = 10_000_000_000
