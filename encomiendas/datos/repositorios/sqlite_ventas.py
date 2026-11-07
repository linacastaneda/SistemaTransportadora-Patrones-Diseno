"""SqliteVentas: acceso a datos; sin lógica de interfaz."""
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
from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.dominio.estados import cargar_estado
from encomiendas.aplicacion.dominio.modelos import Empleado, GuiaEnvio, Viaje, Venta


from encomiendas.datos.sqlite_base import conectar, inicializar, _objeto

class SqliteVentas(RepositorioVentas):
    def __init__(self, db):
        self.db = db

    def obtener(self, identificador):
        r = self.db.execute(
            """SELECT v.*, COALESCE((SELECT SUM(importe_centavos) FROM pagos p
            WHERE p.venta_id=v.id AND p.valido=1),0) pagado_centavos,
            EXISTS(SELECT 1 FROM guias g WHERE g.venta_id=v.id) vinculada
            FROM ventas v WHERE v.id=?""",
            (identificador,),
        ).fetchone()
        return _objeto(Venta, r)
