"""ServicioOperaciones: operaciones de la primera entrega en tres capas."""
from __future__ import annotations
"""Casos de uso recuperados de la primera entrega Java.
No implementan patrones adicionales: amplían la operación de la misma aplicación Flask.
La escritura de datos se delega a un repositorio SQLite.
"""
from dataclasses import dataclass
from datetime import datetime
import re

from encomiendas.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.servicios import exigir_actor



from .programacion_viaje import ProgramacionViaje
from .registro_pago import RegistroPago

class ServicioOperaciones:
    """Orquesta la programación de viajes y el pago asociado a una venta.

    En la primera entrega estas operaciones existían en Java/Swing; aquí se
    adaptan a Python/Flask y se comparten con el registro de encomiendas.
    """

    MEDIOS = frozenset(("EFECTIVO", "TARJETA", "TRANSFERENCIA"))

    def __init__(self, crear_uow):
        self.crear_uow = crear_uow

    def programar_viaje(self, actor_id: int, datos: ProgramacionViaje) -> int:
        if not re.fullmatch(r"[A-Za-z0-9-]{3,30}", datos.codigo.strip()):
            raise ErrorNegocio("CODIGO_INVALIDO", "El código del viaje debe tener de 3 a 30 caracteres.", 422)
        try:
            fecha = datetime.fromisoformat(datos.fecha_salida)
        except ValueError as exc:
            raise ErrorNegocio("FECHA_INVALIDA", "La fecha de salida no tiene un formato válido.", 422) from exc
        if fecha.tzinfo is not None:
            raise ErrorNegocio("FECHA_INVALIDA", "Ingresa la fecha y hora local sin zona horaria.", 422)
        if datos.origen_id == datos.destino_id:
            raise ErrorNegocio("TRAYECTO_INVALIDO", "Origen y destino deben ser diferentes.", 422)
        if not datos.placa.strip() or not datos.conductor.strip() or not datos.ayudante.strip():
            raise ErrorNegocio("TRIPULACION_INVALIDA", "Vehículo, conductor y ayudante son obligatorios.", 422)
        if datos.peso_maximo_g <= 0 or datos.volumen_maximo_cm3 <= 0:
            raise ErrorNegocio("CAPACIDAD_INVALIDA", "Las capacidades deben ser positivas.", 422)
        with self.crear_uow() as u:
            u.iniciar()
            exigir_actor(u, actor_id, coordinador=True)
            if not u.operaciones.sucursales_validas(datos.origen_id, datos.destino_id):
                raise ErrorNegocio("SUCURSAL_INVALIDA", "Selecciona sucursales activas.", 422)
            identificador = u.operaciones.crear_viaje(datos)
            u.confirmar()
            return identificador

    def registrar_pago(self, actor_id: int, datos: RegistroPago) -> int:
        if datos.medio not in self.MEDIOS:
            raise ErrorNegocio("MEDIO_INVALIDO", "Selecciona efectivo, tarjeta o transferencia.", 422)
        if datos.importe_centavos <= 0:
            raise ErrorNegocio("IMPORTE_INVALIDO", "El importe debe ser positivo.", 422)
        if not re.fullmatch(r"[A-Za-z0-9-]{4,48}", datos.referencia.strip()):
            raise ErrorNegocio("REFERENCIA_INVALIDA", "La referencia debe tener entre 4 y 48 caracteres.", 422)
        with self.crear_uow() as u:
            u.iniciar()
            exigir_actor(u, actor_id, coordinador=True)
            venta = u.ventas.obtener(datos.venta_id)
            if venta is None or not venta.activa or venta.vinculada:
                raise ErrorNegocio("VENTA_INVALIDA", "La venta no admite nuevos pagos.", 422)
            saldo = venta.total_centavos - venta.pagado_centavos
            if saldo <= 0 or datos.importe_centavos > saldo:
                raise ErrorNegocio("SALDO_INVALIDO", "El pago supera el saldo pendiente o la venta ya está pagada.", 422)
            identificador = u.operaciones.crear_pago(datos)
            u.confirmar()
            return identificador
