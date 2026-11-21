"""Pantallas de procesos: panel de control, consolidación SAP y reportes."""
from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import ttk

from datos.conexion import BaseDatos
from interfaz import componentes as c
from interfaz import estilos as e
from interfaz.animacion import Animacion, contar, mezclar
from interfaz.pantallas_registro import opciones_empleados, opciones_periodos
from logica import validaciones as v
from logica.reportes import REPORTES

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def fecha_larga(fecha: dt.date) -> str:
    """'sábado, 21 de noviembre de 2026'."""
    return f"{DIAS[fecha.weekday()]}, {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


# ---------------------------------------------------------------- panel de control
class PantallaPanel(tk.Frame):
    """Indicadores animados, gráfico de barras por recargo y ranking de empleados."""

    INDICADORES = [
        ("empleados", "Empleados registrados", "empleados", e.PRIMARIO, e.PRIMARIO_SUAVE, 0),
        ("asistencias", "Asistencias registradas", "asistencias", e.CIAN, e.CIAN_SUAVE, 0),
        ("horas_extra", "Horas extra calculadas", "reloj", e.VIOLETA, e.VIOLETA_SUAVE, 2),
        ("empleados_con_extra", "Empleados con sobretiempo", "usuario", e.ROSA, e.ROSA_SUAVE, 0),
        ("incompletas", "Marcaciones por revisar", "alerta", e.AMBAR_HOVER, e.AMBAR_SUAVE, 0),
        ("pendientes_sap", "Consolidados SAP pendientes", "sap", e.ROJO, e.ROJO_SUAVE, 0),
    ]
    COLORES_BARRAS = [(e.PRIMARIO, e.PRIMARIO_CLARO), (e.AMBAR, "#FCD34D"), (e.ROJO, "#FCA5A5")]

    def __init__(self, padre, bd: BaseDatos):
        super().__init__(padre, bg=e.FONDO)
        self.bd = bd
        cabecera = tk.Frame(self, bg=e.FONDO)
        cabecera.pack(fill="x", pady=(0, 18))
        self.saludo = tk.Label(cabecera, font=e.FUENTE_TITULO, bg=e.FONDO, fg=e.TEXTO, anchor="w")
        self.saludo.pack(anchor="w")
        tk.Label(cabecera, text="Este es el resumen del registro de sobretiempos.", font=e.FUENTE, bg=e.FONDO,
                 fg=e.GRIS).pack(anchor="w")
        self.fecha = tk.Label(cabecera, font=e.FUENTE_NEGRITA, bg=e.BLANCO, fg=e.TEXTO_2, padx=14, pady=6)
        self.fecha.place(relx=1.0, rely=0.5, anchor="e")

        tarjetas = tk.Frame(self, bg=e.FONDO)
        tarjetas.pack(fill="x")
        self.numeros: dict[str, tuple[tk.Label, int]] = {}
        for i, (clave, texto, icono, color, suave, decimales) in enumerate(self.INDICADORES):
            tarjeta = c.Tarjeta(tarjetas, relleno=18, alto=118)
            tarjeta.grid(row=i // 3, column=i % 3, sticky="nsew", padx=(0 if i % 3 == 0 else 8, 0),
                         pady=(0, 10))
            tarjetas.columnconfigure(i % 3, weight=1, uniform="tarjeta")
            c.Insignia(tarjeta.cuerpo, e.ICONO[icono], color, suave, 52).pack(side="left")
            textos = tk.Frame(tarjeta.cuerpo, bg=e.BLANCO)
            textos.pack(side="left", padx=16)
            numero = tk.Label(textos, text="0", font=e.FUENTE_NUMERO, bg=e.BLANCO, fg=e.TEXTO, anchor="w")
            numero.pack(anchor="w")
            tk.Label(textos, text=texto, font=e.FUENTE, bg=e.BLANCO, fg=e.GRIS).pack(anchor="w")
            self.numeros[clave] = (numero, decimales)

        inferior = tk.Frame(self, bg=e.FONDO)
        inferior.pack(fill="both", expand=True, pady=(8, 0))
        inferior.columnconfigure(0, weight=5, uniform="inf")
        inferior.columnconfigure(1, weight=6, uniform="inf")
        inferior.rowconfigure(0, weight=1)
        izquierda = c.Tarjeta(inferior, relleno=20, expandir=True)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(izquierda.cuerpo, text="Horas extra por tipo de recargo", font=e.FUENTE_SUBTITULO, bg=e.BLANCO,
                 fg=e.TEXTO).pack(anchor="w")
        tk.Label(izquierda.cuerpo, text="Total acumulado por código CC Nómina", font=e.FUENTE_PEQUENA,
                 bg=e.BLANCO, fg=e.GRIS).pack(anchor="w")
        self.grafico = tk.Canvas(izquierda.cuerpo, bg=e.BLANCO, highlightthickness=0, height=240)
        self.grafico.pack(fill="both", expand=True, pady=(10, 0))
        self.grafico.bind("<Configure>", lambda _e: self._dibujar_barras(1.0))

        derecha = c.Tarjeta(inferior, relleno=20, expandir=True)
        derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(derecha.cuerpo, text="Empleados con más horas extra", font=e.FUENTE_SUBTITULO, bg=e.BLANCO,
                 fg=e.TEXTO).pack(anchor="w")
        tk.Label(derecha.cuerpo, text="Top 5 de todo el registro", font=e.FUENTE_PEQUENA, bg=e.BLANCO,
                 fg=e.GRIS).pack(anchor="w")
        self.ranking = tk.Canvas(derecha.cuerpo, bg=e.BLANCO, highlightthickness=0, height=300)
        self.ranking.pack(fill="both", expand=True, pady=(10, 0))
        self.ranking.bind("<Configure>", lambda _e: self._dibujar_ranking(1.0))
        self.por_tipo: list[tuple] = []
        self.top: list[tuple] = []

    def actualizar(self) -> None:
        """Consulta sp_dashboard, sp_dashboard_top y sp_reporte_resumen_tipo y anima los resultados."""
        hora = dt.datetime.now().hour
        self.saludo.configure(text="Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches")
        self.fecha.configure(text=fecha_larga(dt.date.today()).capitalize(), font=e.FUENTE_NEGRITA)

        def consultar():
            datos = self.bd.llamar("sp_dashboard").primero() or {}
            for clave, (etiqueta, decimales) in self.numeros.items():
                contar(etiqueta, float(datos.get(clave) or 0), decimales)
            self.top = self.bd.llamar("sp_dashboard_top").filas
            self.por_tipo = self.bd.llamar("sp_reporte_resumen_tipo", None, None, None).filas
            Animacion(self.grafico, 800, self._dibujar_barras, clave="barras")
            Animacion(self.ranking, 900, self._dibujar_ranking, clave="ranking")
        c.ejecutar_seguro(self, consultar)

    def _dibujar_barras(self, t: float) -> None:
        """Gráfico de barras redondeadas que crecen con la animación (t de 0 a 1)."""
        lienzo = self.grafico
        lienzo.delete("all")
        ancho, alto = lienzo.winfo_width(), lienzo.winfo_height()
        if not self.por_tipo or ancho < 50:
            return
        maximo = max(float(f[3]) for f in self.por_tipo) or 1
        base, techo = alto - 36, 26
        for k in range(5):  # líneas guía
            y = base - (base - techo) * k / 4
            lienzo.create_line(40, y, ancho - 10, y, fill=e.BORDE, dash=(2, 4) if k else ())
            lienzo.create_text(32, y, text=f"{maximo * k / 4:.0f}", anchor="e", font=e.FUENTE_PEQUENA, fill=e.GRIS_CLARO)
        n = len(self.por_tipo)
        hueco = (ancho - 60) / n
        barra = min(hueco * 0.5, 70)
        for i, fila in enumerate(self.por_tipo):
            horas = float(fila[3])
            x0 = 50 + hueco * i + (hueco - barra) / 2
            y0 = base - (base - techo) * (horas / maximo) * t
            color, claro = self.COLORES_BARRAS[i % 3]
            if base - y0 > 2:
                c.redondeado(lienzo, x0, y0, x0 + barra, base, 8, fill=mezclar(claro, color, t), outline="")
            lienzo.create_text(x0 + barra / 2, y0 - 12, text=f"{horas * t:.2f} h", font=e.FUENTE_NEGRITA, fill=e.TEXTO)
            lienzo.create_text(x0 + barra / 2, base + 13, text=fila[0], font=e.FUENTE_NEGRITA, fill=e.TEXTO_2)
            lienzo.create_text(x0 + barra / 2, base + 28, text=f"recargo {fila[1]}", font=e.FUENTE_PEQUENA,
                               fill=e.GRIS)

    def _dibujar_ranking(self, t: float) -> None:
        """Barras horizontales de progreso con los empleados que más horas extra tienen."""
        lienzo = self.ranking
        lienzo.delete("all")
        ancho = lienzo.winfo_width()
        if not self.top or ancho < 50:
            return
        maximo = max(float(f[3]) for f in self.top) or 1
        colores = [e.PRIMARIO, e.CIAN, e.VIOLETA, e.AMBAR, e.ROSA]
        for i, (_codigo, nombre, unidad, horas) in enumerate(self.top):
            y = 6 + i * 60
            c.redondeado(lienzo, 0, y, 30, y + 30, 9, fill=e.SUPERFICIE, outline="")
            lienzo.create_text(15, y + 15, text=str(i + 1), font=e.FUENTE_NEGRITA, fill=colores[i])
            lienzo.create_text(42, y + 6, text=nombre.title(), anchor="w", font=e.FUENTE_NEGRITA, fill=e.TEXTO)
            lienzo.create_text(ancho - 4, y + 6, text=f"{float(horas) * t:.2f} h", anchor="e", font=e.FUENTE_NEGRITA,
                               fill=colores[i])
            largo = ancho - 46
            c.redondeado(lienzo, 42, y + 20, 42 + largo, y + 28, 4, fill=e.BORDE, outline="")
            relleno = largo * float(horas) / maximo * t
            if relleno > 8:
                c.redondeado(lienzo, 42, y + 20, 42 + relleno, y + 28, 4, fill=colores[i], outline="")
            lienzo.create_text(42, y + 38, text=unidad, anchor="w", font=e.FUENTE_PEQUENA, fill=e.GRIS)


