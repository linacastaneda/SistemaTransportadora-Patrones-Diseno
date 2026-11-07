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


class SqliteAsignaciones(RepositorioAsignaciones):
    def __init__(self, db):
        self.db = db

    def guardar(self, guia_id, solicitud):
        self.db.execute(
            "INSERT INTO asignaciones(guia_id,viaje_id,peso_g,volumen_cm3) VALUES(?,?,?,?)",
            (guia_id, solicitud.viaje_id, solicitud.peso_g, solicitud.volumen_cm3),
        )


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
        from .operaciones_anteriores import RepositorioOperacionesSqlite
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
