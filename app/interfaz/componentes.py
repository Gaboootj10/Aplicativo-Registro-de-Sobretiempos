"""Componentes reutilizables de la interfaz.

Botones redondeados con animación, tarjetas con sombra, notificaciones
emergentes, diálogos modales, tabla con resaltado al pasar el mouse,
formulario y barra de filtros. Todo se construye con Tkinter (Canvas,
Frame y ttk), sin frameworks.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass, field
from decimal import Decimal
from tkinter import filedialog, ttk

from datos.conexion import ErrorBaseDatos, Resultado
from interfaz import estilos as e
from interfaz.animacion import Animacion, desvanecer, mezclar
from logica import validaciones as v
from logica.exportador import exportar_excel

TRANSPARENTE = "#010203"   # color que Windows vuelve transparente (esquinas redondeadas)
INSET = 7                  # margen del contenido dentro del marco redondeado


# ------------------------------------------------------------------ utilidades
def fondo_de(widget) -> str:
    """Color de fondo de un widget tk o ttk (para que los Canvas se integren)."""
    try:
        return widget.cget("background")
    except tk.TclError:
        estilo = ""
        try:
            estilo = widget.cget("style")
        except tk.TclError:
            pass
        color = ttk.Style().lookup(estilo or widget.winfo_class(), "background")
        return color or e.FONDO


def redondeado(canvas: tk.Canvas, x1, y1, x2, y2, r=10, **opciones):
    """Dibuja un rectángulo con esquinas redondeadas y devuelve su id."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
              x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(puntos, smooth=True, **opciones)


def raiz_de(widget):
    """Ventana principal de la aplicación."""
    return widget.nametowidget(".")


# ---------------------------------------------------------------------- botón
VARIANTES = {
    # nombre: (fondo, fondo_hover, texto, borde)
    "primario": (e.PRIMARIO, e.PRIMARIO_HOVER, e.BLANCO, None),
    "exito": (e.VERDE, e.VERDE_HOVER, e.BLANCO, None),
    "peligro": (e.ROJO, e.ROJO_HOVER, e.BLANCO, None),
    "aviso": (e.AMBAR, e.AMBAR_HOVER, e.BLANCO, None),
    "secundario": (e.BLANCO, e.SUPERFICIE, e.TEXTO, e.BORDE_FUERTE),
    "suave": (e.PRIMARIO_SUAVE, e.PRIMARIO_TENUE, e.PRIMARIO, None),
    "fantasma": (None, e.PRIMARIO_SUAVE, e.PRIMARIO, None),
}


class Boton(tk.Canvas):
    """Botón con esquinas redondeadas, ícono y transición de color al pasar el mouse."""

    def __init__(self, padre, texto: str = "", comando=None, variante: str = "primario", icono: str = "",
                 alto: int = 36, ancho: int | None = None, fondo: str | None = None):
        self.fondo_padre = fondo or fondo_de(padre)
        self.fuente = tkfont.Font(family=e.FAMILIA_SEMI, size=10)
        self.fuente_icono = tkfont.Font(family=e.ICONOS, size=11)
        ancho_texto = self.fuente.measure(texto) if texto else 0
        ancho_icono = 16 if icono else 0
        separacion = 8 if (texto and icono) else 0
        ancho = ancho or ancho_texto + ancho_icono + separacion + 32
        super().__init__(padre, width=ancho, height=alto, bg=self.fondo_padre, highlightthickness=0, bd=0,
                         cursor="hand2")
        self.comando = comando
        self.texto, self.icono, self.alto, self.ancho = texto, icono, alto, ancho
        self.variante = variante
        self.habilitado = True
        self._actual = self._colores()[0] or self.fondo_padre
        self._dibujar(self._actual)
        self.bind("<Enter>", lambda _e: self._transicion(True))
        self.bind("<Leave>", lambda _e: self._transicion(False))
        self.bind("<ButtonPress-1>", self._presionar)
        self.bind("<ButtonRelease-1>", self._soltar)

    def _colores(self):
        return VARIANTES.get(self.variante, VARIANTES["primario"])

    def _dibujar(self, color, desplazamiento: int = 0) -> None:
        self.delete("all")
        fondo, _hover, texto, borde = self._colores()
        if not self.habilitado:
            color, texto, borde = e.BORDE, e.GRIS_CLARO, None
        redondeado(self, 1, 1 + desplazamiento, self.ancho - 1, self.alto - 1 + desplazamiento, 9,
                   fill=color, outline=borde or color, width=1)
        ancho_texto = self.fuente.measure(self.texto) if self.texto else 0
        total = ancho_texto + (16 if self.icono else 0) + (8 if self.texto and self.icono else 0)
        x = (self.ancho - total) / 2
        y = self.alto / 2 + desplazamiento
        if self.icono:
            self.create_text(x + 8, y + 1, text=self.icono, font=self.fuente_icono, fill=texto)
            x += 24 if self.texto else 16
        if self.texto:
            self.create_text(x, y, text=self.texto, font=self.fuente, fill=texto, anchor="w")

    def _transicion(self, dentro: bool) -> None:
        if not self.habilitado:
            return
        fondo, hover, _texto, _borde = self._colores()
        fondo = fondo or self.fondo_padre
        inicio, fin = self._actual, hover if dentro else fondo

        def paso(t):
            self._actual = mezclar(inicio, fin, t)
            self._dibujar(self._actual)
        Animacion(self, 140, paso, clave="hover")

    def _presionar(self, _evento) -> None:
        if self.habilitado:
            self._dibujar(self._actual, desplazamiento=1)

    def _soltar(self, evento) -> None:
        if not self.habilitado:
            return
        self._dibujar(self._actual)
        if 0 <= evento.x <= self.ancho and 0 <= evento.y <= self.alto and self.comando:
            self.comando()

    def configure(self, cnf=None, **kw):  # noqa: D102 - permite configure(state=...) como ttk.Button
        estado = kw.pop("state", None)
        if estado is not None:
            self.habilitado = estado != "disabled"
            self.configure(cursor="hand2" if self.habilitado else "arrow")
            self._actual = self._colores()[0] or self.fondo_padre
            self._dibujar(self._actual)
        if cnf or kw:
            return super().configure(cnf, **kw)
        return None

    config = configure


