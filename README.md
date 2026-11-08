# Sistema de transporte y encomiendas

Aplicación web en Python, Flask y SQLite para programar viajes, registrar pagos y gestionar encomiendas. Retoma los procesos de la primera entrega en Java y los integra en una sola aplicación de tres capas. **Chain of Responsibility** valida el registro y **State** controla el seguimiento de cada guía. Iterator y Memento se mantienen como diseños.

**Equipo:** Lina Castañeda, Juan Riaño y Gerardo Ropero · Universidad Sergio Arboleda.

## Ejecutar en Linux

Necesitas Python 3.11 o posterior. En Debian, si faltan las herramientas:

```bash
sudo apt install python3 python3-venv python3-pip
```

Desde la carpeta que contiene `run.py`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app run preparar-demo
python run.py
```

## Ejecutar en Windows

Instala Python 3.11 o posterior. Abre PowerShell en la carpeta de `run.py`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app run preparar-demo
.\.venv\Scripts\python.exe run.py
```

Estos comandos usan directamente el Python del entorno virtual; no requieren activar scripts en PowerShell.

Abre **http://127.0.0.1:5000**. Detén el servidor con `Ctrl+C`.

`preparar-demo` crea la base y carga ejemplos. Ejecutarlo otra vez conserva las operaciones y las contraseñas existentes. La aplicación guarda sus datos en `instance/encomiendas.sqlite3`.

## Acceso

Contraseña inicial de las cuentas de demostración: **`Demo2026!`**.

| Perfil | Correo |
| --- | --- |
| Coordinación, acceso completo | `coordinador@demo.local` |
| Operación en Bogotá | `operador@demo.local` |
| Operación en Medellín | `medellin@demo.local` |

- **Inicio:** resumen de viajes, saldos pendientes y guías.
- **Transporte:** consulta viajes; coordinación puede programarlos, autorizar su salida y registrar su llegada.
- **Ventas y pagos:** consulta ventas y saldos; coordinación registra abonos en COP.
- **Encomiendas:** registra guías y consulta su historial. Coordinación realiza despacho, recepción y entrega.

Los formularios de viajes reciben kg y m³. Los de pagos reciben pesos colombianos, sin separadores de miles. Admiten coma o punto decimal y conservan los valores cuando hay un error.

Los datos son ficticios. No hay cobros bancarios, venta de tiquetes ni creación general de ventas.

## Volver a iniciar

Linux:

```bash
source .venv/bin/activate
python run.py
```

Windows:

```powershell
.\.venv\Scripts\python.exe run.py
```

Si el puerto está ocupado, sustituye `python run.py` por `python -m flask --app run run --port 5001` y abre http://127.0.0.1:5001. En Windows utiliza `.\.venv\Scripts\python.exe` en lugar de `python`.

## Pruebas

Con el entorno activo en Linux:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

En Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas utilizan bases temporales. La arquitectura y los diagramas están en `docs/`; el código se organiza en `encomiendas/presentacion`, `encomiendas/aplicacion` y `encomiendas/datos`.

Base del proyecto: [encomiendasGestionOperativa](https://github.com/JuanjoRiano/encomiendasGestionOperativa), ampliada por el equipo a partir de su trabajo anterior en Java.
