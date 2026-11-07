# Diseño UML · Patrones de comportamiento

**Sistema de transportes, pasajeros y encomiendas** — versión integrada Python 3 / Flask / SQLite.  
Diagramas monocromáticos, reproducibles y editables en Mermaid. Dos patrones se implementan en código (**Chain of Responsibility y State**); otros dos se **diseñan, pero no se programan** (**Iterator y Memento**). Los nombres de los diagramas implementados corresponden a las clases reales. Se omiten en las firmas de Python los tipos no anotados.

## 1. Arquitectura de tres capas / tres capas

```mermaid
%%{init: {"theme": "neutral"}}%%
flowchart TD
  A["Presentación / Vista y controlador HTTP<br/>rutas.py · operaciones_anteriores.py · HTML"] --> B["Negocio / Servicios<br/>ServicioRegistroEncomienda · ServicioSeguimiento<br/>ServicioViajes · ServicioOperaciones"]
  B --> C["Dominio / Modelo<br/>GuiaEnvio · Venta · Viaje<br/>ValidadorEnvio · EstadoEnvio"]
  B --> D["Contratos de repositorios / UnidadTrabajo"]
  D --> E["Datos / SQLite<br/>sqlite.py · operaciones_anteriores.py · esquema.sql"]
  C -. "Objetos sin SQL ni HTML" .-> D
```

## 2. Chain of Responsibility — diagrama de clases (IMPLEMENTADO)

Funcionalidad: **validar una encomienda vinculada a venta y viaje**, antes de emitir la guía. La cadena rechaza la primera regla incumplida. No guarda información: lo hace el servicio bajo transacción.

```mermaid
%%{init: {"theme": "neutral"}}%%
classDiagram
  class ValidadorEnvio {
    <<abstract>>
    +nombre: str
    -_siguiente: ValidadorEnvio|None
    +__init__()
    +enlazar(siguiente: ValidadorEnvio) ValidadorEnvio
    +validar(ctx: ContextoRegistro) ResultadoValidacion*
    -_resolver(ctx, codigo, error=None) ResultadoValidacion
  }
  class ValidarPersonas {
    +nombre: str
    +validar(ctx) ResultadoValidacion
  }
  class ValidarPaquete {
    +nombre: str
    +validar(ctx) ResultadoValidacion
  }
  class ValidarTrayecto {
    +nombre: str
    +validar(ctx) ResultadoValidacion
  }
  class ValidarPago {
    +nombre: str
    +validar(ctx) ResultadoValidacion
  }
  class ValidarCapacidad {
    +nombre: str
    +validar(ctx) ResultadoValidacion
  }
  class ContextoRegistro {
    +solicitud: SolicitudRegistro
    +venta: Venta|None
    +viaje: Viaje|None
    +peso_ocupado_g: int
    +volumen_ocupado_cm3: int
    +sucursales_activas: frozenset
    +politica: PoliticaPaquete
  }
  class ResultadoValidacion {
    +aprobado: bool
    +codigo: str
    +mensaje: str
    +pasos: tuple
  }
  class ServicioRegistroEncomienda {
    +crear_uow: callable
    +reloj: callable
    +politica: PoliticaPaquete
    +cadena: ValidadorEnvio
    +__init__(crear_uow, politica=None, reloj=ahora_utc)
    +registrar(actor_id, solicitud, token) RegistroConfirmado
  }
  ValidadorEnvio <|-- ValidarPersonas
  ValidadorEnvio <|-- ValidarPaquete
  ValidadorEnvio <|-- ValidarTrayecto
  ValidadorEnvio <|-- ValidarPago
  ValidadorEnvio <|-- ValidarCapacidad
  ValidadorEnvio "1" --> "0..1" ValidadorEnvio : siguiente
  ServicioRegistroEncomienda --> ValidadorEnvio
  ValidadorEnvio ..> ContextoRegistro
  ValidadorEnvio ..> ResultadoValidacion
```

### Diagrama de actividades — Chain of Responsibility

