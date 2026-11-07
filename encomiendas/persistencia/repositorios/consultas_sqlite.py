"""ConsultasSqlite: acceso a datos; sin lógica de interfaz."""
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

class ConsultasSqlite:
    def __init__(self, db):
        self.db = db

    def sucursales(self):
        return [
            dict(r)
            for r in self.db.execute("SELECT * FROM sucursales WHERE activa=1 ORDER BY nombre")
        ]

    def viajes(self):
        return [
            dict(r)
            for r in self.db.execute(
                """SELECT v.*, o.nombre origen, d.nombre destino,
          COALESCE((SELECT SUM(peso_g) FROM asignaciones a WHERE a.viaje_id=v.id),0) peso_ocupado_g,
          COALESCE((SELECT SUM(volumen_cm3) FROM asignaciones a WHERE a.viaje_id=v.id),0) volumen_ocupado_cm3,
          (SELECT COUNT(*) FROM guias g WHERE g.viaje_id=v.id AND estado='RECIBIDO') pendientes,
          (SELECT COUNT(*) FROM guias g WHERE g.viaje_id=v.id) total_guias
          FROM viajes v JOIN sucursales o ON o.id=v.origen_id JOIN sucursales d ON d.id=v.destino_id ORDER BY v.id"""
            )
        ]

    def ventas(self, sucursal=None):
        return [
            dict(r)
            for r in self.db.execute(
                """SELECT v.*, o.nombre origen,d.nombre destino,
          COALESCE((SELECT SUM(importe_centavos) FROM pagos p WHERE p.venta_id=v.id AND p.valido=1),0) pagado_centavos,
          (SELECT numero FROM guias g WHERE g.venta_id=v.id) guia_numero
          FROM ventas v JOIN sucursales o ON o.id=v.origen_id JOIN sucursales d ON d.id=v.destino_id
          WHERE (? IS NULL OR v.origen_id=?) ORDER BY v.id""",
                (sucursal, sucursal),
            )
        ]

    def listar_guias(self, sucursal=None, buscar="", estado="", pagina=1, limite=15):
        #La proyección devuelve valores de lectura; nunca expone un objeto State modificable a la vista.
        filtro = "(? IS NULL OR g.origen_id=? OR g.destino_id=?) AND (?='' OR g.estado=?) AND (?='' OR g.numero LIKE ? ESCAPE '\\' OR g.destinatario_nombre LIKE ? ESCAPE '\\')"
        literal = buscar.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        args = (
            sucursal,
            sucursal,
            sucursal,
            estado,
            estado,
            buscar,
            "%" + literal + "%",
            "%" + literal + "%",
        )
        total = self.db.execute(f"SELECT COUNT(*) FROM guias g WHERE {filtro}", args).fetchone()[0]
        filas = self.db.execute(
            f"""SELECT g.*,o.nombre origen,d.nombre destino,v.codigo viaje
          FROM guias g JOIN sucursales o ON o.id=g.origen_id JOIN sucursales d ON d.id=g.destino_id
          JOIN viajes v ON v.id=g.viaje_id WHERE {filtro} ORDER BY g.id DESC LIMIT ? OFFSET ?""",
            args + (limite, (pagina - 1) * limite),
        )
        return [dict(r) for r in filas], total

    def indicadores(self, sucursal=None):
        return {
            r["estado"]: r["cantidad"]
            for r in self.db.execute(
                """SELECT estado,COUNT(*) cantidad FROM guias
              WHERE ? IS NULL OR origen_id=? OR destino_id=? GROUP BY estado""",
                (sucursal, sucursal, sucursal),
            )
        }

    def detalle(self, identificador):
        r = self.db.execute(
            """SELECT g.*,o.nombre origen,d.nombre destino,v.codigo viaje,v.placa,
          ve.referencia venta,e.nombre creador FROM guias g
          JOIN sucursales o ON o.id=g.origen_id JOIN sucursales d ON d.id=g.destino_id
          JOIN viajes v ON v.id=g.viaje_id JOIN ventas ve ON ve.id=g.venta_id JOIN empleados e ON e.id=g.creado_por
          WHERE g.id=?""",
            (identificador,),
        ).fetchone()
        if r is None:
            return None
        datos = dict(r)
        datos["pasos"] = json.loads(datos["validaciones_json"])
        datos["eventos"] = [
            dict(x)
            for x in self.db.execute(
                """SELECT ev.*,e.nombre actor FROM eventos ev
           JOIN empleados e ON e.id=ev.actor_id WHERE guia_id=? ORDER BY ev.id""",
                (identificador,),
            )
        ]
        return datos
