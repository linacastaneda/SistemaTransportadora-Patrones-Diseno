"""Adaptación de operaciones de la primera entrega a SQLite.
Las reglas de autorización y validación viven en la capa de negocio.
"""
import sqlite3

from encomiendas.aplicacion.dominio.errores import ErrorNegocio


class RepositorioOperacionesSqlite:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def sucursales_validas(self, origen_id: int, destino_id: int) -> bool:
        if origen_id == destino_id:
            return False
        total = self.db.execute(
            "SELECT COUNT(*) FROM sucursales WHERE activa=1 AND id IN (?,?)",
            (origen_id, destino_id),
        ).fetchone()[0]
        return total == 2

    def crear_viaje(self, datos) -> int:
        try:
            cursor = self.db.execute(
                """INSERT INTO viajes (
                    codigo,origen_id,destino_id,fecha_salida,placa,peso_maximo_g,
                    volumen_maximo_cm3,activo,recibe_carga,vehiculo_activo,
                    conductor,ayudante,salida_autorizada,llegada_registrada
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    datos.codigo.strip(), datos.origen_id, datos.destino_id,
                    datos.fecha_salida, datos.placa.strip(), datos.peso_maximo_g,
                    datos.volumen_maximo_cm3, 1, 1, 1,
                    datos.conductor.strip(), datos.ayudante.strip(), 0, 0,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ErrorNegocio("VIAJE_DUPLICADO", "El viaje ya existe o tiene datos inválidos.", 409) from exc
        return cursor.lastrowid

    def crear_pago(self, datos) -> int:
        # El esquema anterior identifica los pagos por referencia única.
        # Se incorpora el medio en esa referencia, sin alterar tablas existentes.
        clave = f"{datos.medio}-{datos.referencia.strip()}"
        try:
            cursor = self.db.execute(
                "INSERT INTO pagos(referencia,venta_id,importe_centavos,valido) VALUES(?,?,?,1)",
                (clave, datos.venta_id, datos.importe_centavos),
            )
        except sqlite3.IntegrityError as exc:
            raise ErrorNegocio("PAGO_DUPLICADO", "La referencia de pago ya existe.", 409) from exc
        return cursor.lastrowid
