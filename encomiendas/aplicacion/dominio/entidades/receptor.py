"""Entidad Receptor. Una clase de dominio por archivo."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Receptor:
    nombre: str
    documento: str
    constancia: str
