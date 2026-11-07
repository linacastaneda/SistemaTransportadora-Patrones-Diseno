from abc import ABC, abstractmethod
import re

from .modelos import ContextoRegistro, PasoValidacion, ResultadoValidacion


class ValidadorEnvio(ABC):
    nombre = "Validación"

    def __init__(self):
        self._siguiente: ValidadorEnvio | None = None

    def enlazar(self, siguiente: "ValidadorEnvio") -> "ValidadorEnvio":
        #La cadena es una lista enlazada de manejadores, no una lista de funciones del controlador.
        actual = siguiente
        visitados = {id(self)}
        while actual is not None:
            if id(actual) in visitados:
                raise ValueError("La cadena no admite ciclos.")
            visitados.add(id(actual))
            actual = actual._siguiente
        self._siguiente = siguiente
        return siguiente

    @abstractmethod
    def validar(self, ctx: ContextoRegistro) -> ResultadoValidacion:
        raise NotImplementedError

    def _resolver(self, ctx, codigo, error=None):
        paso = PasoValidacion(self.nombre, error is None, error or "Conforme")
        if error:
            return ResultadoValidacion(False, codigo, error, (paso,))
        if self._siguiente is None:
            return ResultadoValidacion(True, "APROBADO", "Solicitud validada.", (paso,))
        resto = self._siguiente.validar(ctx)
        #Las tuplas conservan la traza de esta solicitud sin compartir acumuladores mutables.
        return ResultadoValidacion(
            resto.aprobado, resto.codigo, resto.mensaje, (paso,) + resto.pasos
        )


class ValidarPersonas(ValidadorEnvio):
    nombre = "Personas y contacto"

    def validar(self, ctx):
        s = ctx.solicitud
        error = None
        for etiqueta, nombre, documento, telefono in (
            ("remitente", s.remitente_nombre, s.remitente_documento, s.remitente_telefono),
            (
                "destinatario",
                s.destinatario_nombre,
                s.destinatario_documento,
                s.destinatario_telefono,
            ),
        ):
            if not 3 <= len(nombre.strip()) <= 120:
                error = f"El nombre del {etiqueta} debe tener entre 3 y 120 caracteres."
                break
            if not re.fullmatch(r"[A-Za-z0-9.\-]{3,24}", documento):
                error = f"El documento del {etiqueta} no tiene un formato válido."
                break
            if (
                not re.fullmatch(r"[+0-9 ()\-]{7,25}", telefono)
                or len(re.sub(r"\D", "", telefono)) < 7
            ):
                error = f"El teléfono del {etiqueta} no es válido."
                break
        if error is None and not 5 <= len(s.direccion_entrega.strip()) <= 180:
            error = "La dirección de entrega debe tener entre 5 y 180 caracteres."
        return self._resolver(ctx, "PERSONAS", error)


class ValidarPaquete(ValidadorEnvio):
    nombre = "Características del paquete"

    def validar(self, ctx):
        s, p = ctx.solicitud, ctx.politica
        error = None
        if not 3 <= len(s.descripcion.strip()) <= 250 or len(s.observaciones) > 500:
            error = "Indica una descripción de 3 a 250 caracteres y observaciones de hasta 500."
        elif type(s.peso_g) is not int or not 0 < s.peso_g <= p.peso_maximo_g:
            error = f"El peso debe ser mayor que cero y no superar {p.peso_maximo_g / 1000:g} kg."
        elif any(
            type(x) is not int or not 0 < x <= p.dimension_maxima_cm
            for x in (s.largo_cm, s.ancho_cm, s.alto_cm)
        ):
            error = f"Cada dimensión debe ser un entero entre 1 y {p.dimension_maxima_cm} cm."
        elif (
            type(s.valor_centavos) is not int
            or not 0 <= s.valor_centavos <= p.valor_maximo_centavos
        ):
            error = "El valor declarado está fuera del límite permitido."
        return self._resolver(ctx, "PAQUETE", error)


class ValidarTrayecto(ValidadorEnvio):
    nombre = "Trayecto y viaje"

    def validar(self, ctx):
        s, v = ctx.solicitud, ctx.viaje
        error = None
        if s.origen_id == s.destino_id or not {s.origen_id, s.destino_id}.issubset(
            ctx.sucursales_activas
        ):
            error = "Selecciona dos sucursales activas y diferentes."
        elif v is None or not v.activo or not v.recibe_carga or v.llegada_registrada:
            error = "El viaje no está disponible para recibir encomiendas."
        elif (v.origen_id, v.destino_id) != (s.origen_id, s.destino_id):
            error = "El viaje seleccionado no corresponde al origen y destino del envío."
        return self._resolver(ctx, "TRAYECTO", error)


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


class ValidarCapacidad(ValidadorEnvio):
    nombre = "Capacidad de carga"

    def validar(self, ctx):
        s, v = ctx.solicitud, ctx.viaje
        error = None
        if v is None:
            error = "No se puede determinar la capacidad del viaje."
        elif ctx.peso_ocupado_g + s.peso_g > v.peso_maximo_g:
            error = "El peso del paquete supera la capacidad disponible del viaje."
        elif ctx.volumen_ocupado_cm3 + s.volumen_cm3 > v.volumen_maximo_cm3:
            error = "El volumen del paquete supera la capacidad disponible del viaje."
        return self._resolver(ctx, "CAPACIDAD", error)


def crear_cadena() -> ValidadorEnvio:
    primero = ValidarPersonas()
    primero.enlazar(ValidarPaquete()).enlazar(ValidarTrayecto()).enlazar(ValidarPago()).enlazar(
        ValidarCapacidad()
    )
    return primero
