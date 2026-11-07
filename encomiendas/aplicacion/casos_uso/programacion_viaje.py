"""ProgramacionViaje: operaciones de la primera entrega en tres capas."""
from __future__ import annotations
"""Casos de uso recuperados de la primera entrega Java.
No implementan patrones adicionales: amplían la operación de la misma aplicación Flask.
La escritura de datos se delega a un repositorio SQLite.
"""
from dataclasses import dataclass
from datetime import datetime
import re

from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.servicios import exigir_actor




@dataclass(frozen=True)
class ProgramacionViaje:
    codigo: str
    origen_id: int
    destino_id: int
    fecha_salida: str
    placa: str
    conductor: str
    ayudante: str
    peso_maximo_g: int
    volumen_maximo_cm3: int
