"""Lectura y escritura del archivo de configuración ``config.ini``.

El archivo se guarda en la carpeta de datos del usuario
(``%APPDATA%\\RegistroSobretiempos``) para que el aplicativo instalado en
"Archivos de programa" pueda modificarlo sin permisos de administrador.
"""
from __future__ import annotations

import configparser
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

NOMBRE_APLICACION = "RegistroSobretiempos"

RUTAS_MYSQL = [
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin",
    r"C:\Program Files\MySQL\MySQL Server 8.4\bin",
    r"C:\Program Files\MySQL\MySQL Server 9.0\bin",
    r"C:\xampp\mysql\bin",
]


def carpeta_programa() -> Path:
    """Carpeta del ejecutable (instalado) o raíz del proyecto (código fuente)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def ruta_recurso(nombre: str) -> Path:
    """Ruta de un archivo de la carpeta ``recursos`` (ícono), también en el ejecutable."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / "recursos" / nombre


def carpeta_usuario() -> Path:
    """Carpeta donde se guardan la configuración y los respaldos del usuario."""
    base = os.environ.get("APPDATA") or str(Path.home())
    carpeta = Path(base) / NOMBRE_APLICACION
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def ruta_configuracion() -> Path:
    """Ruta del config.ini en uso.

    Si existe un config.ini junto al código fuente se usa ese (modo
    desarrollo). Si no, se usa el de la carpeta del usuario, que se crea a
    partir de config.ini.example la primera vez.
    """
    local = carpeta_programa() / "config.ini"
    if local.exists() and not getattr(sys, "frozen", False):
        return local
    destino = carpeta_usuario() / "config.ini"
    if not destino.exists():
        ejemplo = carpeta_programa() / "config.ini.example"
        if ejemplo.exists():
            shutil.copyfile(ejemplo, destino)
    return destino


def detectar_herramienta(nombre: str) -> str:
    """Busca mysql.exe o mysqldump.exe en las rutas habituales de instalación."""
    encontrado = shutil.which(nombre)
    if encontrado:
        return encontrado
    for carpeta in RUTAS_MYSQL:
        candidato = Path(carpeta) / f"{nombre}.exe"
        if candidato.exists():
            return str(candidato)
    return ""


@dataclass
class ConfiguracionMySQL:
    """Parámetros de conexión y de las herramientas de MySQL."""

    host: str = "localhost"
    puerto: int = 3306
    usuario: str = "root"
    contrasena: str = ""
    base_datos: str = "sobretiempos"
    mysqldump: str = ""
    mysql: str = ""

    @classmethod
    def cargar(cls) -> "ConfiguracionMySQL":
        """Lee la configuración desde config.ini (o devuelve valores por defecto)."""
        lector = configparser.ConfigParser()
        lector.read(ruta_configuracion(), encoding="utf-8")
        m = lector["mysql"] if lector.has_section("mysql") else {}
        h = lector["herramientas"] if lector.has_section("herramientas") else {}
        return cls(
            host=m.get("host", "localhost"),
            puerto=int(m.get("port", 3306)),
            usuario=m.get("user", "root"),
            contrasena=m.get("password", ""),
            base_datos=m.get("database", "sobretiempos"),
            mysqldump=h.get("mysqldump", "") or detectar_herramienta("mysqldump"),
            mysql=h.get("mysql", "") or detectar_herramienta("mysql"),
        )

    def guardar(self) -> Path:
        """Guarda la configuración en config.ini y devuelve su ruta."""
        escritor = configparser.ConfigParser()
        escritor["mysql"] = {
            "host": self.host,
            "port": str(self.puerto),
            "user": self.usuario,
            "password": self.contrasena,
            "database": self.base_datos,
        }
        escritor["herramientas"] = {"mysqldump": self.mysqldump, "mysql": self.mysql}
        ruta = ruta_configuracion()
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("; Configuración del aplicativo Registro de Sobretiempos\n")
            escritor.write(archivo)
        return ruta
