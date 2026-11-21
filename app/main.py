"""Punto de entrada del aplicativo Registro de Sobretiempos.

Arquitectura en tres capas:
    datos/     conexión con MySQL y llamada a procedimientos almacenados
    logica/    validaciones, importación de Excel, exportación, respaldos y reportes
    interfaz/  ventanas y pantallas construidas con Tkinter

Ejecución desde el código fuente:  python app/main.py
"""
import ctypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from interfaz.ventana_principal import VentanaPrincipal  # noqa: E402


def main() -> None:
    """Inicia la ventana principal."""
    try:  # textos nítidos en pantallas con escalado (Windows)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    VentanaPrincipal().mainloop()


if __name__ == "__main__":
    main()
