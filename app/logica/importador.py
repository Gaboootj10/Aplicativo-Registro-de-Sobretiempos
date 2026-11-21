"""Lectura del "Reporte de Asistencia Detallado" exportado desde Humana.

Se buscan las columnas Codigo, Fecha, Turno, Marca Ingreso y Marca Salida.
El turno se obtiene del texto (por ejemplo "A10 7:00 a 3:00 pm" -> A10,
"Descanso obligatorio" -> DES, "Feriado" -> FER).
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import openpyxl

from logica import validaciones as v


@dataclass
class FilaImportada:
    """Una fila del Excel ya interpretada."""

    fila_excel: int
    codigo: str
    fecha: dt.date | None
    turno: str
    entrada: dt.time | None
    salida: dt.time | None
    observacion: str = ""

    @property
    def valida(self) -> bool:
        """True si la fila se puede enviar a la base de datos."""
        return not self.observacion


def _normalizar(texto) -> str:
    """Quita tildes, espacios y puntos y pasa a minúsculas (para comparar encabezados)."""
    cadena = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[\s\.]", "", cadena).lower()


COLUMNAS = {
    "codigo": ("codigo",),
    "fecha": ("fecha",),
    "turno": ("turno",),
    "entrada": ("marcaingreso", "marcaentrada", "ingreso", "entrada"),
    "salida": ("marcasalida", "salida"),
}


def interpretar_turno(texto: str, turnos_validos: set[str]) -> str:
    """Obtiene el código de turno a partir del texto del reporte."""
    cadena = v.texto(texto)
    normal = _normalizar(cadena)
    if normal.startswith("descanso"):
        return "DES"
    if normal.startswith("feriado"):
        return "FER"
    codigo = cadena.split(" ")[0].upper() if cadena else ""
    return codigo if codigo in turnos_validos or not turnos_validos else codigo


def leer_excel(ruta: str | Path, turnos_validos: set[str], empleados: set[str]) -> list[FilaImportada]:
    """Lee el Excel y devuelve las filas interpretadas, marcando las que tienen errores."""
    libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    hoja = libro.active
    posiciones: dict[str, int] = {}
    filas: list[FilaImportada] = []
    for numero, valores in enumerate(hoja.iter_rows(values_only=True), start=1):
        if not posiciones:  # todavía buscando la fila de encabezados
            encabezados = [_normalizar(x) for x in valores]
            if "codigo" in encabezados and "fecha" in encabezados:
                for clave, alias in COLUMNAS.items():
                    for nombre in alias:
                        if nombre in encabezados:
                            posiciones[clave] = encabezados.index(nombre)
                            break
                faltantes = set(COLUMNAS) - set(posiciones)
                if faltantes:
                    raise v.ErrorValidacion("El archivo no tiene las columnas: " + ", ".join(sorted(faltantes)))
            continue
        codigo = v.texto(valores[posiciones["codigo"]])
        if not codigo:
            continue
        fila = FilaImportada(numero, codigo, None, "", None, None)
        try:
            fila.fecha = v.fecha(valores[posiciones["fecha"]])
            fila.turno = interpretar_turno(valores[posiciones["turno"]], turnos_validos)
            fila.entrada = v.hora(valores[posiciones["entrada"]], "marca de ingreso")
            fila.salida = v.hora(valores[posiciones["salida"]], "marca de salida")
            if codigo not in empleados:
                fila.observacion = "Empleado no registrado"
            elif turnos_validos and fila.turno not in turnos_validos:
                fila.observacion = f"Turno {fila.turno} no registrado"
        except v.ErrorValidacion as error:
            fila.observacion = str(error)
        filas.append(fila)
    libro.close()
    if not posiciones:
        raise v.ErrorValidacion("No se encontró la fila de encabezados (Codigo, Fecha, Turno...).")
    return filas
