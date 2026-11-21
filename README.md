# Registro de Sobretiempos – Industrias San Miguel del Sur S.A.C. (Kola Real)

Aplicativo de escritorio para la funcionalidad **Registro de sobretiempos**: registra las asistencias del
personal, calcula automáticamente las horas extra (H25, H35 y H100), las consolida por periodo para su carga
en SAP (transacción PA70) y genera 14 reportes.

Proyecto del curso **Gestión de Datos e Información** – Escuela Profesional de Ingeniería de Sistemas, UCSM.

## Características

- Python 3.10 + Tkinter, **sin frameworks**.
- Todas las inserciones, modificaciones y eliminaciones se hacen con **procedimientos almacenados**; los
  **disparadores** validan, normalizan, protegen el historial y calculan el sobretiempo.
- 14 reportes (11 con JOIN) exportables a Excel.
- Importación del *Reporte de Asistencia Detallado* de Humana (.xlsx).
- Consolidación para SAP con conciliación e historial de cambios.
- Respaldo y restauración con `mysqldump` / `mysql`.

## Estructura

```
base_datos/sobretiempos.sql   Script único: tablas, vistas, 53 procedimientos, 17 disparadores y datos de prueba
app/main.py                   Punto de entrada
app/datos/                    Capa de datos: conexión y llamada a procedimientos (CALL)
app/logica/                   Capa lógica: validaciones, importación, exportación, respaldos, reportes
app/interfaz/                 Capa de presentación: ventanas Tkinter
app/recursos/                 Ícono del aplicativo
instalador/                   Script de compilación (PyInstaller) e instalador (Inno Setup)
documentacion/                Memoria descriptiva, manual de usuario y capturas
config.ini.example            Plantilla de configuración de la conexión
```

## Instalación (usuario)

1. Ejecutar `base_datos/sobretiempos.sql` en MySQL 8.0 (por ejemplo, desde MySQL Workbench).
2. Ejecutar el instalador `Instalador_RegistroSobretiempos_1.1.0.exe` (publicado en *Releases*).
3. Al abrir el aplicativo por primera vez, configurar la conexión (servidor, usuario y contraseña de MySQL).

## Ejecución desde el código fuente

```powershell
pip install -r requirements.txt
copy config.ini.example config.ini   # y escribir la contraseña de MySQL
python app\main.py
```

## Generar el ejecutable y el instalador

```powershell
pip install pyinstaller
powershell -ExecutionPolicy Bypass -File instalador\construir.ps1
```

El ejecutable queda en `dist\RegistroSobretiempos\` y el instalador en `instalador\salida\`
(requiere Inno Setup 6).

## Normas de desarrollo

- PEP 8 (estilo) y PEP 257 (docstrings) en todo el código Python.
- Base de datos: nombres en minúsculas; prefijos `sp_` (procedimientos), `trg_` (disparadores) y `v_` (vistas).

## Integrantes

- Correa Abanto Dulce María
- Huamani Murillo Fiorella Rubi
- Marquez Delgado Mauriceu Marshello
- Tapia Jara Gabriel Omar
