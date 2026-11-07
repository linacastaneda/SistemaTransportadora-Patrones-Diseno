"""SqliteViajes: acceso a datos; sin lógica de interfaz."""
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

class SqliteViajes(RepositorioViajes):
    def __init__(self, db):
        self.db = db

    def obtener(self, identificador):
        return _objeto(
            Viaje, self.db.execute("SELECT * FROM viajes WHERE id=?", (identificador,)).fetchone()
        )

    def consultar_carga(self, identificador):
        r = self.db.execute(
            "SELECT COALESCE(SUM(peso_g),0) peso, COALESCE(SUM(volumen_cm3),0) volumen FROM asignaciones WHERE viaje_id=?",
            (identificador,),
        ).fetchone()
        return r["peso"], r["volumen"]

    def cerrar_carga(self, identificador):
        self.db.execute("UPDATE viajes SET recibe_carga=0 WHERE id=?", (identificador,))

    def autorizar(self, identificador):
        self.db.execute("UPDATE viajes SET salida_autorizada=1 WHERE id=?", (identificador,))

    def registrar_llegada(self, identificador):
        self.db.execute(
            "UPDATE viajes SET llegada_registrada=1,recibe_carga=0 WHERE id=?", (identificador,)
        )

    def pendientes(self, identificador):
        return self.db.execute(
            "SELECT COUNT(*) FROM guias WHERE viaje_id=? AND estado='RECIBIDO'", (identificador,)
        ).fetchone()[0]

    def total_guias(self, identificador):
        return self.db.execute(
            "SELECT COUNT(*) FROM guias WHERE viaje_id=?", (identificador,)
        ).fetchone()[0]

    def anotar(self, identificador, accion, actor_id, fecha):
        self.db.execute(
            "INSERT INTO movimientos_viaje(viaje_id,accion,actor_id,fecha) VALUES(?,?,?,?)",
            (identificador, accion, actor_id, fecha),
        )