# --------------------------------------------------------------------- tarjeta
class Tarjeta(tk.Canvas):
    """Contenedor blanco con esquinas redondeadas y sombra suave.

    Los widgets internos se colocan en ``tarjeta.cuerpo``. Con ``expandir=False``
    la tarjeta toma la altura de su contenido.
    """

    def __init__(self, padre, relleno: int = 18, expandir: bool = False, radio: int = 14,
                 color: str = e.BLANCO, alto: int | None = None):
        super().__init__(padre, bg=fondo_de(padre), highlightthickness=0, bd=0, height=alto or 10)
        self.relleno, self.expandir, self.radio, self.color = relleno, expandir or bool(alto), radio, color
        self.cuerpo = tk.Frame(self, bg=color)
        self._ventana = self.create_window(relleno, relleno, window=self.cuerpo, anchor="nw")
        self.bind("<Configure>", self._redibujar)
        if not self.expandir:
            # el cuerpo puede quedar fuera del área visible al inicio (y no recibir <Configure>),
            # por eso la altura también se ajusta al dibujar y al quedar libre el ciclo de eventos
            self.cuerpo.bind("<Configure>", self._ajustar_altura)
            self.after_idle(self._ajustar_altura)

    def _ajustar_altura(self, _evento=None) -> None:
        try:
            alto = self.cuerpo.winfo_reqheight() + 2 * self.relleno + 3
            if int(self.cget("height")) != alto:
                self.configure(height=alto)
        except tk.TclError:
            pass

    def _redibujar(self, evento) -> None:
        ancho, alto = evento.width, evento.height
        self.delete("fondo")
        redondeado(self, 2, 4, ancho - 2, alto - 1, self.radio, fill=e.SOMBRA, outline="", tags="fondo")
        redondeado(self, 1, 1, ancho - 2, alto - 4, self.radio, fill=self.color, outline=e.BORDE, tags="fondo")
        self.tag_lower("fondo")
        opciones = {"width": max(ancho - 2 * self.relleno, 10)}
        if self.expandir:
            opciones["height"] = max(alto - 2 * self.relleno - 3, 10)
        self.itemconfigure(self._ventana, **opciones)
        if not self.expandir:
            self.after_idle(self._ajustar_altura)