```mermaid
%%{init: {"theme": "neutral"}}%%
flowchart TD
  A([Inicio]) --> B["Recibir solicitud y token"]
  B --> C["Obtener actor, venta, viaje y capacidad<br/>con unidad de trabajo"]
  C --> D["ValidarPersonas"]
  D --> E{¿Personas válidas?}
  E -- No --> Z["Rechazar sin guardar"]
  E -- Sí --> F["ValidarPaquete"]
  F --> G{¿Paquete válido?}
  G -- No --> Z
  G -- Sí --> H["ValidarTrayecto"]
  H --> I{¿Trayecto válido?}
  I -- No --> Z
  I -- Sí --> J["ValidarPago"]
  J --> K{¿Venta totalmente pagada?}
  K -- No --> Z
  K -- Sí --> L["ValidarCapacidad"]
  L --> M{¿Hay capacidad?}
  M -- No --> Z
  M -- Sí --> N["Guardar guía, asignación y evento RECIBIDO<br/>en una transacción"]
  N --> O["Confirmar"]
  O --> P([Fin])
  Z --> P
```

## 3. Iterator — diagrama de clases (SOLO DISEÑO)

Funcionalidad proyectada: **consultar las guías de un viaje mediante un manifiesto**, con dos cursores independientes. Estas clases NO están implementadas y no forman parte de los tests.

```mermaid
%%{init: {"theme": "neutral"}}%%
classDiagram
  class ColeccionEncomiendas {
    <<interface>>
    +crear_iterador() IteradorEncomiendas
  }
  class IteradorEncomiendas {
    <<interface>>
    +hay_siguiente() bool
    +siguiente() ResumenEncomienda
    +reiniciar() None
  }
  class ManifiestoViaje {
    -viaje_id: int
    -elementos: tuple~ResumenEncomienda~
    +__init__(viaje_id: int, elementos: tuple)
    +crear_iterador() IteradorEncomiendas
    +cantidad() int
  }
  class IteradorManifiesto {
    -elementos: tuple~ResumenEncomienda~
    -posicion: int
    +__init__(elementos: tuple)
    +hay_siguiente() bool
    +siguiente() ResumenEncomienda
    +reiniciar() None
  }
  class ResumenEncomienda {
    +numero: str
    +destino: str
    +peso_g: int
    +estado: str
  }
  class ServicioManifiesto {
    +crear_uow: callable
    +__init__(crear_uow)
    +consultar(actor_id: int, viaje_id: int) ManifiestoViaje
  }
  ColeccionEncomiendas <|.. ManifiestoViaje
  IteradorEncomiendas <|.. IteradorManifiesto
  ManifiestoViaje ..> IteradorManifiesto : crea
  ManifiestoViaje "1" o-- "0..*" ResumenEncomienda
  IteradorManifiesto --> ResumenEncomienda
  ServicioManifiesto --> ColeccionEncomiendas
```

### Diagrama de actividades — Iterator

```mermaid
%%{init: {"theme": "neutral"}}%%
flowchart TD
  A([Inicio]) --> B["Verificar actor y viaje"]
  B --> C{¿Autorizado?}
  C -- No --> X["Rechazar consulta"]
  C -- Sí --> D["Consultar guías del viaje"]
  D --> E["Crear instantánea ManifiestoViaje"]
  E --> F["crear_iterador(): posición 0"]
  F --> G{¿hay_siguiente()?}
  G -- Sí --> H["siguiente(): devolver resumen<br/>y avanzar posición"]
  H --> G
  G -- No --> I["Finalizar recorrido sin modificar guías"]
  X --> J([Fin])
  I --> J
```

## 4. Memento — diagrama de clases (SOLO DISEÑO)

Funcionalidad proyectada: **deshacer modificaciones de un borrador de guía**, sin revertir ventas, pagos, seguimiento ni datos persistidos de una guía emitida. Estas clases NO se implementan.

