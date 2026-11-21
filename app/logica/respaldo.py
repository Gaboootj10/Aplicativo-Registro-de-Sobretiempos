"""Respaldo y restauración de la base de datos con las herramientas de MySQL.

El respaldo usa ``mysqldump --single-transaction`` (copia consistente sin
bloquear las tablas InnoDB) e incluye procedimientos, disparadores y eventos.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
from pathlib import Path

from datos.configuracion import ConfiguracionMySQL

SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class ErrorRespaldo(Exception):
    """Error al generar o restaurar un respaldo."""


def _entorno(config: ConfiguracionMySQL) -> dict:
    """Entorno con la contraseña en MYSQL_PWD para no escribirla en la línea de comandos."""
    entorno = os.environ.copy()
    entorno["MYSQL_PWD"] = config.contrasena
    return entorno


def generar_respaldo(config: ConfiguracionMySQL, carpeta: str | Path) -> Path:
    """Genera un archivo .sql con la estructura, los datos y la lógica de la base."""
    if not config.mysqldump or not Path(config.mysqldump).exists():
        raise ErrorRespaldo("No se encontró mysqldump.exe. Indique su ruta en Conexión.")
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f"{config.base_datos}_{dt.datetime.now():%Y%m%d_%H%M%S}.sql"
    comando = [config.mysqldump, "-h", config.host, "-P", str(config.puerto), "-u", config.usuario,
               "--single-transaction", "--routines", "--triggers", "--events",
               "--set-gtid-purged=OFF", "--default-character-set=utf8mb4",
               "--databases", config.base_datos, f"--result-file={archivo}"]
    proceso = subprocess.run(comando, env=_entorno(config), capture_output=True, text=True,
                             creationflags=SIN_VENTANA)
    if proceso.returncode != 0:
        archivo.unlink(missing_ok=True)
        raise ErrorRespaldo(proceso.stderr.strip() or "mysqldump terminó con error.")
    return archivo


def restaurar_respaldo(config: ConfiguracionMySQL, archivo: str | Path) -> None:
    """Restaura un archivo de respaldo con el cliente mysql."""
    if not config.mysql or not Path(config.mysql).exists():
        raise ErrorRespaldo("No se encontró mysql.exe. Indique su ruta en Conexión.")
    comando = [config.mysql, "-h", config.host, "-P", str(config.puerto), "-u", config.usuario,
               "--default-character-set=utf8mb4"]
    with open(archivo, "rb") as entrada:
        proceso = subprocess.run(comando, stdin=entrada, env=_entorno(config), capture_output=True,
                                 creationflags=SIN_VENTANA)
    if proceso.returncode != 0:
        raise ErrorRespaldo(proceso.stderr.decode("utf-8", "replace").strip() or "mysql terminó con error.")


def listar_respaldos(carpeta: str | Path) -> list[tuple[str, str, str]]:
    """Lista los respaldos (.sql) de la carpeta: nombre, fecha y tamaño."""
    carpeta = Path(carpeta)
    if not carpeta.exists():
        return []
    archivos = sorted(carpeta.glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [(a.name, dt.datetime.fromtimestamp(a.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
             f"{a.stat().st_size / 1024:.1f} KB") for a in archivos]
