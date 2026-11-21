"""Ventana principal: pantalla de carga, barra lateral animada y área de contenido."""
from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont

from datos.conexion import BaseDatos, ErrorBaseDatos
from datos.configuracion import ConfiguracionMySQL, ruta_recurso
from interfaz import componentes as c
from interfaz import estilos as e
from interfaz.animacion import Animacion, desvanecer, mezclar
from interfaz.pantallas_herramientas import DialogoConexion, PantallaImportar, PantallaRespaldo
from interfaz.pantallas_procesos import PantallaPanel, PantallaReportes, PantallaSap
from interfaz.pantallas_registro import (PantallaAsistencias, PantallaEmpleados, PantallaMaestros,
                                         PantallaSobretiempos)

VERSION = "1.1.0"
NOMBRE = "SobreTiempos"
LEMA = "Gestión de horas extra"

# (clave, texto del menú, clase de la pantalla)
MODULOS = [
    ("panel", "Panel de control", PantallaPanel),
    ("empleados", "Empleados", PantallaEmpleados),
    ("asistencias", "Asistencias", PantallaAsistencias),
    ("sobretiempos", "Sobretiempos", PantallaSobretiempos),
    ("sap", "Consolidación SAP", PantallaSap),
    ("reportes", "Reportes", PantallaReportes),
    ("importar", "Importar asistencias", PantallaImportar),
    ("maestros", "Datos maestros", PantallaMaestros),
    ("respaldo", "Respaldo", PantallaRespaldo),
]

ANCHO_LATERAL = 248
INICIO_MENU = 148
ALTO_ITEM = 46


def logotipo(lienzo: tk.Canvas, x: float, y: float, tamano: int) -> None:
    """Dibuja el logotipo: cuadro redondeado índigo con un reloj."""
    c.redondeado(lienzo, x, y, x + tamano, y + tamano, tamano / 3.4, fill=e.PRIMARIO, outline="")
    c.redondeado(lienzo, x + 3, y + 3, x + tamano - 3, y + tamano * 0.55, tamano / 4, fill=e.PRIMARIO_CLARO, outline="")
    lienzo.create_text(x + tamano / 2, y + tamano / 2 + 1, text=e.ICONO["reloj"], fill=e.BLANCO,
                       font=(e.ICONOS, int(tamano / 2.4)))


# --------------------------------------------------------------- pantalla inicial
class PantallaCarga(tk.Toplevel):
    """Ventana de bienvenida con barra de carga animada mientras se conecta con MySQL."""

    def __init__(self, raiz):
        super().__init__(raiz)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg=c.TRANSPARENTE)
        try:
            self.attributes("-transparentcolor", c.TRANSPARENTE)
        except tk.TclError:
            pass
        ancho, alto = 520, 300
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.lienzo = tk.Canvas(self, width=ancho, height=alto, bg=c.TRANSPARENTE, highlightthickness=0, bd=0)
        self.lienzo.pack()
        lz = self.lienzo
        c.redondeado(lz, 0, 0, ancho - 1, alto - 1, 22, fill=e.LATERAL, outline="")
        for radio, tono in ((190, 0.35), (130, 0.55), (75, 0.8)):  # círculos decorativos
            lz.create_oval(ancho - 60 - radio, -40 - radio, ancho - 60 + radio, -40 + radio,
                           fill=mezclar(e.LATERAL, "#064E3B", tono * 0.6), outline="")
        # máscara de la esquina superior derecha para conservar el borde redondeado
        r = 22
        arco = [(ancho - r + r * math.sin(a * math.pi / 40), r - r * math.cos(a * math.pi / 40)) for a in range(21)]
        lz.create_polygon([(ancho - r, -1), (ancho + 1, -1), (ancho + 1, r)] + arco[::-1], fill=c.TRANSPARENTE,
                          outline=c.TRANSPARENTE)
        logotipo(lz, 44, 54, 64)
        lz.create_text(128, 70, text=NOMBRE, anchor="w", fill=e.BLANCO, font=(e.FAMILIA_SEMI, 24))
        lz.create_text(130, 104, text=LEMA, anchor="w", fill=e.GRIS_CLARO, font=(e.FAMILIA, 11))
        self.estado = lz.create_text(44, 208, text="Iniciando...", anchor="w", fill=e.GRIS_CLARO, font=e.FUENTE)
        c.redondeado(lz, 44, 232, ancho - 44, 238, 3, fill="#1E293B", outline="")
        self.barra = c.redondeado(lz, 44, 232, 124, 238, 3, fill=e.PRIMARIO, outline="")
        lz.create_text(ancho - 44, alto - 28, text=f"versión {VERSION}", anchor="e", fill="#475569",
                       font=e.FUENTE_PEQUENA)
        self.ancho = ancho
        self._pos = 0.0
        self._moviendo = True
        desvanecer(self, 0.0, 1.0, 260)
        self._mover()

    def _mover(self) -> None:
        """Mueve el segmento de la barra de un lado a otro (carga indeterminada)."""
        if not self._moviendo or not self.winfo_exists():
            return
        self._pos = (self._pos + 0.018) % 1.0
        recorrido = self.ancho - 88 - 80
        x = 44 + recorrido * (0.5 - 0.5 * math.cos(self._pos * 2 * math.pi))
        self.lienzo.coords(self.barra, *self._puntos(x, 232, x + 80, 238, 3))
        self.after(15, self._mover)

    @staticmethod
    def _puntos(x1, y1, x2, y2, r):
        return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
                x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]

    def mensaje(self, texto: str) -> None:
        self.lienzo.itemconfigure(self.estado, text=texto)
        self.update()

    def cerrar(self, al_terminar) -> None:
        """Completa la barra y desaparece."""
        self._moviendo = False

        def paso(t):
            self.lienzo.coords(self.barra, *self._puntos(44, 232, 124 + (self.ancho - 168) * t, 238, 3))
        Animacion(self, 260, paso, lambda: desvanecer(self, 1.0, 0.0, 220, lambda: (self.destroy(), al_terminar())),
                  clave="completar")