# ------------------------------------------------------------- consolidación SAP
class PantallaSap(tk.Frame):
    """Consolidación de un periodo para SAP (PA70), conciliación e historial."""

    def __init__(self, padre, bd: BaseDatos):
        super().__init__(padre, bg=e.FONDO)
        self.bd = bd
        c.encabezado(self, "Consolidación para SAP",
                     "Suma el sobretiempo de cada empleado por código CC Nómina y periodo (sp_consolidar_periodo). "
                     "La carga en SAP mediante la transacción PA70 sigue siendo manual.",
                     e.ICONO["sap"], e.ROJO, e.ROJO_SUAVE).pack(fill="x", pady=(0, 16))
        barra = tk.Frame(self, bg=e.FONDO)
        barra.pack(fill="x", pady=(0, 12))
        self.periodo = tk.StringVar()
        self.fecha_carga = tk.StringVar(value=dt.date.today().strftime("%d/%m/%Y"))
        tk.Label(barra, text="Periodo", font=e.FUENTE_NEGRITA, bg=e.FONDO, fg=e.TEXTO_2).pack(side="left")
        self.combo = ttk.Combobox(barra, textvariable=self.periodo, width=10, state="readonly", font=e.FUENTE)
        self.combo.pack(side="left", padx=(8, 16))
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.actualizar_datos())
        tk.Label(barra, text="Fecha de carga", font=e.FUENTE_NEGRITA, bg=e.FONDO, fg=e.TEXTO_2).pack(side="left")
        c.Entrada(barra, self.fecha_carga, "DD/MM/AAAA", width=12).pack(side="left", padx=(8, 16))
        c.Boton(barra, "Consolidar periodo", self.consolidar, "primario", e.ICONO["generar"]).pack(side="left")
        c.Boton(barra, "Exportar para SAP", self.exportar, "secundario", e.ICONO["exportar"]).pack(side="right")

        resumen = tk.Frame(self, bg=e.FONDO)
        resumen.pack(fill="x", pady=(0, 12))
        self.chips = {}
        for clave, texto, color, suave in (("total", "Consolidados", e.PRIMARIO, e.PRIMARIO_SUAVE),
                                           ("ok", "Conciliados", e.VERDE_HOVER, e.VERDE_SUAVE),
                                           ("pend", "Pendientes o desactualizados", e.ROJO_HOVER, e.ROJO_SUAVE)):
            chip = tk.Label(resumen, text=f"0  {texto}", font=e.FUENTE_NEGRITA, bg=suave, fg=color, padx=14, pady=6)
            chip.pack(side="left", padx=(0, 8))
            self.chips[clave] = (chip, texto)

        cuaderno = ttk.Notebook(self)
        cuaderno.pack(fill="both", expand=True)
        self.cuaderno = cuaderno
        tarjetas = []
        for texto in ("Conciliación", "Historial de cambios"):
            marco = tk.Frame(cuaderno, bg=e.FONDO)
            cuaderno.add(marco, text=texto, padding=(0, 12, 0, 0))
            tarjeta = c.Tarjeta(marco, relleno=14, expandir=True)
            tarjeta.pack(fill="both", expand=True)
            tarjetas.append(tarjeta)
        self.tabla = c.Tabla(tarjetas[0].cuerpo)
        self.tabla.pack(fill="both", expand=True)
        self.tabla_historial = c.Tabla(tarjetas[1].cuerpo)
        self.tabla_historial.pack(fill="both", expand=True)

    def actualizar(self) -> None:
        """Recarga los periodos y la conciliación."""
        def cargar_periodos():
            periodos = opciones_periodos(self.bd)
            self.combo.configure(values=periodos)
            if periodos and self.periodo.get() not in periodos:
                self.periodo.set(periodos[0])
        c.ejecutar_seguro(self, cargar_periodos)
        self.actualizar_datos()

    def actualizar_datos(self) -> None:
        """Muestra la conciliación (v_conciliacion_sap) y el historial del periodo."""
        def consultar():
            resultado = self.bd.llamar("sp_registro_sap_listar", self.periodo.get())
            self.tabla.cargar(resultado, alerta=lambda f: f["Estado"] != "CONCILIADO")
            estados = [f["Estado"] for f in resultado.como_diccionarios()]
            pendientes = sum(1 for x in estados if x != "CONCILIADO")
            for clave, valor in (("total", len(estados)), ("ok", len(estados) - pendientes), ("pend", pendientes)):
                chip, texto = self.chips[clave]
                chip.configure(text=f"{valor}  {texto}")
            self.tabla_historial.cargar(self.bd.llamar("sp_historial_sap_listar", self.periodo.get()))
        c.ejecutar_seguro(self, consultar)

    def consolidar(self) -> None:
        """Ejecuta sp_consolidar_periodo (inserta, actualiza o anula los consolidados)."""
        if not self.periodo.get():
            c.Notificacion(self, "Seleccione un periodo.", "alerta", "Consolidar")
            return
        try:
            fecha = v.fecha(self.fecha_carga.get(), "fecha de carga")
        except v.ErrorValidacion as error:
            c.mostrar_error(self, error)
            return
        if c.ejecutar_seguro(self, self.bd.llamar, "sp_consolidar_periodo", self.periodo.get(), fecha,
                             exito=f"Periodo {self.periodo.get()} consolidado. Los cambios quedaron en el historial."):
            self.actualizar_datos()

    def exportar(self) -> None:
        """Exporta el consolidado del periodo para ingresarlo en SAP."""
        self.tabla.exportar(self, f"Consolidado SAP {self.periodo.get()}",
                            "Horas por empleado y CC Nómina para la transacción PA70")


