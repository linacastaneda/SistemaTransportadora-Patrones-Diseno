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


def conectar(ruta, timeout=5):
    conexion = sqlite3.connect(str(ruta), timeout=timeout, isolation_level=None)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys=ON")
    return conexion


def inicializar(ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with closing(conectar(ruta)) as db:
        db.executescript(Path(__file__).with_name("esquema.sql").read_text(encoding="utf-8"))
        db.execute("PRAGMA user_version=1")


def _objeto(tipo, fila):
    return None if fila is None else tipo(**{f.name: fila[f.name] for f in fields(tipo)})


