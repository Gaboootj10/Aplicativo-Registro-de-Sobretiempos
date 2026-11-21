"""Capa lógica: conversión y validación de los datos que ingresa el usuario.

Las reglas definitivas se validan en los procedimientos almacenados; aquí
solo se revisa el formato para avisar al usuario antes de llamar a MySQL.
"""
from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal


class ErrorValidacion(Exception):
    """Dato ingresado con un formato incorrecto."""


def texto(valor) -> str:
    """Devuelve el valor como texto sin espacios a los lados."""
    return "" if valor is None else str(valor).strip()


def fecha(valor, campo: str = "fecha", obligatorio: bool = True) -> dt.date | None:
    """Convierte 'DD/MM/AAAA' o 'AAAA-MM-DD' en un objeto date."""
    if isinstance(valor, dt.datetime):
        return valor.date()
    if isinstance(valor, dt.date):
        return valor
    cadena = texto(valor)
    if not cadena:
        if obligatorio:
            raise ErrorValidacion(f"Ingrese la {campo}.")
        return None
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(cadena, formato).date()
        except ValueError:
            continue
    raise ErrorValidacion(f"La {campo} debe tener el formato DD/MM/AAAA.")


def hora(valor, campo: str = "hora", obligatorio: bool = False) -> dt.time | None:
    """Convierte 'HH:MM' (o 'H:MM') en un objeto time. '-' o vacío es None."""
    if isinstance(valor, dt.time):
        return valor
    if isinstance(valor, dt.datetime):
        return valor.time()
    if isinstance(valor, dt.timedelta):
        segundos = int(valor.total_seconds()) % 86400
        return dt.time(segundos // 3600, (segundos % 3600) // 60)
    cadena = texto(valor)
    if cadena in ("", "-", "--"):
        if obligatorio:
            raise ErrorValidacion(f"Ingrese la {campo}.")
        return None
    coincidencia = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", cadena)
    if not coincidencia:
        raise ErrorValidacion(f"La {campo} debe tener el formato HH:MM (por ejemplo 07:30).")
    horas, minutos = int(coincidencia.group(1)), int(coincidencia.group(2))
    if horas > 23 or minutos > 59:
        raise ErrorValidacion(f"La {campo} {cadena} no es válida.")
    return dt.time(horas, minutos)


def digitos(valor, cantidad: int, campo: str) -> str:
    """Valida que el valor tenga exactamente ``cantidad`` dígitos."""
    cadena = texto(valor)
    if not re.fullmatch(rf"\d{{{cantidad}}}", cadena):
        raise ErrorValidacion(f"El {campo} debe tener {cantidad} dígitos.")
    return cadena


def longitud(valor, cantidad: int, campo: str) -> str:
    """Valida que el texto tenga exactamente ``cantidad`` caracteres."""
    cadena = texto(valor).upper()
    if len(cadena) != cantidad:
        raise ErrorValidacion(f"El {campo} debe tener {cantidad} caracteres.")
    return cadena


def obligatorio(valor, campo: str) -> str:
    """Valida que el texto no esté vacío."""
    cadena = texto(valor)
    if not cadena:
        raise ErrorValidacion(f"Ingrese {campo}.")
    return cadena


def mostrar(valor) -> str:
    """Formatea un valor de la base de datos para mostrarlo en pantalla."""
    if valor is None:
        return ""
    if isinstance(valor, dt.datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, dt.date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, dt.timedelta):
        h = hora(valor)
        return h.strftime("%H:%M")
    if isinstance(valor, Decimal):
        return f"{valor:.2f}"
    return str(valor)
