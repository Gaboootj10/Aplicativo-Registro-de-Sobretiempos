"""Tema visual del aplicativo: paleta, tipografías, íconos y estilos ttk."""
from tkinter import ttk

# ------------------------------------------------------------------- paleta
FONDO = "#F1F5F9"          # fondo general (slate-100)
BLANCO = "#FFFFFF"
SUPERFICIE = "#F8FAFC"     # filas alternas, campos deshabilitados
BORDE = "#E2E8F0"
BORDE_FUERTE = "#CBD5E1"
SOMBRA = "#DCE3EC"
TEXTO = "#0F172A"
TEXTO_2 = "#475569"
GRIS = "#64748B"
GRIS_CLARO = "#94A3B8"

LATERAL = "#0F172A"        # barra lateral (degradado de LATERAL a LATERAL_2)
LATERAL_2 = "#1E293B"
LATERAL_HOVER = "#273449"

PRIMARIO = "#059669"       # verde esmeralda
PRIMARIO_HOVER = "#047857"
PRIMARIO_SUAVE = "#ECFDF5"
PRIMARIO_CLARO = "#34D399"
PRIMARIO_TENUE = "#D1FAE5"
CIAN = "#0EA5E9"
CIAN_SUAVE = "#E0F2FE"
VERDE = "#10B981"
VERDE_HOVER = "#059669"
VERDE_SUAVE = "#D1FAE5"
AMBAR = "#F59E0B"
AMBAR_HOVER = "#D97706"
AMBAR_SUAVE = "#FEF3C7"
ROJO = "#EF4444"
ROJO_HOVER = "#DC2626"
ROJO_SUAVE = "#FEE2E2"
VIOLETA = "#8B5CF6"
VIOLETA_SUAVE = "#EDE9FE"
ROSA = "#EC4899"
ROSA_SUAVE = "#FCE7F3"

# Compatibilidad con nombres anteriores
AZUL = PRIMARIO
AZUL_CLARO = PRIMARIO_HOVER
NARANJA = AMBAR

# -------------------------------------------------------------- tipografías
FAMILIA = "Segoe UI"
FAMILIA_SEMI = "Segoe UI Semibold"
ICONOS = "Segoe MDL2 Assets"

FUENTE = (FAMILIA, 10)
FUENTE_PEQUENA = (FAMILIA, 9)
FUENTE_NEGRITA = (FAMILIA_SEMI, 10)
FUENTE_TITULO = (FAMILIA_SEMI, 20)
FUENTE_SUBTITULO = (FAMILIA_SEMI, 12)
FUENTE_NUMERO = (FAMILIA_SEMI, 24)
FUENTE_MENU = (FAMILIA, 10)

# ------------------------------------------------------- íconos (MDL2 Assets)
ICONO = {
    "panel": "", "empleados": "", "asistencias": "", "sobretiempos": "",
    "sap": "", "reportes": "", "importar": "", "maestros": "",
    "respaldo": "", "conexion": "", "buscar": "", "agregar": "",
    "editar": "", "eliminar": "", "excel": "", "exportar": "",
    "recargar": "", "ok": "", "error": "", "info": "", "alerta": "",
    "reloj": "", "dinero": "", "calendario": "", "usuario": "",
    "archivo": "", "carpeta": "", "restaurar": "", "guardar": "",
    "cerrar": "", "limpiar": "", "generar": "", "base": "",
}