# ------------------------------------------------------------------ barra lateral
class BarraLateral(tk.Canvas):
    """Menú lateral con degradado, íconos, resaltado al pasar el mouse y marcador deslizante."""

    def __init__(self, padre, al_elegir, al_conexion):
        super().__init__(padre, width=ANCHO_LATERAL, bg=e.LATERAL, highlightthickness=0, bd=0)
        self.al_elegir = al_elegir
        self.al_conexion = al_conexion
        self.fuente = tkfont.Font(family=e.FAMILIA, size=10)
        self.fuente_activa = tkfont.Font(family=e.FAMILIA_SEMI, size=10)
        self.activo: str | None = None
        self.y_marcador = INICIO_MENU
        self.colores: dict[str, str] = {}
        self.estado_texto = ("Sin conexión", "")
        self.conectado = False
        self._pulso = 0.0
        self.bind("<Configure>", lambda _e: self._dibujar())
        self._latir()

    def _y(self, clave: str) -> int:
        indice = [m[0] for m in MODULOS].index(clave)
        return INICIO_MENU + indice * ALTO_ITEM

    def _dibujar(self) -> None:
        self.delete("all")
        alto = max(self.winfo_height(), 600)
        pasos = 60
        for i in range(pasos):  # degradado vertical
            y0, y1 = alto * i / pasos, alto * (i + 1) / pasos + 1
            self.create_rectangle(0, y0, ANCHO_LATERAL, y1, fill=mezclar(e.LATERAL, e.LATERAL_2, i / pasos),
                                  outline="")
        logotipo(self, 22, 26, 44)
        self.create_text(78, 38, text=NOMBRE, anchor="w", fill=e.BLANCO, font=(e.FAMILIA_SEMI, 15))
        self.create_text(79, 60, text=LEMA, anchor="w", fill=e.GRIS_CLARO, font=e.FUENTE_PEQUENA)
        self.create_text(24, INICIO_MENU - 24, text="MENÚ PRINCIPAL", anchor="w", fill="#64748B",
                         font=(e.FAMILIA_SEMI, 8))
        y = self._y(self.activo) if self.activo else INICIO_MENU
        self.y_marcador = y
        self.marcador = c.redondeado(self, 14, y + 3, ANCHO_LATERAL - 14, y + ALTO_ITEM - 3, 11,
                                     fill=e.PRIMARIO, outline="", tags="marcador")
        self.brillo = self.create_rectangle(14, y + 13, 17, y + ALTO_ITEM - 13, fill="#6EE7B7", outline="",
                                            tags="marcador")
        for clave, texto, _clase in MODULOS:
            y = self._y(clave)
            etiqueta = f"item_{clave}"
            c.redondeado(self, 14, y + 3, ANCHO_LATERAL - 14, y + ALTO_ITEM - 3, 11, fill="", outline="",
                         tags=(etiqueta, f"fondo_{clave}"))
            color = e.BLANCO if clave == self.activo else self.colores.get(clave, e.GRIS_CLARO)
            self.create_text(40, y + ALTO_ITEM / 2 + 1, text=e.ICONO[clave], fill=color, font=(e.ICONOS, 12),
                             tags=(etiqueta, f"texto_{clave}"))
            self.create_text(64, y + ALTO_ITEM / 2, text=texto, anchor="w", fill=color,
                             font=self.fuente_activa if clave == self.activo else self.fuente,
                             tags=(etiqueta, f"texto_{clave}", f"rotulo_{clave}"))
            self.tag_bind(etiqueta, "<Enter>", lambda _e, k=clave: self._hover(k, True))
            self.tag_bind(etiqueta, "<Leave>", lambda _e, k=clave: self._hover(k, False))
            self.tag_bind(etiqueta, "<Button-1>", lambda _e, k=clave: self.al_elegir(k))
        self.tag_raise("marcador")
        for clave, _t, _c in MODULOS:
            self.tag_raise(f"texto_{clave}")
        self._pie(alto)

    def _pie(self, alto: int) -> None:
        y = alto - 128
        c.redondeado(self, 14, y, ANCHO_LATERAL - 14, y + 66, 12, fill="#1E293B", outline="#334155")
        self.punto = self.create_oval(30, y + 18, 40, y + 28, fill=e.VERDE if self.conectado else e.ROJO, outline="")
        self.halo = self.create_oval(30, y + 18, 40, y + 28, outline=e.VERDE if self.conectado else e.ROJO)
        self.create_text(50, y + 23, text=self.estado_texto[0], anchor="w", fill=e.BLANCO, font=e.FUENTE_NEGRITA)
        self.create_text(30, y + 46, text=self.estado_texto[1], anchor="w", fill=e.GRIS_CLARO,
                         font=e.FUENTE_PEQUENA, width=ANCHO_LATERAL - 56)
        y2 = alto - 52
        self.create_text(40, y2 + 16, text=e.ICONO["conexion"], fill=e.GRIS_CLARO, font=(e.ICONOS, 11),
                         tags="conexion")
        self.create_text(64, y2 + 15, text="Configurar conexión", anchor="w", fill=e.GRIS_CLARO, font=self.fuente,
                         tags="conexion")
        self.create_text(ANCHO_LATERAL - 24, y2 + 15, text=f"v{VERSION}", anchor="e", fill="#475569",
                         font=e.FUENTE_PEQUENA)
        self.tag_bind("conexion", "<Button-1>", lambda _e: self.al_conexion())
        self.tag_bind("conexion", "<Enter>", lambda _e: (self.itemconfigure("conexion", fill=e.BLANCO),
                                                        self.configure(cursor="hand2")))
        self.tag_bind("conexion", "<Leave>", lambda _e: (self.itemconfigure("conexion", fill=e.GRIS_CLARO),
                                                        self.configure(cursor="")))

    def _latir(self) -> None:
        """Animación continua del indicador de conexión (halo que crece y se desvanece)."""
        try:
            self._pulso = (self._pulso + 0.035) % 1.0
            if hasattr(self, "halo"):
                x0, y0, x1, y1 = self.coords(self.punto)
                cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, 5 + 7 * self._pulso
                self.coords(self.halo, cx - r, cy - r, cx + r, cy + r)
                base = e.VERDE if self.conectado else e.ROJO
                self.itemconfigure(self.halo, outline=mezclar(base, "#1E293B", self._pulso))
            self.after(40, self._latir)
        except tk.TclError:
            pass

    def _hover(self, clave: str, dentro: bool) -> None:
        self.configure(cursor="hand2" if dentro else "")
        if clave == self.activo:
            return
        self.itemconfigure(f"fondo_{clave}", fill=e.LATERAL_HOVER if dentro else "")
        inicio = self.colores.get(clave, e.GRIS_CLARO)
        fin = e.BLANCO if dentro else e.GRIS_CLARO

        def paso(t):
            self.colores[clave] = mezclar(inicio, fin, t)
            self.itemconfigure(f"texto_{clave}", fill=self.colores[clave])
        Animacion(self, 150, paso, clave=f"hover_{clave}")

    def activar(self, clave: str) -> None:
        """Mueve el marcador hasta el módulo elegido con una animación."""
        anterior = self.activo
        self.activo = clave
        if anterior:
            self.colores[anterior] = e.GRIS_CLARO
            self.itemconfigure(f"texto_{anterior}", fill=e.GRIS_CLARO)
            self.itemconfigure(f"rotulo_{anterior}", font=self.fuente)
        self.itemconfigure(f"fondo_{clave}", fill="")
        self.itemconfigure(f"texto_{clave}", fill=e.BLANCO)
        self.itemconfigure(f"rotulo_{clave}", font=self.fuente_activa)
        inicio, fin = self.y_marcador, self._y(clave)

        def paso(t):
            nuevo = inicio + (fin - inicio) * t
            self.move("marcador", 0, nuevo - self.y_marcador)
            self.y_marcador = nuevo
        Animacion(self, 260, paso, clave="marcador")

    def estado(self, conectado: bool, titulo: str, detalle: str) -> None:
        self.conectado = conectado
        self.estado_texto = (titulo, detalle)
        self._dibujar()


