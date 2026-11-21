"""Capa de datos: conexión con MySQL y ejecución de procedimientos almacenados.

El aplicativo nunca escribe sentencias INSERT, UPDATE o DELETE: todas las
operaciones se realizan llamando a procedimientos almacenados con ``CALL``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pymysql

from datos.configuracion import ConfiguracionMySQL


class ErrorBaseDatos(Exception):
    """Error de la base de datos con un mensaje que se puede mostrar al usuario."""


@dataclass
class Resultado:
    """Resultado de un procedimiento: nombres de columnas y filas."""

    columnas: list[str] = field(default_factory=list)
    filas: list[tuple] = field(default_factory=list)

    def como_diccionarios(self) -> list[dict]:
        """Devuelve las filas como diccionarios {columna: valor}."""
        return [dict(zip(self.columnas, fila)) for fila in self.filas]

    def primero(self) -> dict | None:
        """Devuelve la primera fila como diccionario, o None si no hay filas."""
        filas = self.como_diccionarios()
        return filas[0] if filas else None


# Errores de MySQL que se traducen a mensajes comprensibles.
_MENSAJES = {
    1045: "Usuario o contraseña de MySQL incorrectos.",
    1049: "La base de datos indicada no existe. Ejecute primero el script sobretiempos.sql.",
    2003: "No se pudo conectar con el servidor MySQL. Verifique que el servicio esté iniciado.",
    1062: "El registro ya existe (valor duplicado).",
    1451: "No se puede eliminar: el registro está siendo usado por otros datos.",
    1452: "El valor seleccionado no existe en la tabla relacionada.",
    3819: "Un dato no cumple las restricciones de la base de datos.",
}


def _traducir(error: pymysql.MySQLError) -> ErrorBaseDatos:
    """Convierte una excepción de PyMySQL en un ErrorBaseDatos legible."""
    codigo = error.args[0] if error.args else None
    detalle = error.args[1] if len(error.args) > 1 else str(error)
    if codigo == 1644:  # SIGNAL SQLSTATE '45000' de los procedimientos y disparadores
        return ErrorBaseDatos(detalle)
    mensaje = _MENSAJES.get(codigo)
    return ErrorBaseDatos(f"{mensaje}\n\nDetalle: {detalle}" if mensaje else detalle)


class BaseDatos:
    """Administra la conexión y la llamada a procedimientos almacenados."""

    def __init__(self, config: ConfiguracionMySQL):
        self.config = config
        self._conexion: pymysql.connections.Connection | None = None

    # ------------------------------------------------------------------ conexión
    def _abrir(self) -> pymysql.connections.Connection:
        """Abre una conexión nueva con los parámetros de la configuración."""
        try:
            return pymysql.connect(
                host=self.config.host,
                port=self.config.puerto,
                user=self.config.usuario,
                password=self.config.contrasena,
                database=self.config.base_datos,
                charset="utf8mb4",
                autocommit=True,
                connect_timeout=5,
            )
        except pymysql.MySQLError as error:
            raise _traducir(error) from error

    def conexion(self) -> pymysql.connections.Connection:
        """Devuelve la conexión activa, reconectando si se perdió."""
        if self._conexion is None:
            self._conexion = self._abrir()
        else:
            try:
                self._conexion.ping(reconnect=True)
            except pymysql.MySQLError:
                self._conexion = self._abrir()
        return self._conexion

    def probar(self) -> str:
        """Prueba la conexión y devuelve la versión del servidor MySQL."""
        conexion = self._abrir()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                return cursor.fetchone()[0]
        finally:
            conexion.close()

    def cerrar(self) -> None:
        """Cierra la conexión activa."""
        if self._conexion is not None:
            try:
                self._conexion.close()
            finally:
                self._conexion = None

    # ------------------------------------------------------------ procedimientos
    def llamar(self, procedimiento: str, *parametros) -> Resultado:
        """Ejecuta ``CALL procedimiento(parametros)`` y devuelve el primer resultado.

        Los textos vacíos se envían como NULL para que los filtros opcionales
        de los procedimientos funcionen como "sin filtro".
        """
        valores = tuple(None if (isinstance(p, str) and p.strip() == "") else p for p in parametros)
        try:
            with self.conexion().cursor() as cursor:
                cursor.callproc(procedimiento, valores)
                resultado = Resultado()
                if cursor.description:
                    resultado.columnas = [d[0] for d in cursor.description]
                    resultado.filas = list(cursor.fetchall())
                while cursor.nextset():  # descarta el estado final del CALL
                    pass
                return resultado
        except pymysql.MySQLError as error:
            raise _traducir(error) from error