class Insignia(tk.Canvas):
    """Cuadro redondeado de color suave con un ícono (para encabezados e indicadores)."""

    def __init__(self, padre, icono: str, color: str, color_suave: str, tamano: int = 44):
        super().__init__(padre, width=tamano, height=tamano, bg=fondo_de(padre), highlightthickness=0, bd=0)
        redondeado(self, 0, 0, tamano, tamano, tamano // 3.2, fill=color_suave, outline="")
        self.create_text(tamano / 2, tamano / 2 + 1, text=icono, fill=color,
                         font=(e.ICONOS, int(tamano / 2.7)))


# ---------------------------------------------------------- capa oscura modal
class Fondo(tk.Toplevel):
    """Capa semitransparente que oscurece la ventana principal detrás de un diálogo."""

    def __init__(self, raiz):
        super().__init__(raiz)
        self.overrideredirect(True)
        self.configure(bg="#0B1120")
        self.attributes("-alpha", 0.0)
        self.attributes("-topmost", True)
        raiz.update_idletasks()
        self.geometry(f"{raiz.winfo_width()}x{raiz.winfo_height()}+{raiz.winfo_rootx()}+{raiz.winfo_rooty()}")
        desvanecer(self, 0.0, 0.35, 160)


class VentanaFlotante(tk.Toplevel):
    """Ventana sin bordes, con esquinas redondeadas, centrada sobre la principal y con aparición animada."""

    def __init__(self, padre, ancho: int, oscurecer: bool = True):
        self.raiz = raiz_de(padre)
        self.capa = Fondo(self.raiz) if oscurecer and self.raiz.winfo_viewable() else None
        super().__init__(self.raiz)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg=TRANSPARENTE)
        try:
            self.attributes("-transparentcolor", TRANSPARENTE)
        except tk.TclError:
            pass
        self.ancho = ancho
        self.lienzo = tk.Canvas(self, bg=TRANSPARENTE, highlightthickness=0, bd=0, width=ancho)
        self.lienzo.pack(fill="both", expand=True)
        self.contenido = tk.Frame(self.lienzo, bg=e.BLANCO)
        self.lienzo.create_window(INSET, INSET, window=self.contenido, anchor="nw", width=ancho - 2 * INSET)

    def mostrar(self) -> None:
        """Dibuja el fondo redondeado, centra la ventana y la hace aparecer."""
        self.update_idletasks()
        alto = self.contenido.winfo_reqheight() + 2 * INSET
        self.lienzo.configure(height=alto)
        self.lienzo.delete("marco")
        redondeado(self.lienzo, 0, 0, self.ancho - 1, alto - 1, 14, fill=e.BLANCO, outline=e.BORDE_FUERTE,
                   tags="marco")
        self.lienzo.tag_lower("marco")
        self.lienzo.itemconfigure(1, height=alto - 2 * INSET)
        raiz = self.raiz
        if raiz.winfo_viewable():
            x = raiz.winfo_rootx() + (raiz.winfo_width() - self.ancho) // 2
            y = raiz.winfo_rooty() + max((raiz.winfo_height() - alto) // 2 - 20, 20)
        else:
            x = (self.winfo_screenwidth() - self.ancho) // 2
            y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{self.ancho}x{alto}+{x}+{y + 14}")
        desvanecer(self, 0.0, 1.0, 200)
        Animacion(self, 220, lambda t: self.geometry(f"+{x}+{round(y + 14 * (1 - t))}"), clave="subir")
        self.grab_set()
        self.focus_force()

    def sacudir(self) -> None:
        """Sacude la ventana horizontalmente (indica un error)."""
        x, y = self.winfo_x(), self.winfo_y()
        desplazamientos = [10, -10, 8, -8, 5, -5, 2, 0]

        def paso(t):
            indice = min(int(t * len(desplazamientos)), len(desplazamientos) - 1)
            self.geometry(f"+{x + desplazamientos[indice]}+{y}")
        Animacion(self, 360, paso, clave="sacudir", curva=lambda t: t)

    def cerrar(self) -> None:
        """Cierra la ventana con un desvanecimiento."""
        try:
            self.grab_release()
        except tk.TclError:
            pass
        if self.capa:
            desvanecer(self.capa, 0.35, 0.0, 140, self.capa.destroy)
        desvanecer(self, 1.0, 0.0, 120, self.destroy)


# ------------------------------------------------------------ diálogos modales
TIPOS = {
    "error": (e.ICONO["error"], e.ROJO, e.ROJO_SUAVE),
    "info": (e.ICONO["info"], e.PRIMARIO, e.PRIMARIO_SUAVE),
    "exito": (e.ICONO["ok"], e.VERDE, e.VERDE_SUAVE),
    "alerta": (e.ICONO["alerta"], e.AMBAR, e.AMBAR_SUAVE),
}


class Dialogo(VentanaFlotante):
    """Mensaje modal con ícono, título, texto y botones. ``resultado`` indica la respuesta."""

    def __init__(self, padre, titulo: str, mensaje: str, tipo: str = "info", confirmar: bool = False,
                 texto_si: str = "Aceptar", variante_si: str = "primario"):
        super().__init__(padre, 440)
        self.resultado = False
        icono, color, suave = TIPOS.get(tipo, TIPOS["info"])
        marco = tk.Frame(self.contenido, bg=e.BLANCO, padx=26, pady=24)
        marco.pack(fill="both", expand=True)
        fila = tk.Frame(marco, bg=e.BLANCO)
        fila.pack(fill="x")
        Insignia(fila, icono, color, suave, 46).pack(side="left", anchor="n")
        textos = tk.Frame(fila, bg=e.BLANCO)
        textos.pack(side="left", fill="x", expand=True, padx=(16, 0))
        tk.Label(textos, text=titulo, font=e.FUENTE_SUBTITULO, bg=e.BLANCO, fg=e.TEXTO, anchor="w",
                 justify="left", wraplength=320).pack(fill="x")
        tk.Label(textos, text=mensaje, font=e.FUENTE, bg=e.BLANCO, fg=e.TEXTO_2, anchor="w", justify="left",
                 wraplength=320).pack(fill="x", pady=(6, 0))
        botones = tk.Frame(marco, bg=e.BLANCO)
        botones.pack(fill="x", pady=(22, 0))
        Boton(botones, texto_si, self._si, variante_si if confirmar else ("peligro" if tipo == "error" else
                                                                          "primario")).pack(side="right")
        if confirmar:
            Boton(botones, "Cancelar", self.cerrar, "secundario").pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._si())
        self.bind("<Escape>", lambda _e: self.cerrar())
        self.mostrar()

    def _si(self) -> None:
        self.resultado = True
        self.cerrar()


