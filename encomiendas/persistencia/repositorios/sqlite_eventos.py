"""SqliteEventos: acceso a datos; sin lógica de interfaz."""
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

class SqliteEventos(RepositorioEventos):
    def __init__(self, db):
        self.db = db

    def agregar(self, guia_id, anterior, nuevo, accion, actor_id, fecha, receptor=None):
        self.db.execute(
            """INSERT INTO eventos(guia_id,estado_anterior,estado_nuevo,accion,actor_id,fecha,
                          receptor_nombre,receptor_documento,constancia) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                guia_id,
                anterior,
                nuevo,
                accion,
                actor_id,
                fecha,
                receptor.nombre if receptor else "",
                receptor.documento if receptor else "",
                receptor.constancia if receptor else "",
            ),
        )
