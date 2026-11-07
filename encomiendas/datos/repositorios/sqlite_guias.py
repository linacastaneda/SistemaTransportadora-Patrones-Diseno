"""SqliteGuias: acceso a datos; sin lógica de interfaz."""
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

class SqliteGuias(RepositorioGuias):
    def __init__(self, db):
        self.db = db

    def obtener(self, identificador):
        r = self.db.execute("SELECT * FROM guias WHERE id=?", (identificador,)).fetchone()
        if r is None:
            return None
        return GuiaEnvio(
            r["id"],
            r["numero"],
            r["viaje_id"],
            r["origen_id"],
            r["destino_id"],
            r["version"],
            cargar_estado(r["estado"]),
        )

    def por_token(self, token):
        return self.db.execute("SELECT * FROM guias WHERE token_registro=?", (token,)).fetchone()

    def guardar(self, solicitud, actor_id, token, huella, fecha, pasos):
        datos = asdict(solicitud)
        datos.update(
            estado="RECIBIDO",
            creado_por=actor_id,
            creado_en=fecha,
            token_registro=token,
            huella=huella,
            validaciones_json=json.dumps([asdict(p) for p in pasos], ensure_ascii=False),
        )
        #Las columnas provienen de dataclasses internas; los valores siempre se parametrizan.
        columnas = ",".join(datos)
        marcas = ",".join("?" for _ in datos)
        cursor = self.db.execute(
            f"INSERT INTO guias ({columnas}) VALUES ({marcas})", tuple(datos.values())
        )
        identificador = cursor.lastrowid
        numero = f"GE-{identificador:07d}"
        self.db.execute("UPDATE guias SET numero=? WHERE id=?", (numero, identificador))
        return self.obtener(identificador)

    def actualizar_con_version(self, guia, version):
        cursor = self.db.execute(
            "UPDATE guias SET estado=?,version=version+1 WHERE id=? AND version=?",
            (guia.estado.codigo, guia.id, version),
        )
        if cursor.rowcount != 1:
            raise ErrorNegocio(
                "CONFLICTO_VERSION",
                "La guía cambió en otra sesión. Actualiza la página antes de continuar.",
                409,
            )