def mostrar_error(padre, error: Exception, titulo: str = "No se pudo completar la operación") -> None:
    """Muestra un error de validación o de la base de datos en un diálogo modal."""
    dialogo = Dialogo(padre, titulo, str(error), "error")
    padre.wait_window(dialogo)


def mostrar_info(padre, mensaje: str, titulo: str = "Operación realizada") -> None:
    """Muestra un mensaje breve como notificación emergente."""
    Notificacion(padre, mensaje, "info", titulo)


def confirmar(padre, mensaje: str, titulo: str = "Confirmar", texto_si: str = "Sí, continuar") -> bool:
    """Pide confirmación al usuario y devuelve True si acepta."""
    dialogo = Dialogo(padre, titulo, mensaje, "alerta", confirmar=True, texto_si=texto_si,
                      variante_si="peligro")
    padre.wait_window(dialogo)
    return dialogo.resultado


def ejecutar_seguro(padre, funcion, *args, exito: str | None = None):
    """Ejecuta una función; si falla muestra el error. Devuelve su resultado o None."""
    try:
        resultado = funcion(*args)
    except (ErrorBaseDatos, v.ErrorValidacion) as error:
        mostrar_error(padre, error)
        return None
    if exito:
        Notificacion(padre, exito, "exito")
    return resultado if resultado is not None else True