```mermaid
%%{init: {"theme": "neutral"}}%%
classDiagram
  class RecuerdoBorrador {
    <<interface>>
    +id_borrador() str
    +fecha() str
    +etiqueta() str
  }
  class MementoGuia {
    -_borrador_id: str
    -_fecha: str
    -_etiqueta: str
    -_datos: dict
    +__init__(borrador_id, fecha, etiqueta, datos)
    +id_borrador() str
    +fecha() str
    +etiqueta() str
    -_contenido_para(originador) dict
  }
  class BorradorGuia {
    -_id: str
    -_propietario_id: int
    -_abierto: bool
    -_datos: dict
    +__init__(id, propietario_id, datos)
    +editar(cambios: dict) None
    +crear_recuerdo(etiqueta: str) RecuerdoBorrador
    +restaurar(recuerdo: RecuerdoBorrador) None
    +cerrar() None
  }
  class HistorialBorrador {
    -_recuerdos: list~RecuerdoBorrador~
    -_limite: int
    +__init__(limite: int)
    +guardar(recuerdo: RecuerdoBorrador) None
    +ultimo() RecuerdoBorrador
    +consumir_ultimo() None
    +vaciar() None
  }
  class ServicioBorrador {
    +crear_uow: callable
    +__init__(crear_uow)
    +editar(actor_id, borrador_id, cambios) None
    +deshacer(actor_id, borrador_id) None
    +confirmar(actor_id, borrador_id) str
  }
  RecuerdoBorrador <|.. MementoGuia
  BorradorGuia ..> MementoGuia : crea/restaura
  HistorialBorrador "1" o-- "0..*" RecuerdoBorrador
  ServicioBorrador --> HistorialBorrador
  ServicioBorrador --> BorradorGuia
```

### Diagrama de actividades — Memento

```mermaid
%%{init: {"theme": "neutral"}}%%
flowchart TD
  A([Inicio]) --> B["Abrir borrador propio"]
  B --> C{¿Está abierto y autorizado?}
  C -- No --> X["Rechazar sin modificar"]
  C -- Sí --> D{¿Acción?}
  D -- Editar --> E["Crear recuerdo anterior"]
  E --> F["Validar y aplicar cambios"]
  F --> G{¿Edición válida?}
  G -- Sí --> H["Guardar memento"]
  G -- No --> X
  D -- Deshacer --> I{¿Hay recuerdo del mismo borrador?}
  I -- No --> X
  I -- Sí --> J["Restaurar datos anteriores"]
  J --> K["Consumir recuerdo después del éxito"]
  D -- Confirmar --> L["Revalidar pago, datos, capacidad y registrar guía"]
  L --> M{¿Registro confirmado?}
  M -- No --> X
  M -- Sí --> N["Cerrar borrador y vaciar historial"]
  H --> O([Fin])
  K --> O
  N --> O
  X --> O
```

## 5. State — diagrama de clases (IMPLEMENTADO)

Funcionalidad: **seguir la MISMA guía admitida por Chain** mediante acciones; no existe selector libre de estados. Las transiciones autorizadas son `RECIBIDO → EN_TRANSITO → EN_DESTINO → ENTREGADO`.