def aplicar_estilos(raiz) -> None:
    """Configura el tema ttk (sobre 'clam') con la paleta del aplicativo."""
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(bg=FONDO)
    raiz.option_add("*TCombobox*Listbox.font", FUENTE)
    raiz.option_add("*TCombobox*Listbox.selectBackground", PRIMARIO)
    raiz.option_add("*TCombobox*Listbox.selectForeground", BLANCO)

    estilo.configure(".", font=FUENTE, background=FONDO, foreground=TEXTO, bordercolor=BORDE,
                     focuscolor=PRIMARIO)
    estilo.configure("TFrame", background=FONDO)
    estilo.configure("Blanco.TFrame", background=BLANCO)
    estilo.configure("TLabel", background=FONDO, foreground=TEXTO)
    estilo.configure("Blanco.TLabel", background=BLANCO)
    estilo.configure("Titulo.TLabel", font=FUENTE_TITULO, foreground=TEXTO)
    estilo.configure("Subtitulo.TLabel", font=FUENTE_SUBTITULO, foreground=TEXTO)
    estilo.configure("Ayuda.TLabel", foreground=GRIS)
    estilo.configure("AyudaBlanco.TLabel", foreground=GRIS, background=BLANCO)
    estilo.configure("Campo.TLabel", foreground=TEXTO_2, background=BLANCO, font=FUENTE_NEGRITA)

    # Campos de texto y listas desplegables
    for nombre in ("TEntry", "TCombobox"):
        estilo.configure(nombre, fieldbackground=BLANCO, background=BLANCO, bordercolor=BORDE_FUERTE,
                         lightcolor=BORDE_FUERTE, darkcolor=BORDE_FUERTE, padding=(8, 6), arrowcolor=GRIS,
                         insertcolor=TEXTO)
        estilo.map(nombre, bordercolor=[("focus", PRIMARIO)], lightcolor=[("focus", PRIMARIO)],
                   darkcolor=[("focus", PRIMARIO)], fieldbackground=[("readonly", BLANCO), ("disabled", SUPERFICIE)],
                   foreground=[("disabled", GRIS)])
    estilo.map("TCombobox", fieldbackground=[("readonly", BLANCO), ("disabled", SUPERFICIE)],
               selectbackground=[("readonly", BLANCO)], selectforeground=[("readonly", TEXTO)])

    # Tablas
    estilo.configure("Treeview", rowheight=32, background=BLANCO, fieldbackground=BLANCO, foreground=TEXTO,
                     bordercolor=BLANCO, lightcolor=BLANCO, darkcolor=BLANCO, borderwidth=0, font=FUENTE)
    estilo.configure("Treeview.Heading", font=FUENTE_NEGRITA, background=SUPERFICIE, foreground=TEXTO_2,
                     relief="flat", padding=(8, 8), bordercolor=BORDE, lightcolor=SUPERFICIE, darkcolor=BORDE)
    estilo.map("Treeview.Heading", background=[("active", PRIMARIO_SUAVE)], foreground=[("active", PRIMARIO)])
    estilo.map("Treeview", background=[("selected", PRIMARIO_SUAVE)], foreground=[("selected", PRIMARIO)])
    estilo.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # Barras de desplazamiento delgadas
    for orient in ("Vertical", "Horizontal"):
        estilo.configure(f"{orient}.TScrollbar", background=BORDE, troughcolor=BLANCO, bordercolor=BLANCO,
                         lightcolor=BORDE, darkcolor=BORDE, arrowcolor=GRIS, gripcount=0, arrowsize=12)
        estilo.map(f"{orient}.TScrollbar", background=[("active", BORDE_FUERTE)])

    # Pestañas
    estilo.configure("TNotebook", background=FONDO, borderwidth=0, tabmargins=(0, 0, 0, 0))
    estilo.configure("TNotebook.Tab", padding=(18, 9), font=FUENTE_NEGRITA, background=FONDO,
                     foreground=GRIS, borderwidth=0, lightcolor=FONDO, bordercolor=FONDO)
    estilo.map("TNotebook.Tab", background=[("selected", BLANCO), ("active", PRIMARIO_SUAVE)],
               foreground=[("selected", PRIMARIO), ("active", PRIMARIO)],
               lightcolor=[("selected", PRIMARIO)])

    estilo.configure("TButton", padding=(12, 6), background=BLANCO, bordercolor=BORDE_FUERTE)
    estilo.configure("Horizontal.TProgressbar", troughcolor=BORDE, background=PRIMARIO, bordercolor=BORDE,
                     lightcolor=PRIMARIO, darkcolor=PRIMARIO, thickness=6)
