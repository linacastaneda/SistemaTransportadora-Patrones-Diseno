"""SqliteEmpleados: acceso a datos; sin lógica de interfaz."""
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

class SqliteEmpleados:
    def __init__(self, db):
        self.db = db

    def obtener(self, identificador):
        return _objeto(
            Empleado,
            self.db.execute("SELECT * FROM empleados WHERE id=?", (identificador,)).fetchone(),
        )

    def por_correo(self, correo):
        return self.db.execute(
            "SELECT * FROM empleados WHERE correo=? COLLATE NOCASE", (correo,)
        ).fetchone()