```mermaid
%%{init: {"theme": "neutral"}}%%
classDiagram
  class EstadoEnvio {
    <<abstract>>
    +codigo: str
    +etiqueta: str
    +acciones: tuple
    -_rechazar(accion) None
    +despachar(guia, ctx) None*
    +recibir_destino(guia, ctx) None*
    +entregar(guia, ctx, receptor) None*
  }
  class Recibido {
    +codigo: str
    +etiqueta: str
    +acciones: tuple
    +despachar(guia, ctx) None
    +recibir_destino(guia, ctx) None
    +entregar(guia, ctx, receptor) None
  }
  class EnTransito {
    +codigo: str
    +etiqueta: str
    +acciones: tuple
    +despachar(guia, ctx) None
    +recibir_destino(guia, ctx) None
    +entregar(guia, ctx, receptor) None
  }
  class EnDestino {
    +codigo: str
    +etiqueta: str
    +acciones: tuple
    +despachar(guia, ctx) None
    +recibir_destino(guia, ctx) None
    +entregar(guia, ctx, receptor) None
  }
  class Entregado {
    +codigo: str
    +etiqueta: str
    +acciones: tuple
    +despachar(guia, ctx) None
    +recibir_destino(guia, ctx) None
    +entregar(guia, ctx, receptor) None
  }
  class GuiaEnvio {
    +id: int
    +numero: str
    +viaje_id: int
    +origen_id: int
    +destino_id: int
    +version: int
    +estado: EstadoEnvio
    +despachar(ctx) None
    +recibir_destino(ctx) None
    +entregar(ctx, receptor) None
    -_cambiar_estado(nuevo: EstadoEnvio) None
  }
  class ContextoSeguimiento {
    +viaje: Viaje
    +empleado: Empleado
  }
  class Receptor {
    +nombre: str
    +documento: str
    +constancia: str
  }
  class ServicioSeguimiento {
    +crear_uow: callable
    +reloj: callable
    +__init__(crear_uow, reloj=ahora_utc)
    +despachar(actor_id, guia_id, version) None
    +recibir_destino(actor_id, guia_id, version) None
    +entregar(actor_id, guia_id, version, receptor) None
    -_operar(actor_id, guia_id, version, accion, receptor=None) None
  }
  EstadoEnvio <|-- Recibido
  EstadoEnvio <|-- EnTransito
  EstadoEnvio <|-- EnDestino
  EstadoEnvio <|-- Entregado
  GuiaEnvio "1" --> "1" EstadoEnvio : estado vigente
  ServicioSeguimiento --> GuiaEnvio
  GuiaEnvio ..> ContextoSeguimiento
  GuiaEnvio ..> Receptor
```

### Diagrama de actividades — State

```mermaid
%%{init: {"theme": "neutral"}}%%
flowchart TD
  A([Inicio]) --> B["Consultar guía, actor, viaje y versión"]
  B --> C{¿Actor autorizado y versión vigente?}
  C -- No --> X["Rechazar sin persistir"]
  C -- Sí --> D{Estado actual}
  D -- RECIBIDO --> E{¿Despachar y viaje apto?}
  E -- Sí --> F["Cambiar a EN_TRANSITO"]
  E -- No --> X
  D -- EN_TRANSITO --> G{¿Llegada registrada y destino coincide?}
  G -- Sí --> H["Cambiar a EN_DESTINO"]
  G -- No --> X
  D -- EN_DESTINO --> I{¿Entrega con receptor y constancia?}
  I -- Sí --> J["Cambiar a ENTREGADO"]
  I -- No --> X
  D -- ENTREGADO --> X
  F --> K["Guardar estado y evento de auditoría<br/>en una transacción"]
  H --> K
  J --> K
  K --> L["Confirmar"]
  L --> M([Fin])
  X --> M
```

## 6. Diagrama de clases INTEGRADO — Chain + State en la misma aplicación

Ambos patrones comparten **`GuiaEnvio`**, `Venta`, `Viaje`, `UnidadTrabajoSqlite` y las vistas Flask; no se implementan como programas separados.

