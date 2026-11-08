from decimal import Decimal, InvalidOperation

from encomiendas.aplicacion.dominio.errores import ErrorNegocio
from encomiendas.aplicacion.dominio.modelos import SolicitudRegistro
from encomiendas.aplicacion.casos_uso.programacion_viaje import ProgramacionViaje
from encomiendas.aplicacion.casos_uso.registro_pago import RegistroPago


def entero(valor, etiqueta):
    try:
        texto = str(valor).strip()
        if len(texto) > 12 or not texto.lstrip("-").isdigit():
            raise ValueError
        return int(texto)
    except (ValueError, TypeError):
        raise ErrorNegocio(
            "FORMATO_INVALIDO", f"{etiqueta}: ingresa un número entero válido.", 400
        ) from None


def escalar(valor, factor, etiqueta):
    try:
        texto = str(valor).strip().replace(",", ".")
        if len(texto) > 24:
            raise ValueError
        numero = Decimal(texto)
        if not numero.is_finite() or abs(numero) > Decimal("1000000000"):
            raise ValueError
        exacto = numero * factor
        if exacto != exacto.to_integral_value():
            raise ValueError
        return int(exacto)
    except (ValueError, InvalidOperation):
        raise ErrorNegocio(
            "FORMATO_INVALIDO", f"{etiqueta}: revisa el número y sus decimales.", 400
        ) from None


def leer_solicitud(datos):
    def texto(campo):
        return str(datos.get(campo, "")).strip()

    return SolicitudRegistro(
        venta_id=entero(texto("venta_id"), "Venta"),
        viaje_id=entero(texto("viaje_id"), "Viaje"),
        origen_id=entero(texto("origen_id"), "Origen"),
        destino_id=entero(texto("destino_id"), "Destino"),
        remitente_nombre=texto("remitente_nombre"),
        remitente_documento=texto("remitente_documento").upper(),
        remitente_telefono=texto("remitente_telefono"),
        destinatario_nombre=texto("destinatario_nombre"),
        destinatario_documento=texto("destinatario_documento").upper(),
        destinatario_telefono=texto("destinatario_telefono"),
        direccion_entrega=texto("direccion_entrega"),
        descripcion=texto("descripcion"),
        peso_g=escalar(texto("peso_kg"), 1000, "Peso"),
        largo_cm=entero(texto("largo_cm"), "Largo"),
        ancho_cm=entero(texto("ancho_cm"), "Ancho"),
        alto_cm=entero(texto("alto_cm"), "Alto"),
        valor_centavos=escalar(texto("valor_declarado"), 100, "Valor declarado"),
        observaciones=texto("observaciones"),
    )


def leer_programacion(datos):
    #La presentación convierte las unidades; el caso de uso conserva su contrato entero.
    return ProgramacionViaje(
        codigo=datos.get("codigo", "").strip(),
        origen_id=entero(datos.get("origen_id", ""), "Origen"),
        destino_id=entero(datos.get("destino_id", ""), "Destino"),
        fecha_salida=datos.get("fecha_salida", "").strip(),
        placa=datos.get("placa", "").strip(),
        conductor=datos.get("conductor", "").strip(),
        ayudante=datos.get("ayudante", "").strip(),
        peso_maximo_g=escalar(datos.get("peso_maximo_kg", ""), 1000, "Capacidad en kg"),
        volumen_maximo_cm3=escalar(datos.get("volumen_maximo_m3", ""), 1000000, "Capacidad en m³"),
    )


def leer_pago(datos):
    return RegistroPago(
        venta_id=entero(datos.get("venta_id", ""), "Venta"),
        medio=datos.get("medio", "").strip().upper(),
        referencia=datos.get("referencia", "").strip(),
        importe_centavos=escalar(datos.get("importe_cop", ""), 100, "Importe en COP"),
    )