# ---------------------------------------------------------------------- reportes
class ElementoLista(tk.Frame):
    """Fila seleccionable de la lista de reportes, con transición de color."""

    def __init__(self, padre, reporte, al_elegir):
        super().__init__(padre, bg=e.BLANCO, cursor="hand2", padx=10, pady=7)
        self.reporte, self.al_elegir, self.elegido = reporte, al_elegir, False
        self.numero = tk.Label(self, text=f"{reporte.numero:02d}", font=e.FUENTE_NEGRITA, width=3,
                               bg=e.SUPERFICIE, fg=e.GRIS)
        self.numero.pack(side="left")
        self.texto = tk.Label(self, text=reporte.titulo, font=e.FUENTE, bg=e.BLANCO, fg=e.TEXTO, anchor="w")
        self.texto.pack(side="left", fill="x", expand=True, padx=10)
        self.etiqueta = tk.Label(self, text="JOIN" if reporte.usa_join else "", font=(e.FAMILIA_SEMI, 8),
                                 bg=e.CIAN_SUAVE if reporte.usa_join else e.BLANCO, fg=e.CIAN, padx=5)
        self.etiqueta.pack(side="right")
        self._color = e.BLANCO
        for w in (self, self.numero, self.texto, self.etiqueta):
            w.bind("<Enter>", lambda _e: self._pintar(e.SUPERFICIE if not self.elegido else e.PRIMARIO_SUAVE))
            w.bind("<Leave>", lambda _e: self._pintar(e.PRIMARIO_SUAVE if self.elegido else e.BLANCO))
            w.bind("<Button-1>", lambda _e: self.al_elegir(self))

    def _pintar(self, destino: str) -> None:
        inicio = self._color

        def paso(t):
            self._color = mezclar(inicio, destino, t)
            for w in (self, self.texto):
                w.configure(bg=self._color)
            if not self.reporte.usa_join:
                self.etiqueta.configure(bg=self._color)
        Animacion(self, 120, paso, clave="color")

    def marcar(self, elegido: bool) -> None:
        self.elegido = elegido
        self.numero.configure(bg=e.PRIMARIO if elegido else e.SUPERFICIE, fg=e.BLANCO if elegido else e.GRIS)
        self.texto.configure(fg=e.PRIMARIO if elegido else e.TEXTO,
                             font=e.FUENTE_NEGRITA if elegido else e.FUENTE)
        self._pintar(e.PRIMARIO_SUAVE if elegido else e.BLANCO)


