"""Exportación de cualquier tabla del aplicativo a un archivo Excel (.xlsx)."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def exportar_excel(ruta: str | Path, titulo: str, columnas: list[str], filas: list[tuple],
                   subtitulo: str = "") -> Path:
    """Crea un libro de Excel con un título, los encabezados y las filas."""
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = titulo[:31]
    hoja["A1"] = titulo
    hoja["A1"].font = Font(bold=True, size=14, color="1F3B57")
    hoja["A2"] = subtitulo or f"Generado el {dt.datetime.now():%d/%m/%Y %H:%M}"
    hoja["A2"].font = Font(italic=True, color="666666")

    encabezado = PatternFill("solid", fgColor="1F3B57")
    for col, nombre in enumerate(columnas, start=1):
        celda = hoja.cell(row=4, column=col, value=nombre)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = encabezado
        celda.alignment = Alignment(horizontal="center")

    for f, fila in enumerate(filas, start=5):
        for c, valor in enumerate(fila, start=1):
            if isinstance(valor, Decimal):
                valor = float(valor)
            elif isinstance(valor, dt.timedelta):
                segundos = int(valor.total_seconds()) % 86400
                valor = f"{segundos // 3600:02d}:{(segundos % 3600) // 60:02d}"
            celda = hoja.cell(row=f, column=c, value=valor)
            if isinstance(valor, dt.date):
                celda.number_format = "DD/MM/YYYY"
            elif isinstance(valor, float):
                celda.number_format = "0.00"

    for col, nombre in enumerate(columnas, start=1):
        ancho = max([len(str(nombre))] + [len(str(f[col - 1] or "")) for f in filas[:300]])
        hoja.column_dimensions[get_column_letter(col)].width = min(max(ancho + 2, 10), 45)
    hoja.freeze_panes = "A5"

    ruta = Path(ruta)
    libro.save(ruta)
    return ruta
