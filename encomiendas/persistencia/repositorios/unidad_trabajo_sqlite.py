"""UnidadTrabajoSqlite: acceso a datos; sin lógica de interfaz."""
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
from .sqlite_guias import SqliteGuias
from .sqlite_viajes import SqliteViajes
from .sqlite_ventas import SqliteVentas
from .sqlite_asignaciones import SqliteAsignaciones
from .sqlite_eventos import SqliteEventos
from .sqlite_empleados import SqliteEmpleados
from .consultas_sqlite import ConsultasSqlite

class UnidadTrabajoSqlite(UnidadTrabajo):
    def __init__(self, ruta, timeout=5):
        self.ruta, self.timeout = ruta, timeout

    def __enter__(self):
        self.db = conectar(self.ruta, self.timeout)
        self.guias = SqliteGuias(self.db)
        self.viajes = SqliteViajes(self.db)
        self.ventas = SqliteVentas(self.db)
        self.asignaciones = SqliteAsignaciones(self.db)
        self.eventos = SqliteEventos(self.db)
        self.empleados = SqliteEmpleados(self.db)
        self.consultas = ConsultasSqlite(self.db)
        from encomiendas.persistencia.operaciones_anteriores import RepositorioOperacionesSqlite
        self.operaciones = RepositorioOperacionesSqlite(self.db)
        return self

    def iniciar(self):
        #El bloqueo se toma antes de leer capacidad; dos escritores no pueden aprobar el mismo cupo.
        self.db.execute("BEGIN IMMEDIATE")

    def confirmar(self):
        self.db.commit()

    def revertir(self):
        self.db.rollback()

    def __exit__(self, tipo, valor, traza):
        try:
            if self.db.in_transaction:
                self.revertir()
        finally:
            self.db.close()
        if isinstance(valor, sqlite3.OperationalError) and "locked" in str(valor).lower():
            raise ErrorNegocio(
                "BASE_OCUPADA",
                "Hay otra operación en curso. Espera un momento y vuelve a intentar.",
                503,
            ) from valor
        return False
