"""ValidarPago: participante del patrón Chain of Responsibility."""
from __future__ import annotations
import re
from encomiendas.dominio.modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion
from .validador_envio import ValidadorEnvio

class ValidarPago(ValidadorEnvio):
    nombre = "Venta y pago"

    def validar(self, ctx):
        s, v = ctx.solicitud, ctx.venta
        error = None
        if v is None or not v.activa:
            error = "La venta no existe o no está activa."
        elif v.vinculada:
            error = "La venta ya está vinculada a una guía."
        elif (v.origen_id, v.destino_id, v.remitente_documento, v.destinatario_documento) != (
            s.origen_id,
            s.destino_id,
            s.remitente_documento,
            s.destinatario_documento,
        ):
            error = "Las personas o el trayecto no corresponden a la venta seleccionada."
        elif v.total_centavos <= 0 or v.pagado_centavos != v.total_centavos:
            error = "La suma de los pagos válidos debe coincidir con el total de la venta."
        return self._resolver(ctx, "PAGO", error)
