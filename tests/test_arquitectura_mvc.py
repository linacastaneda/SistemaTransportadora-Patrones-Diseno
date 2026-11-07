"""Garantías de estructura para mantener el proyecto alineado con el UML.

Cada clase se define en un único archivo, sin duplicados en las fachadas
de compatibilidad. Esta regla evita diagramas desactualizados cuando se añaden
manejadores, estados, servicios y repositorios.
"""
import ast
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1] / "encomiendas"


def test_una_clase_por_archivo():
    for archivo in RAIZ.rglob("*.py"):
        if "__pycache__" in archivo.parts:
            continue
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        clases = [n.name for n in arbol.body if isinstance(n, (ast.ClassDef,))]
        assert len(clases) <= 1, f"{archivo.relative_to(RAIZ)} contiene múltiples clases: {clases}"


def test_clases_de_patrones_separadas():
    from encomiendas.dominio.patrones.cadena import (
        validador_envio, validar_personas, validar_paquete,
        validar_trayecto, validar_pago, validar_capacidad,
    )
    from encomiendas.dominio.patrones.estado import (
        estado_envio, recibido, en_transito, en_destino, entregado,
    )
    cadena = [validador_envio.ValidadorEnvio, validar_personas.ValidarPersonas,
              validar_paquete.ValidarPaquete, validar_trayecto.ValidarTrayecto,
              validar_pago.ValidarPago, validar_capacidad.ValidarCapacidad]
    estado = [estado_envio.EstadoEnvio, recibido.Recibido, en_transito.EnTransito,
              en_destino.EnDestino, entregado.Entregado]
    for clase in cadena + estado:
        ruta = Path(__import__(clase.__module__, fromlist=["__file__"]).__file__)
        assert ruta.name == "".join(("_" + c.lower() if c.isupper() and i else c.lower())
                                    for i, c in enumerate(clase.__name__)).lstrip("_") + ".py"


def test_fachadas_siguen_apuntando_a_las_mismas_clases():
    from encomiendas.dominio.modelos import GuiaEnvio
    from encomiendas.dominio.entidades.guia_envio import GuiaEnvio as GuiaNueva
    from encomiendas.dominio.cadena import ValidarPaquete
    from encomiendas.dominio.patrones.cadena.validar_paquete import ValidarPaquete as ValidadorNuevo
    from encomiendas.dominio.estados import Recibido
    from encomiendas.dominio.patrones.estado.recibido import Recibido as EstadoNuevo
    assert GuiaEnvio is GuiaNueva
    assert ValidarPaquete is ValidadorNuevo
    assert Recibido is EstadoNuevo
