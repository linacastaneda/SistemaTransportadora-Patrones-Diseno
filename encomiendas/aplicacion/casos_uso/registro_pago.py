"""RegistroPago: operaciones de la primera entrega en tres capas."""
from __future__ import annotations
"""Casos de uso recuperados de la primera entrega Java.
No implementan patrones adicionales: amplían la operación de la misma aplicación Flask.
La escritura de datos se delega a un repositorio SQLite.
"""
from dataclasses import dataclass
from datetime import datetime
import re

from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.servicios import exigir_actor




@dataclass(frozen=True)
class RegistroPago:
    venta_id: int
    medio: str
    referencia: str
    importe_centavos: int