```mermaid
%%{init: {"theme": "neutral"}}%%
classDiagram
 direction LR
 class rutas_web {
  <<presentacion>>
  +nueva()
  +detalle(guia_id)
  +transicion(guia_id, accion)
  +viajes()
  +ventas()
 }
 class ServicioRegistroEncomienda {
  <<negocio>>
  +crear_uow
  +cadena: ValidadorEnvio
  +registrar(actor_id, solicitud, token) RegistroConfirmado
 }
 class ServicioSeguimiento {
  <<negocio>>
  +crear_uow
  +despachar(actor_id, guia_id, version)
  +recibir_destino(actor_id, guia_id, version)
  +entregar(actor_id, guia_id, version, receptor)
  -_operar(actor_id, guia_id, version, accion, receptor)
 }
 class ValidadorEnvio {
  <<Chain>>
  -_siguiente: ValidadorEnvio
  +enlazar(siguiente)
  +validar(ctx) ResultadoValidacion
 }
 class ValidarPersonas
 class ValidarPaquete
 class ValidarTrayecto
 class ValidarPago
 class ValidarCapacidad
 class GuiaEnvio {
  <<dominio>>
  +id: int
  +numero: str
  +viaje_id: int
  +version: int
  +estado: EstadoEnvio
  +despachar(ctx)
  +recibir_destino(ctx)
  +entregar(ctx, receptor)
  -_cambiar_estado(nuevo)
 }
 class EstadoEnvio {
  <<State>>
  +codigo: str
  +etiqueta: str
  +acciones: tuple
  +despachar(guia, ctx)
  +recibir_destino(guia, ctx)
  +entregar(guia, ctx, receptor)
 }
 class Recibido
 class EnTransito
 class EnDestino
 class Entregado
 class UnidadTrabajoSqlite {
  <<datos>>
  +guias
  +ventas
  +viajes
  +asignaciones
  +eventos
  +iniciar()
  +confirmar()
  +revertir()
 }
 class SqliteGuias {
  +obtener(id) GuiaEnvio
  +guardar(solicitud, actor_id, token, huella, fecha, pasos)
  +actualizar_con_version(guia, version)
 }
 class SqliteVentas {
  +obtener(id) Venta
 }
 class SqliteViajes {
  +obtener(id) Viaje
  +consultar_carga(id)
 }
 class SqliteEventos {
  +agregar(guia_id, anterior, nuevo, accion, actor_id, fecha, receptor)
 }
 rutas_web --> ServicioRegistroEncomienda
 rutas_web --> ServicioSeguimiento
 ServicioRegistroEncomienda --> ValidadorEnvio
 ValidarPersonas --|> ValidadorEnvio
 ValidarPaquete --|> ValidadorEnvio
 ValidarTrayecto --|> ValidadorEnvio
 ValidarPago --|> ValidadorEnvio
 ValidarCapacidad --|> ValidadorEnvio
 ServicioRegistroEncomienda --> UnidadTrabajoSqlite
 ServicioSeguimiento --> UnidadTrabajoSqlite
 UnidadTrabajoSqlite --> SqliteGuias
 UnidadTrabajoSqlite --> SqliteVentas
 UnidadTrabajoSqlite --> SqliteViajes
 UnidadTrabajoSqlite --> SqliteEventos
 ServicioRegistroEncomienda ..> GuiaEnvio : crea tras aprobar
 ServicioSeguimiento --> GuiaEnvio : opera la misma guía
 GuiaEnvio --> EstadoEnvio
 Recibido --|> EstadoEnvio
 EnTransito --|> EstadoEnvio
 EnDestino --|> EstadoEnvio
 Entregado --|> EstadoEnvio
```

## 7. Observaciones de consistencia

- **Solo dos patrones implementados:** `encomiendas/aplicacion/dominio/cadena.py` y `encomiendas/aplicacion/dominio/estados.py`.
- **Iterator y Memento no están en el código ejecutable:** son diseños propuestos coherentes con las mismas entidades y repositorios.
- **Coexistencia:** la cadena crea la guía en RECIBIDO; State continúa el ciclo de la misma guía, identificada con `id` y `numero`.
- **Capas:** plantilla y controlador HTTP no realizan SQL; los servicios negocian la transacción; repositorios SQLite la almacenan.
- **Primera entrega Java:** se recuperan programación de viajes y registro de pagos mediante `operaciones_anteriores.py`, compartiendo `viajes`, `ventas` y `pagos`. Los patrones creacionales antiguos no se vuelven a implementar en Python, porque el alcance de esta entrega permite implementar solo dos patrones de comportamiento.
- **Evidencia:** grabar pruebas reales de registro rechazado, registro aprobado, transición inválida, despacho, llegada y entrega; las capturas del video deben ser de la aplicación corriendo, no imágenes simuladas.
