"""Fachada histórica para mantener API de Flask y pruebas anteriores."""
from .utilidades import ahora_utc, exigir_actor, exigir_acceso
from .casos_uso.servicio_acceso import ServicioAcceso
from .casos_uso.registro_confirmado import RegistroConfirmado
from .casos_uso.servicio_registro_encomienda import ServicioRegistroEncomienda
from .casos_uso.servicio_seguimiento import ServicioSeguimiento
from .casos_uso.servicio_viajes import ServicioViajes
from .casos_uso.servicio_consultas import ServicioConsultas