# ------------------------------------------------------- notificación emergente
class Notificacion(tk.Toplevel):
    """Aviso que aparece en la esquina inferior derecha, se desliza y desaparece solo."""

    abiertas: list["Notificacion"] = []

    def __init__(self, padre, mensaje: str, tipo: str = "exito", titulo: str | None = None, duracion: int = 3200):
        raiz = raiz_de(padre)
        super().__init__(raiz)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg=TRANSPARENTE)
        try:
            self.attributes("-transparentcolor", TRANSPARENTE)
        except tk.TclError:
            pass
        icono, color, suave = TIPOS.get(tipo, TIPOS["info"])
        titulo = titulo or {"exito": "Listo", "error": "Error", "alerta": "Atención"}.get(tipo, "Aviso")
        ancho = 370
        fuente = tkfont.Font(family=e.FAMILIA, size=10)
        lineas = max(1, sum(fuente.measure(x) // 270 + 1 for x in mensaje.split("\n")))
        alto = 54 + 18 * lineas
        lienzo = tk.Canvas(self, width=ancho, height=alto, bg=TRANSPARENTE, highlightthickness=0, bd=0)
        lienzo.pack()
        redondeado(lienzo, 0, 0, ancho - 1, alto - 1, 14, fill=e.BLANCO, outline=e.BORDE)
        redondeado(lienzo, 0, 0, 6, alto - 1, 3, fill=color, outline="")
        redondeado(lienzo, 18, 16, 50, 48, 10, fill=suave, outline="")
        lienzo.create_text(34, 33, text=icono, font=(e.ICONOS, 12), fill=color)
        lienzo.create_text(64, 18, text=titulo, font=e.FUENTE_NEGRITA, fill=e.TEXTO, anchor="nw")
        lienzo.create_text(64, 40, text=mensaje, font=e.FUENTE, fill=e.TEXTO_2, anchor="nw", width=280)
        lienzo.create_text(ancho - 18, 18, text=e.ICONO["cerrar"], font=(e.ICONOS, 8), fill=e.GRIS_CLARO,
                           tags="cerrar")
        lienzo.tag_bind("cerrar", "<Button-1>", lambda _e: self._salir())
        barra = lienzo.create_line(6, alto - 3, ancho - 8, alto - 3, fill=suave, width=3)

        raiz.update_idletasks()
        apiladas = sum(n.alto + 10 for n in Notificacion.abiertas if n.winfo_exists())
        self.alto = alto
        self.x = raiz.winfo_rootx() + raiz.winfo_width() - ancho - 24
        self.y = raiz.winfo_rooty() + raiz.winfo_height() - alto - 24 - apiladas
        Notificacion.abiertas.append(self)
        self.geometry(f"{ancho}x{alto}+{self.x + 40}+{self.y}")
        desvanecer(self, 0.0, 1.0, 220)
        Animacion(self, 260, lambda t: self.geometry(f"+{round(self.x + 40 * (1 - t))}+{self.y}"), clave="entrar")
        Animacion(lienzo, duracion, lambda t: lienzo.coords(barra, 6, alto - 3, 6 + (ancho - 14) * (1 - t), alto - 3),
                  clave="progreso", curva=lambda t: t)
        self.after(duracion, self._salir)

    def _salir(self) -> None:
        if not self.winfo_exists():
            return
        if self in Notificacion.abiertas:
            Notificacion.abiertas.remove(self)
        desvanecer(self, 1.0, 0.0, 200, self.destroy)


# ------------------------------------------------------------------------- tabla
class Tabla(tk.Frame):
    """Treeview sin bordes, con filas alternas, resaltado al pasar el mouse y mensaje si está vacía."""

    def __init__(self, padre, al_doble_clic=None, altura: int = 15):
        super().__init__(padre, bg=e.BLANCO)
        self.arbol = ttk.Treeview(self, show="headings", height=altura, selectmode="browse")
        barra_v = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        barra_h = ttk.Scrollbar(self, orient="horizontal", command=self.arbol.xview)
        self.arbol.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
        self.arbol.grid(row=0, column=0, sticky="nsew")
        barra_v.grid(row=0, column=1, sticky="ns")
        barra_h.grid(row=1, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.arbol.tag_configure("par", background=e.SUPERFICIE)
        self.arbol.tag_configure("alerta", foreground=e.ROJO_HOVER)
        self.arbol.tag_configure("hover", background=e.PRIMARIO_SUAVE)
        self.vacio = tk.Label(self, text=f"{e.ICONO['buscar']}", font=(e.ICONOS, 22), fg=e.BORDE_FUERTE, bg=e.BLANCO,
                              compound="top")
        self.vacio_texto = tk.Label(self, text="No hay registros para mostrar", font=e.FUENTE, fg=e.GRIS_CLARO,
                                    bg=e.BLANCO)
        self.resultado = Resultado()
        self.ocultas: set[str] = set()
        self._hover = ""
        self.arbol.bind("<Motion>", self._mover)
        self.arbol.bind("<Leave>", lambda _e: self._resaltar(""))
        if al_doble_clic:
            self.arbol.bind("<Double-1>", lambda _e: al_doble_clic())

    def _mover(self, evento) -> None:
        self._resaltar(self.arbol.identify_row(evento.y))

    def _resaltar(self, fila: str) -> None:
        if fila == self._hover:
            return
        if self._hover and self.arbol.exists(self._hover):
            etiquetas = [t for t in self.arbol.item(self._hover, "tags") if t != "hover"]
            self.arbol.item(self._hover, tags=etiquetas)
        self._hover = fila
        if fila:
            self.arbol.item(fila, tags=list(self.arbol.item(fila, "tags")) + ["hover"])

    def cargar(self, resultado: Resultado, ocultar: tuple[str, ...] = (), alerta=None) -> None:
        """Muestra las filas del resultado. ``alerta(fila_dict)`` resalta filas en rojo."""
        self.resultado = resultado
        self.ocultas = set(ocultar)
        self._hover = ""
        visibles = [c for c in resultado.columnas if c not in self.ocultas]
        self.arbol.delete(*self.arbol.get_children())
        self.arbol.configure(columns=resultado.columnas, displaycolumns=visibles)
        anchos = {}
        for indice, columna in enumerate(resultado.columnas):
            valores = [f[indice] for f in resultado.filas[:200]]
            ancho = max([len(columna)] + [len(v.mostrar(x)) for x in valores])
            numerico = any(isinstance(x, (int, float, Decimal)) and not isinstance(x, bool) for x in valores)
            anchos[columna] = (min(max(ancho * 7 + 24, 64), 300), numerico)
        disponible = max(self.winfo_width(), 900)
        estirar = sum(a for c, (a, _n) in anchos.items() if c not in self.ocultas) <= disponible
        for columna, (ancho, numerico) in anchos.items():
            self.arbol.heading(columna, text=columna, anchor="e" if numerico else "w")
            self.arbol.column(columna, width=ancho, minwidth=ancho if not estirar else 40,
                              anchor="e" if numerico else "w", stretch=estirar)
        for i, fila in enumerate(resultado.filas):
            etiquetas = ["par"] if i % 2 else []
            if alerta and alerta(dict(zip(resultado.columnas, fila))):
                etiquetas.append("alerta")
            self.arbol.insert("", "end", iid=str(i), values=[v.mostrar(x) for x in fila], tags=etiquetas)
        if resultado.filas:
            self.vacio.place_forget()
            self.vacio_texto.place_forget()
        else:
            self.vacio.place(relx=0.5, rely=0.42, anchor="center")
            self.vacio_texto.place(relx=0.5, rely=0.42, anchor="n", y=26)

    def seleccion(self) -> dict | None:
        """Devuelve la fila seleccionada como diccionario con los valores originales."""
        elegido = self.arbol.selection()
        if not elegido:
            return None
        return dict(zip(self.resultado.columnas, self.resultado.filas[int(elegido[0])]))

    def exportar(self, padre, titulo: str, subtitulo: str = "") -> None:
        """Exporta el contenido actual a Excel, preguntando dónde guardarlo."""
        if not self.resultado.filas:
            Notificacion(padre, "No hay datos para exportar.", "alerta")
            return
        ruta = filedialog.asksaveasfilename(parent=padre, defaultextension=".xlsx",
                                            initialfile=f"{titulo}.xlsx",
                                            filetypes=[("Libro de Excel", "*.xlsx")])
        if ruta:
            exportar_excel(ruta, titulo, self.resultado.columnas, self.resultado.filas, subtitulo)
            Notificacion(padre, f"Archivo guardado:\n{ruta}", "exito", "Exportado a Excel")


# --------------------------------------------------------- entrada con ayuda
class Entrada(ttk.Entry):
    """Entry con texto de ayuda (placeholder) que desaparece al escribir."""

    def __init__(self, padre, textvariable: tk.StringVar, ayuda: str = "", **opciones):
        opciones.setdefault("font", e.FUENTE)
        super().__init__(padre, textvariable=textvariable, **opciones)
        self.variable = textvariable
        self.ayuda = tk.Label(self, text=ayuda, font=e.FUENTE, fg=e.GRIS_CLARO, bg=e.BLANCO, cursor="xterm")
        self.ayuda.bind("<Button-1>", lambda _e: self.focus_set())
        textvariable.trace_add("write", lambda *_a: self._actualizar())
        self.bind("<FocusIn>", lambda _e: self._actualizar(), add="+")
        self.bind("<FocusOut>", lambda _e: self._actualizar(), add="+")
        self.after_idle(self._actualizar)

    def _actualizar(self) -> None:
        try:
            if self.variable.get() or (self.focus_get() == self) or str(self.cget("state")) == "readonly":
                self.ayuda.place_forget()
            else:
                self.ayuda.place(x=9, rely=0.5, anchor="w")
        except (tk.TclError, KeyError):
            pass


# -------------------------------------------------------------------- formulario
@dataclass
class Campo:
    """Definición de un campo del formulario."""

    clave: str
    etiqueta: str
    tipo: str = "texto"                 # texto | combo | fecha | hora
    opciones: list = field(default_factory=list)   # [(valor, texto)] para combo
    solo_lectura: bool = False
    ayuda: str = ""


class Formulario(VentanaFlotante):
    """Ventana modal que pide los datos de un registro; los errores se muestran en la misma ventana."""

    def __init__(self, padre, titulo: str, campos: list[Campo], valores: dict | None = None,
                 al_guardar=None, icono: str = ""):
        super().__init__(padre, 560)
        self.campos = campos
        self.al_guardar = al_guardar
        self.variables: dict[str, tk.StringVar] = {}
        self.combos: dict[str, dict[str, str]] = {}
        valores = valores or {}
        nuevo = titulo.lower().startswith("nuevo")

        cabecera = tk.Frame(self.contenido, bg=e.BLANCO, padx=26, pady=20)
        cabecera.pack(fill="x")
        Insignia(cabecera, icono or (e.ICONO["agregar"] if nuevo else e.ICONO["editar"]),
                 e.PRIMARIO if nuevo else e.AMBAR_HOVER, e.PRIMARIO_SUAVE if nuevo else e.AMBAR_SUAVE, 42
                 ).pack(side="left")
        textos = tk.Frame(cabecera, bg=e.BLANCO)
        textos.pack(side="left", padx=14)
        tk.Label(textos, text=titulo, font=e.FUENTE_SUBTITULO, bg=e.BLANCO, fg=e.TEXTO).pack(anchor="w")
        tk.Label(textos, text="Complete los datos y presione Guardar", font=e.FUENTE_PEQUENA, bg=e.BLANCO,
                 fg=e.GRIS).pack(anchor="w")
        cerrar = tk.Label(cabecera, text=e.ICONO["cerrar"], font=(e.ICONOS, 10), bg=e.BLANCO, fg=e.GRIS_CLARO,
                          cursor="hand2")
        cerrar.pack(side="right", anchor="n")
        cerrar.bind("<Button-1>", lambda _e: self.cerrar())
        tk.Frame(self.contenido, bg=e.BORDE, height=1).pack(fill="x")

        cuerpo = tk.Frame(self.contenido, bg=e.BLANCO, padx=26, pady=16)
        cuerpo.pack(fill="both")
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=1)
        primero = None
        for indice, campo in enumerate(campos):
            fila, columna = divmod(indice, 2) if len(campos) > 4 else (indice, 0)
            celda = tk.Frame(cuerpo, bg=e.BLANCO)
            celda.grid(row=fila, column=columna, columnspan=1 if len(campos) > 4 else 2, sticky="new",
                       padx=(0, 12) if columna == 0 else (0, 0), pady=6)
            linea = tk.Frame(celda, bg=e.BLANCO)
            linea.pack(fill="x")
            ttk.Label(linea, text=campo.etiqueta, style="Campo.TLabel").pack(side="left")
            variable = tk.StringVar(value=self._valor_inicial(campo, valores.get(campo.clave)))
            self.variables[campo.clave] = variable
            if campo.tipo == "combo":
                textos_combo = {texto: valor for valor, texto in campo.opciones}
                self.combos[campo.clave] = textos_combo
                widget = ttk.Combobox(celda, textvariable=variable, values=list(textos_combo), font=e.FUENTE,
                                      state="disabled" if campo.solo_lectura else "readonly")
            else:
                ayuda = {"fecha": "DD/MM/AAAA", "hora": "HH:MM"}.get(campo.tipo, "")
                widget = Entrada(celda, variable, ayuda, state="readonly" if campo.solo_lectura else "normal")
            widget.pack(fill="x", pady=(4, 0))
            if campo.ayuda:
                tk.Label(celda, text=campo.ayuda, font=e.FUENTE_PEQUENA, bg=e.BLANCO, fg=e.GRIS_CLARO,
                         anchor="w").pack(fill="x", pady=(2, 0))
            if primero is None and not campo.solo_lectura:
                primero = widget

        self.error = tk.Label(self.contenido, text="", font=e.FUENTE, bg=e.ROJO_SUAVE, fg=e.ROJO_HOVER,
                              anchor="w", padx=14, pady=8, wraplength=490, justify="left")
        pie = tk.Frame(self.contenido, bg=e.SUPERFICIE, padx=26, pady=14)
        pie.pack(fill="x", side="bottom")
        Boton(pie, "Guardar", self._guardar, "primario", e.ICONO["guardar"]).pack(side="right")
        Boton(pie, "Cancelar", self.cerrar, "secundario").pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._guardar())
        self.bind("<Escape>", lambda _e: self.cerrar())
        self.mostrar()
        if primero is not None:
            primero.focus_set()

    @staticmethod
    def _valor_inicial(campo: Campo, valor) -> str:
        """Convierte el valor del registro en el texto que se muestra en el campo."""
        if campo.tipo == "combo":
            for clave, texto in campo.opciones:
                if str(clave) == str(valor):
                    return texto
            return ""
        return v.mostrar(valor)

    def datos(self) -> dict:
        """Devuelve los valores del formulario ya convertidos (fecha, hora, código)."""
        resultado = {}
        for campo in self.campos:
            texto = self.variables[campo.clave].get().strip()
            if campo.tipo == "combo":
                resultado[campo.clave] = self.combos[campo.clave].get(texto, "")
            elif campo.tipo == "fecha":
                resultado[campo.clave] = v.fecha(texto, campo.etiqueta.lower(), obligatorio=False)
            elif campo.tipo == "hora":
                resultado[campo.clave] = v.hora(texto, campo.etiqueta.lower())
            else:
                resultado[campo.clave] = texto
        return resultado

    def _mostrar_error(self, error: Exception) -> None:
        self.error.configure(text=f"  {error}")
        if not self.error.winfo_ismapped():
            self.error.pack(fill="x", padx=26, pady=(0, 14), before=self.contenido.winfo_children()[-1])
        self.mostrar_tamano()
        self.sacudir()

    def mostrar_tamano(self) -> None:
        """Ajusta el alto de la ventana a su contenido (al aparecer el mensaje de error)."""
        self.update_idletasks()
        alto = self.contenido.winfo_reqheight() + 2 * INSET
        self.lienzo.configure(height=alto)
        self.lienzo.delete("marco")
        redondeado(self.lienzo, 0, 0, self.ancho - 1, alto - 1, 14, fill=e.BLANCO, outline=e.BORDE_FUERTE,
                   tags="marco")
        self.lienzo.tag_lower("marco")
        self.lienzo.itemconfigure(1, height=alto - 2 * INSET)
        self.geometry(f"{self.ancho}x{alto}")

    def _guardar(self) -> None:
        """Valida y entrega los datos a ``al_guardar``; cierra si no hubo errores."""
        try:
            datos = self.datos()
            if self.al_guardar:
                self.al_guardar(datos)
        except (ErrorBaseDatos, v.ErrorValidacion) as error:
            self._mostrar_error(error)
            return
        self.cerrar()


# ----------------------------------------------------------- barra de filtros
class BarraFiltros(tk.Frame):
    """Búsqueda por texto y rango de fechas opcional."""

    def __init__(self, padre, al_buscar, fechas: bool = False, texto_busqueda: str = "Buscar"):
        super().__init__(padre, bg=fondo_de(padre))
        self.al_buscar = al_buscar
        self.buscar = tk.StringVar()
        self.desde = tk.StringVar()
        self.hasta = tk.StringVar()
        fondo = fondo_de(padre)
        tk.Label(self, text=e.ICONO["buscar"], font=(e.ICONOS, 11), bg=fondo, fg=e.GRIS).pack(side="left")
        entrada = Entrada(self, self.buscar, texto_busqueda, width=30)
        entrada.pack(side="left", padx=(8, 14))
        entrada.bind("<Return>", lambda _e: self.al_buscar())
        if fechas:
            tk.Label(self, text=e.ICONO["calendario"], font=(e.ICONOS, 11), bg=fondo, fg=e.GRIS).pack(side="left")
            for variable, ayuda in ((self.desde, "Desde"), (self.hasta, "Hasta")):
                campo = Entrada(self, variable, f"{ayuda} DD/MM/AAAA", width=17)
                campo.pack(side="left", padx=(8, 0))
                campo.bind("<Return>", lambda _e: self.al_buscar())
            tk.Frame(self, bg=fondo, width=14).pack(side="left")
        Boton(self, "Buscar", self.al_buscar, "suave", e.ICONO["buscar"], fondo=fondo).pack(side="left")
        Boton(self, "Limpiar", self.limpiar, "fantasma", e.ICONO["limpiar"], fondo=fondo).pack(side="left", padx=6)

    def valores(self) -> tuple:
        """Devuelve (texto, desde, hasta) validados."""
        return (self.buscar.get().strip(),
                v.fecha(self.desde.get(), "fecha desde", obligatorio=False),
                v.fecha(self.hasta.get(), "fecha hasta", obligatorio=False))

    def limpiar(self) -> None:
        """Borra los filtros y vuelve a buscar."""
        for variable in (self.buscar, self.desde, self.hasta):
            variable.set("")
        self.al_buscar()


def encabezado(padre, titulo: str, descripcion: str, icono: str = "", color: str = e.PRIMARIO,
               color_suave: str = e.PRIMARIO_SUAVE) -> tk.Frame:
    """Título de una pantalla con ícono y descripción."""
    marco = tk.Frame(padre, bg=fondo_de(padre))
    if icono:
        Insignia(marco, icono, color, color_suave, 48).pack(side="left", padx=(0, 14))
    textos = tk.Frame(marco, bg=fondo_de(padre))
    textos.pack(side="left", fill="x", expand=True)
    tk.Label(textos, text=titulo, font=e.FUENTE_TITULO, bg=fondo_de(padre), fg=e.TEXTO, anchor="w").pack(fill="x")
    if descripcion:
        tk.Label(textos, text=descripcion, font=e.FUENTE, bg=fondo_de(padre), fg=e.GRIS, anchor="w",
                 justify="left", wraplength=980).pack(fill="x")
    return marco
