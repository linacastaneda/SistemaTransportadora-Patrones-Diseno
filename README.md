# Sistema Integral de Transportadora — Patrones de Diseño

Aplicación académica **Python 3.11 / Flask / SQLite**, ampliación de la implementación de gestión de encomiendas desarrollada por el equipo. Conserva **Chain of Responsibility y State**, unidos en el registro y seguimiento de la **misma guía**, e integra programación de viajes y registro de pagos según los procesos trabajados en la primera entrega Java/Swing.

**Equipo:** Lina Castañeda, Juan Riaño y Gerardo Ropero · Universidad Sergio Arboleda.

## Alcance y procedencia

- **Base preservada:** [JuanjoRiano/encomiendasGestionOperativa](https://github.com/JuanjoRiano/encomiendasGestionOperativa), aplicación web Flask/SQLite (inicio de sesión, registro de encomiendas, despacho, llegada, entrega, auditoría y pruebas). No se modifica el repositorio original.
- **Primera entrega tomada como referencia:** Sistema Integral de Gestión de una empresa transportadora de pasajeros y encomiendas, implementado en **Java 17, Swing, MVC** con Factory Method, Abstract Factory, Builder, Prototype y Singleton. Los conceptos `Viaje`, `Venta`, `Pago`, `GuiaEnvio` y `AsignacionCarga` se reutilizan conceptualmente en esta ampliación Python.
- **Novedad funcional en este repositorio:** menú **Programar viajes y pagos**, que permite crear viajes y aplicar pagos a las ventas desde la misma base SQLite.
- **Patrones de comportamiento implementados:** Chain of Responsibility y State, sin alterar la regla de implementar solamente dos.
- **Patrones diseñados, no programados:** Iterator y Memento.

La aplicación Python **no es una conversión literal de todos los módulos Java**: se incorporan procesos compatibles sin sustituir las funcionalidades existentes. Los patrones creacionales de la primera entrega quedan como antecedente, no se ejecutan nuevamente aquí.

## Organización actual: MVC / tres capas

La aplicación se ordena en **Presentación (Vista y Controlador Flask)**, **Negocio (casos de uso, entidades y patrones)** y **Datos (repositorios SQLite)**. **Cada clase dispone de un archivo Python propio**; los archivos de compatibilidad solo reexportan las clases.

- **[Ver arquitectura y mapa clase → archivo](docs/ARQUITECTURA_TRES_CAPAS.md)**.
- **[Ver diagramas de clases y actividades](docs/DIAGRAMAS_UML.md)**.
- **[Ver pruebas de arquitectura](tests/test_arquitectura_mvc.py)**.

```text
encomiendas/
├── presentacion/                 # Vistas HTML y controladores Flask
│   ├── rutas.py
│   ├── operaciones_anteriores.py
│   ├── templates/
│   └── static/
├── aplicacion/                   # Capa de negocio
│   ├── casos_uso/                # Cada servicio en su archivo
│   ├── puertos/                  # Contratos de repositorios
│   └── utilidades.py
├── dominio/                      # Modelo y patrones de comportamiento
│   ├── entidades/                # GuiaEnvio, Viaje, Venta, etc.
│   └── patrones/
│       ├── cadena/               # 6 clases + fabrica.py
│       └── estado/               # 5 clases
└── persistencia/                 # Capa de datos
    ├── repositorios/             # Adaptadores individuales
    ├── sqlite_base.py
    └── esquema.sql
```

## Cómo funciona la integración de Chain y State

1. El operador selecciona una venta de encomienda y un viaje con capacidad.
2. Chain of Responsibility valida personas, paquete, trayecto, pago y capacidad; ante un error, rechaza sin guardar.
3. Con la validación aprobada, la transacción guarda `GuiaEnvio`, `AsignacionCarga` y el evento inicial `RECIBIDO`.
4. State gobierna **la misma guía**: `RECIBIDO → EN_TRANSITO → EN_DESTINO → ENTREGADO`.
5. Los estados inválidos se rechazan; el historial, la versión y las reglas de concurrencia se conservan en SQLite.

## Arquitectura de tres capas / MVC

| Capa | Archivos |
|---|---|
| Presentación / Controlador | `encomiendas/presentacion/rutas.py`, `operaciones_anteriores.py`, plantillas HTML |
| Negocio / Modelo | `encomiendas/aplicacion/servicios.py`, `operaciones_anteriores.py`, `encomiendas/aplicacion/dominio/` |
| Datos | `encomiendas/datos/sqlite.py`, `operaciones_anteriores.py`, `esquema.sql` |

## Instalar y ejecutar

Se necesita Python 3.11 o superior. En la carpeta del repositorio:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app run preparar-demo
python run.py
```

Abrir [http://127.0.0.1:5000](http://127.0.0.1:5000).

**Datos académicos de demostración:** usuario `coordinador@demo.local`, contraseña `Demo2026!`. Se pueden cargar cuentas de demostración con `preparar-demo`. No usar esos datos en producción. La contraseña se puede cambiar configurando la variable `ENCOMIENDAS_CLAVE_DEMO` antes de cargar la demo.

**Módulo adicional:** después de iniciar sesión, abrir **Programar viajes y pagos**. Un pago aceptado actualiza el saldo disponible de la misma venta usada al registrar una guía; un viaje nuevo aparece entre los viajes disponibles.

## Ejecutar pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Además, **GitHub Actions** verifica las pruebas con Python 3.11 en cada cambio.

## Documentación y entregables

- [Diagramas UML en blanco y negro — 4 de clases, 4 de actividades y 1 integrado](docs/DIAGRAMAS_UML.md).
- Código fuente documentado y pruebas en `encomiendas/` y `tests/`.
- Informe de la actividad: los resultados de ejecución deben corresponder a esta versión Flask (no usar el informe Java anterior como si describiera este código).
- Falta el video obligatorio en YouTube con cámara de los tres integrantes; añadir el enlace una vez grabado.

## Agradecimientos y conservación

Se conserva la base aportada por Juan Riaño. La ampliación incorpora la referencia de la primera entrega del equipo (Lina Castañeda, Juan Riaño y Gerardo Ropero). El repositorio original del compañero no se borró ni modificó.