class PantallaReportes(tk.Frame):
    """Catálogo de los 14 reportes con filtros y exportación a Excel."""

    def __init__(self, padre, bd: BaseDatos):
        super().__init__(padre, bg=e.FONDO)
        self.bd = bd
        c.encabezado(self, "Reportes",
                     "14 reportes de la base de datos (11 con JOIN). Seleccione uno, ajuste los filtros y "
                     "presione Generar.", e.ICONO["reportes"], e.CIAN, e.CIAN_SUAVE).pack(fill="x", pady=(0, 16))
        cuerpo = tk.Frame(self, bg=e.FONDO)
        cuerpo.pack(fill="both", expand=True)

        lista = c.Tarjeta(cuerpo, relleno=10, expandir=True)
        lista.pack(side="left", fill="y", padx=(0, 12))
        lista.configure(width=360)
        tk.Label(lista.cuerpo, text="Reportes disponibles", font=e.FUENTE_SUBTITULO, bg=e.BLANCO, fg=e.TEXTO,
                 padx=8, pady=6).pack(anchor="w")
        self.elementos = [ElementoLista(lista.cuerpo, r, self._elegir) for r in REPORTES]
        for elemento in self.elementos:
            elemento.pack(fill="x")
        self.actual = self.elementos[0]

        derecha = c.Tarjeta(cuerpo, relleno=18, expandir=True)
        derecha.pack(side="left", fill="both", expand=True)
        zona = derecha.cuerpo
        self.titulo = tk.Label(zona, font=e.FUENTE_SUBTITULO, bg=e.BLANCO, fg=e.TEXTO, anchor="w")
        self.titulo.pack(fill="x")
        self.descripcion = tk.Label(zona, font=e.FUENTE, bg=e.BLANCO, fg=e.GRIS, anchor="w", justify="left",
                                    wraplength=760)
        self.descripcion.pack(fill="x", pady=(2, 12))
        filtros = tk.Frame(zona, bg=e.BLANCO)
        filtros.pack(fill="x", pady=(0, 12))
        self.desde, self.hasta, self.empleado = tk.StringVar(), tk.StringVar(), tk.StringVar()
        tk.Label(filtros, text=e.ICONO["calendario"], font=(e.ICONOS, 11), bg=e.BLANCO, fg=e.GRIS).pack(side="left")
        c.Entrada(filtros, self.desde, "Desde DD/MM/AAAA", width=17).pack(side="left", padx=(8, 6))
        c.Entrada(filtros, self.hasta, "Hasta DD/MM/AAAA", width=17).pack(side="left", padx=(0, 14))
        tk.Label(filtros, text=e.ICONO["usuario"], font=(e.ICONOS, 11), bg=e.BLANCO, fg=e.GRIS).pack(side="left")
        self.combo_empleado = ttk.Combobox(filtros, textvariable=self.empleado, width=32, state="readonly",
                                           font=e.FUENTE)
        self.combo_empleado.pack(side="left", padx=(8, 14))
        c.Boton(filtros, "Generar", self.generar, "primario", e.ICONO["generar"]).pack(side="left")
        c.Boton(filtros, "Excel", self.exportar, "secundario", e.ICONO["exportar"]).pack(side="right")
        self.contador = tk.Label(zona, font=e.FUENTE_NEGRITA, bg=e.PRIMARIO_SUAVE, fg=e.PRIMARIO, padx=10, pady=3)
        self.tabla = c.Tabla(zona)
        self.tabla.pack(fill="both", expand=True)
        self._elegir(self.elementos[0])

    def actualizar(self) -> None:
        """Carga la lista de empleados para el filtro."""
        def cargar():
            opciones = ["(Todos los empleados)"] + [texto for _valor, texto in opciones_empleados(self.bd)]
            self.combo_empleado.configure(values=opciones)
            if not self.empleado.get():
                self.empleado.set(opciones[0])
        c.ejecutar_seguro(self, cargar)

    def _elegir(self, elemento: ElementoLista) -> None:
        for otro in self.elementos:
            if otro.elegido and otro is not elemento:
                otro.marcar(False)
        elemento.marcar(True)
        self.actual = elemento
        r = elemento.reporte
        self.titulo.configure(text=f"Reporte {r.numero:02d} · {r.titulo}")
        self.descripcion.configure(text=f"{r.descripcion}  Procedimiento: {r.procedimiento}")

    def _reporte(self):
        return self.actual.reporte

    @property
    def listado(self):
        """Compatibilidad: permite elegir un reporte por índice (selection_set)."""
        pantalla = self

        class _Listado:
            def selection_clear(self, *_a):
                pass

            def selection_set(self, indice):
                pantalla._elegir(pantalla.elementos[indice])
        return _Listado()

    def _seleccionar(self) -> None:
        """Compatibilidad con versiones anteriores (la selección ya actualiza la descripción)."""

    def generar(self) -> None:
        """Llama al procedimiento del reporte con los filtros."""
        reporte = self._reporte()

        def consultar():
            desde = v.fecha(self.desde.get(), "fecha desde", obligatorio=False)
            hasta = v.fecha(self.hasta.get(), "fecha hasta", obligatorio=False)
            empleado = self.empleado.get().split(" - ")[0] if " - " in self.empleado.get() else ""
            resultado = self.bd.llamar(reporte.procedimiento, desde, hasta, empleado)
            self.tabla.cargar(resultado, alerta=lambda f: f.get("Resultado") == "REVISAR"
                              or f.get("Estado") not in (None, "CONCILIADO"))
            self.contador.configure(text=f"{len(resultado.filas)} fila(s)")
            self.contador.place(in_=self.titulo, relx=1.0, rely=0.5, anchor="e")
        c.ejecutar_seguro(self, consultar)

    def exportar(self) -> None:
        """Exporta el reporte generado a Excel."""
        reporte = self._reporte()
        filtros = f"Desde: {self.desde.get() or '-'}  Hasta: {self.hasta.get() or '-'}  Empleado: {self.empleado.get()}"
        self.tabla.exportar(self, f"Reporte {reporte.numero:02d} - {reporte.titulo}", filtros)
