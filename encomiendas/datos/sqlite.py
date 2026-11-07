"""Fachada de compatibilidad; cada repositorio tiene archivo propio."""
from .sqlite_base import conectar, inicializar, _objeto
from .repositorios.sqlite_guias import SqliteGuias
from .repositorios.sqlite_viajes import SqliteViajes
from .repositorios.sqlite_ventas import SqliteVentas
from .repositorios.sqlite_asignaciones import SqliteAsignaciones
from .repositorios.sqlite_eventos import SqliteEventos
from .repositorios.sqlite_empleados import SqliteEmpleados
from .repositorios.consultas_sqlite import ConsultasSqlite
from .repositorios.unidad_trabajo_sqlite import UnidadTrabajoSqlite
