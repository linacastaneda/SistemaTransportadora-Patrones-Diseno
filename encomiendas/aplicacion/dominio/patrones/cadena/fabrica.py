"""Fábrica de cadena: orden explícito de validadores."""
from .validar_personas import ValidarPersonas
from .validar_paquete import ValidarPaquete
from .validar_trayecto import ValidarTrayecto
from .validar_pago import ValidarPago
from .validar_capacidad import ValidarCapacidad
from .validador_envio import ValidadorEnvio

def crear_cadena() -> ValidadorEnvio:
    primero = ValidarPersonas()
    primero.enlazar(ValidarPaquete()).enlazar(ValidarTrayecto()).enlazar(ValidarPago()).enlazar(
        ValidarCapacidad()
    )
    return primero
