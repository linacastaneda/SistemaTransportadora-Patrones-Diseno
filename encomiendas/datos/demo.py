from datetime import datetime, timedelta, timezone
import hashlib
import json
from dataclasses import asdict

from werkzeug.security import generate_password_hash

from encomiendas.aplicacion.dominio.cadena import crear_cadena
from encomiendas.aplicacion.dominio.modelos import (
    ContextoRegistro,
    ContextoSeguimiento,
    PoliticaPaquete,
    Receptor,
    SolicitudRegistro,
)


def sembrar_demo(crear_uow, clave="Demo2026!"):
    with crear_uow() as u:
        u.iniciar()
        db = u.db
        db.executemany(
            "INSERT OR IGNORE INTO sucursales VALUES(?,?,1)",
            [(1, "Bogotá"), (2, "Medellín"), (3, "Cali"), (4, "Bucaramanga")],
        )
        for identidad, nombre, correo, rol, sucursal in (
            (1, "Laura Méndez", "operador@demo.local", "operador", 1),
            (2, "Andrés Torres", "coordinador@demo.local", "coordinador", 1),
            (3, "Camila Ríos", "medellin@demo.local", "operador", 2),
        ):
            if not db.execute("SELECT 1 FROM empleados WHERE id=?", (identidad,)).fetchone():
                db.execute(
                    "INSERT INTO empleados VALUES(?,?,?,?,?,?,1)",
                    (identidad, nombre, correo, generate_password_hash(clave), rol, sucursal),
                )
        fecha = (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat()
        for identidad, origen, destino, peso, volumen, autorizado in (
            (1, 1, 2, 120000, 1500000, 1),
            (2, 1, 3, 100000, 1200000, 0),
            (3, 1, 4, 10000, 200000, 1),
            (4, 1, 2, 120000, 1500000, 1),
            (5, 1, 3, 100000, 1200000, 1),
            (6, 1, 2, 120000, 1500000, 1),
            (7, 2, 1, 100000, 1200000, 1),
        ):
            fecha_viaje = (
                (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
                if identidad in (4, 5, 6)
                else fecha
            )
            db.execute(
                "INSERT OR IGNORE INTO viajes VALUES(?,?,?,?,?,?,?,?,1,1,1,?,?,?,0)",
                (
                    identidad,
                    f"V-{identidad:03}",
                    origen,
                    destino,
                    fecha_viaje,
                    f"TST{100+identidad}",
                    peso,
                    volumen,
                    "Conductor de demostración",
                    "Auxiliar de demostración",
                    autorizado,
                ),
            )
        nombres = ["Papelería Central", "Comercial Andina", "Editorial Norte", "Taller del Parque"]
        for i in range(1, 33):
            origen = 2 if i == 32 else 1
            destino = 1 if i == 32 else 3 if 13 <= i <= 20 or i == 30 else 4 if 21 <= i <= 24 else 2
            total = (18000 + (i % 5) * 3500) * 100
            db.execute(
                "INSERT OR IGNORE INTO ventas VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)",
                (
                    i,
                    f"VE-{i:04}",
                    origen,
                    destino,
                    nombres[(i - 1) % 4],
                    f"900000{i:03}",
                    "3001234567",
                    f"Cliente de prueba {i:02}",
                    f"100000{i:03}",
                    "3109876543",
                    f"Calle {20+i} número 10-25",
                    total,
                ),
            )
            if i != 25:
                importe = total // 2 if i == 26 else total
                db.execute(
                    "INSERT OR IGNORE INTO pagos VALUES(?,?,?,?,1)", (i, f"PD-{i:04}", i, importe)
                )
        #Los datos iniciales pasan por los mismos validadores y estados que las operaciones reales.
        for venta_id, viaje_id, avance in [(28, 1, 0), (29, 4, 1), (30, 5, 2), (31, 6, 3)]:
            if db.execute("SELECT 1 FROM guias WHERE venta_id=?", (venta_id,)).fetchone():
                continue
            venta = db.execute("SELECT * FROM ventas WHERE id=?", (venta_id,)).fetchone()
            solicitud = SolicitudRegistro(
                venta_id,
                viaje_id,
                venta["origen_id"],
                venta["destino_id"],
                venta["remitente_nombre"],
                venta["remitente_documento"],
                venta["remitente_telefono"],
                venta["destinatario_nombre"],
                venta["destinatario_documento"],
                venta["destinatario_telefono"],
                venta["direccion_entrega"],
                "Material comercial de demostración",
                8000,
                40,
                30,
                20,
                15000000,
                "Registro inicial de demostración.",
            )
            peso, volumen = u.viajes.consultar_carga(viaje_id)
            resultado = crear_cadena().validar(
                ContextoRegistro(
                    solicitud,
                    u.ventas.obtener(venta_id),
                    u.viajes.obtener(viaje_id),
                    peso,
                    volumen,
                    frozenset((1, 2, 3, 4)),
                    PoliticaPaquete(),
                )
            )
            if not resultado.aprobado:
                raise RuntimeError(resultado.mensaje)
            instante = datetime.now(timezone.utc) - timedelta(days=2)
            huella = hashlib.sha256(
                json.dumps(asdict(solicitud), sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            guia = u.guias.guardar(
                solicitud, 2, f"{venta_id:032x}", huella, instante.isoformat(), resultado.pasos
            )
            u.asignaciones.guardar(guia.id, solicitud)
            u.eventos.agregar(guia.id, None, "RECIBIDO", "registrar", 2, instante.isoformat())
            for paso in range(avance):
                anterior = guia.estado.codigo
                receptor = None
                if paso == 1:
                    u.viajes.registrar_llegada(viaje_id)
                ctx = ContextoSeguimiento(u.viajes.obtener(viaje_id), u.empleados.obtener(2))
                if paso == 0:
                    accion = "despachar"
                    guia.despachar(ctx)
                    u.viajes.cerrar_carga(viaje_id)
                elif paso == 1:
                    accion = "recibir_destino"
                    guia.recibir_destino(ctx)
                else:
                    accion = "entregar"
                    receptor = Receptor(
                        venta["destinatario_nombre"],
                        venta["destinatario_documento"],
                        "Entrega de demostración recibida a conformidad.",
                    )
                    guia.entregar(ctx, receptor)
                u.guias.actualizar_con_version(guia, guia.version)
                guia.version += 1
                u.eventos.agregar(
                    guia.id,
                    anterior,
                    guia.estado.codigo,
                    accion,
                    2,
                    (instante + timedelta(hours=(paso + 1) * 6)).isoformat(),
                    receptor,
                )
        u.confirmar()
