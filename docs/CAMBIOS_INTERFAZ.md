# Actualización de la interfaz

Base: `linacastaneda/SistemaTransportadora-Patrones-Diseno`, commit `2601943`.

## Incorporado

- Identidad general de transporte y encomiendas en el acceso, la navegación y el pie de página.
- Inicio con indicadores y accesos a Transporte, Ventas y pagos y Encomiendas, limitados al ámbito del empleado.
- Formularios separados para programar viajes y registrar pagos; acceso exclusivo de coordinación.
- Capacidades en kg y m³ e importes en COP, convertidos sin redondeo a las unidades enteras del servicio.
- Conservación de los datos ante errores y explicación de la regla rechazada.
- Consulta de ventas con total, pagado, saldo y acciones según su situación; filtros de viajes y ventas.
- README de ejecución para Linux y Windows, dependencia de datos horarios y diagramas del diseño acordado.

Los casos de uso, los patrones y el esquema SQLite mantienen sus contratos. No se requiere migrar la base de datos.

## Llevarlo al repositorio

El comprimido contiene el proyecto completo, con `docs/` incluido. No contiene entorno virtual, base de datos, claves ni cachés. El repositorio remoto no se modificó.

1. Conserva una copia de tu carpeta actual antes de reemplazar archivos.
2. Copia desde el comprimido `encomiendas/`, `tests/`, `docs/`, `README.md`, `requirements.txt` y `pyproject.toml` sobre la raíz de tu proyecto. No borres `instance/` ni tu entorno virtual.
3. Con el servidor detenido, instala `requirements.txt` otra vez y reinicia con `python run.py`. Si ya tienes una base inicializada, no necesitas volver a preparar la demostración.
4. Ejecuta las pruebas, revisa los cambios y súbelos al repositorio cuando lo decidas.

Las rutas conservan `/guias`, `/viajes`, `/ventas` y `/operaciones`. Los formularios de operaciones ahora están en `/operaciones/viajes` y `/operaciones/pagos`, con GET y POST. El formulario de viajes envía `peso_maximo_kg` y `volumen_maximo_m3`; el de pagos envía `importe_cop`. Los servicios siguen recibiendo gramos, cm³ y centavos.

## Validación

- Las 75 pruebas anteriores se conservaron.
- Se añadieron 24 casos para conversiones exactas, formularios, permisos, CSRF, errores, filtros y el recorrido integrado.
- Resultado de la suite: **99 pruebas aprobadas** con Python 3.12 en Linux.
- Se comprobó la zona de Colombia usando `tzdata` sin recurrir a la base horaria del sistema. Esto no equivale a una ejecución real en Windows.
- El navegador disponible en el entorno de revisión no pudo acceder al servidor local. La validación automatizada usa el cliente HTTP de Flask; queda pendiente la comprobación visual en el navegador del equipo. No se incluyen capturas de ejecución nuevas ni se afirma que hayan sido verificadas.

## Recorrido sugerido para las capturas

Sobre una base de demostración sin utilizar:

1. Entrar como `coordinador@demo.local` y capturar Inicio.
2. En Transporte, programar un viaje Bogotá–Medellín, con código único, fecha/hora, placa, tripulación, 100 kg y 1 m³.
3. En Ventas y pagos, abrir VE-0025 y registrar su saldo de 18.000 COP con una referencia nueva. La venta pasa a estar lista para guía.
4. Registrar la encomienda de VE-0025 en el viaje creado. Una descripción, 8 kg y 40 × 30 × 20 cm permiten comprobar el registro.
5. Intentar despachar antes de autorizar la salida y comprobar el rechazo; autorizar el viaje desde Transporte y repetir el despacho.
6. Registrar la llegada, recibir la guía en destino y confirmar su entrega con los datos del receptor. Abrir el comprobante y el historial.
7. Para mostrar un rechazo de Chain por capacidad, utilizar VE-0021 y V-003 con 12 kg; corregir a 8 kg y confirmar.
8. Entrar como operador y comprobar que los botones de programación y pagos no aparecen.

Estas capturas corresponden a Chain y State. Iterator y Memento permanecen exclusivamente en el diseño. El enlace del video continúa pendiente.