# ------------------------------------------------------------- ventana principal
class VentanaPrincipal(tk.Tk):
    """Ventana principal del aplicativo Registro de Sobretiempos."""

    def __init__(self, mostrar_carga: bool = True):
        super().__init__()
        self.withdraw()
        self.title("Registro de Sobretiempos")
        self.geometry("1360x820")
        self.minsize(1180, 700)
        e.aplicar_estilos(self)
        icono = ruta_recurso("icono.png")
        if icono.exists():
            self._icono = tk.PhotoImage(file=str(icono))
            self.iconphoto(True, self._icono)
        self.config_mysql = ConfiguracionMySQL.cargar()
        self.bd = BaseDatos(self.config_mysql)
        self.pantallas: dict[str, tk.Frame] = {}
        self.actual: str | None = None
        self.lateral = BarraLateral(self, self.mostrar, self.abrir_conexion)
        self.lateral.pack(side="left", fill="y")
        self.contenido = tk.Frame(self, bg=e.FONDO)
        self.contenido.pack(side="left", fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.salir)
        if mostrar_carga:
            self.carga = PantallaCarga(self)
            self.after(900, self._iniciar)
        else:
            self.carga = None
            self.deiconify()
            self.after(50, self._iniciar)

    def _iniciar(self) -> None:
        """Prueba la conexión mientras se muestra la pantalla de carga."""
        error = None
        if self.carga:
            self.carga.mensaje("Conectando con la base de datos...")
        try:
            self.bd.conexion()
            if self.carga:
                self.carga.mensaje("Cargando módulos...")
        except ErrorBaseDatos as problema:
            error = problema

        def continuar():
            self.attributes("-alpha", 0.0)
            self.deiconify()
            desvanecer(self, 0.0, 1.0, 260)
            if error is None:
                self._conectado()
            else:
                self.lateral.estado(False, "Sin conexión", "Configure los datos de MySQL")
                self.after(300, lambda: (c.mostrar_error(self, error, "No se pudo conectar con la base de datos"),
                                         self.abrir_conexion()))
        if self.carga:
            self.carga.cerrar(continuar)
        else:
            continuar()

    def _conectado(self) -> None:
        cfg = self.config_mysql
        self.lateral.estado(True, "Conectado", f"{cfg.usuario}@{cfg.host}:{cfg.puerto} · {cfg.base_datos}")
        for pantalla in self.pantallas.values():
            pantalla.destroy()
        self.pantallas.clear()
        self.actual = None
        self.mostrar("panel")

    # ---------------------------------------------------------------- navegación
    def mostrar(self, clave: str) -> None:
        """Muestra la pantalla del módulo con una transición y la actualiza con datos de la base."""
        if clave == self.actual:
            return
        if self.actual and self.actual in self.pantallas:
            self.pantallas[self.actual].place_forget()
        if clave not in self.pantallas:
            clase = next(m[2] for m in MODULOS if m[0] == clave)
            self.pantallas[clave] = clase(self.contenido, self.bd)
        pantalla = self.pantallas[clave]
        self.actual = clave
        self.lateral.activar(clave)
        margen = 28

        def paso(t):
            desplazamiento = round(36 * (1 - t))
            pantalla.place(x=margen + desplazamiento, y=margen, relwidth=1, relheight=1,
                           width=-2 * margen, height=-2 * margen)
        paso(0)
        self.update_idletasks()
        pantalla.actualizar()
        Animacion(self.contenido, 240, paso, clave="transicion")

    def abrir_conexion(self) -> None:
        """Abre el diálogo para configurar la conexión con MySQL."""
        def al_conectar(config: ConfiguracionMySQL):
            self.bd.cerrar()
            self.config_mysql = config
            self.bd = BaseDatos(config)
            self._conectado()
            c.Notificacion(self, f"Conectado a {config.base_datos} en {config.host}.", "exito", "Conexión establecida")
        DialogoConexion(self, self.config_mysql, al_conectar)

    def salir(self) -> None:
        """Cierra la conexión y la ventana."""
        self.bd.cerrar()
        self.destroy()
