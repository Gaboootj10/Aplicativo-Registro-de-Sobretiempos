"""Utilidades de animación para Tkinter: interpolación de colores y transiciones suaves.

Tkinter no tiene un motor de animación, por lo que cada efecto se construye con
``after()`` llamando a una función por cuadro (unos 60 cuadros por segundo).
"""
from __future__ import annotations

CUADRO_MS = 15


def facilidad(t: float) -> float:
    """Curva ease-out cúbica: arranca rápido y frena al final."""
    return 1 - (1 - t) ** 3


def a_rgb(color: str) -> tuple[int, int, int]:
    """'#RRGGBB' -> (r, g, b)."""
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def mezclar(c1: str, c2: str, t: float) -> str:
    """Color intermedio entre c1 y c2 (t entre 0 y 1)."""
    r1, g1, b1 = a_rgb(c1)
    r2, g2, b2 = a_rgb(c2)
    return "#%02x%02x%02x" % (round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t))


class Animacion:
    """Ejecuta ``paso(t)`` con t de 0 a 1 durante ``duracion`` ms.

    Si se inicia una animación nueva con la misma clave sobre el mismo widget,
    la anterior se cancela (evita parpadeos al pasar el mouse rápido).
    """

    _activas: dict[tuple, str] = {}

    def __init__(self, widget, duracion: int, paso, al_terminar=None, clave: str = "", curva=facilidad):
        self.widget = widget
        self.duracion = max(duracion, 1)
        self.paso = paso
        self.al_terminar = al_terminar
        self.curva = curva
        self.clave = (str(widget), clave)
        self.transcurrido = 0
        anterior = Animacion._activas.pop(self.clave, None)
        if anterior:
            try:
                widget.after_cancel(anterior)
            except Exception:  # noqa: BLE001 - el widget pudo destruirse
                pass
        self._cuadro()

    def _cuadro(self) -> None:
        try:
            if not self.widget.winfo_exists():
                return
        except Exception:  # noqa: BLE001
            return
        t = min(self.transcurrido / self.duracion, 1.0)
        self.paso(self.curva(t))
        if t >= 1.0:
            Animacion._activas.pop(self.clave, None)
            if self.al_terminar:
                self.al_terminar()
            return
        self.transcurrido += CUADRO_MS
        Animacion._activas[self.clave] = self.widget.after(CUADRO_MS, self._cuadro)


def desvanecer(ventana, desde: float, hasta: float, duracion: int = 180, al_terminar=None) -> None:
    """Cambia la opacidad (-alpha) de una ventana Toplevel o Tk."""
    def paso(t):
        try:
            ventana.attributes("-alpha", desde + (hasta - desde) * t)
        except Exception:  # noqa: BLE001
            pass
    Animacion(ventana, duracion, paso, al_terminar, clave="alpha")


def contar(etiqueta, final: float, decimales: int = 0, duracion: int = 900, sufijo: str = "") -> None:
    """Anima un número que sube desde 0 hasta ``final`` en una etiqueta."""
    def paso(t):
        etiqueta.configure(text=f"{final * t:,.{decimales}f}{sufijo}")
    Animacion(etiqueta, duracion, paso, clave="contar")
