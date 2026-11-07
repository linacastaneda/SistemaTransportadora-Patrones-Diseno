"""SqliteAsignaciones: acceso a datos; sin lógica de interfaz."""
from __future__ import annotations
from dataclasses import asdict, fields
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from encomiendas.aplicacion.contratos import (
    RepositorioGuias,
    RepositorioViajes,
    RepositorioVentas,
    RepositorioAsignaciones,
    RepositorioEventos,
    UnidadTrabajo,
)
from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.dominio.estados import cargar_estado
from encomiendas.dominio.modelos import Empleado, GuiaEnvio, Viaje, Venta


from encomiendas.persistencia.sqlite_base import conectar, inicializar, _objeto

class SqliteAsignaciones(RepositorioAsignaciones):
    def __init__(self, db):
        self.db = db

    def guardar(self, guia_id, solicitud):
        self.db.execute(
            "INSERT INTO asignaciones(guia_id,viaje_id,peso_g,volumen_cm3) VALUES(?,?,?,?)",
            (guia_id, solicitud.viaje_id, solicitud.peso_g, solicitud.volumen_cm3),
        )
