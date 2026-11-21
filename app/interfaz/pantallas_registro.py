"""Pantallas de registro: maestros, empleados, asistencias y sobretiempos.

Todas usan PantallaCrud; cada acción llama a un procedimiento almacenado:
``sp_<tabla>_listar``, ``sp_<tabla>_insertar``, ``sp_<tabla>_actualizar`` y
``sp_<tabla>_eliminar``.
"""
from __future__ import annotations

import calendar
import datetime as dt
import tkinter as tk
from tkinter import ttk

from datos.conexion import BaseDatos
from interfaz import componentes as c
from interfaz import estilos as e
from interfaz.componentes import Campo
from interfaz.pantalla_crud import PantallaCrud
from logica import validaciones as v


# --------------------------------------------------------------- opciones combo
def opciones_centros(bd: BaseDatos) -> list:
    """Opciones (código, 'código - nombre') de los centros de coste."""
    return [(f[0], f"{f[0]} - {f[1]}") for f in bd.llamar("sp_centro_coste_listar", "").filas]


def opciones_areas(bd: BaseDatos) -> list:
    """Opciones de las áreas (unidades organizativas)."""
    return [(f[0], f"{f[0]} - {f[1]}") for f in bd.llamar("sp_area_listar", "").filas]


def opciones_turnos(bd: BaseDatos) -> list:
    """Opciones de los turnos programados con su horario."""
    return [(f[0], f"{f[0]}  ({f[3]} {f[1]}-{f[2]})") for f in bd.llamar("sp_turno_listar").filas]


def opciones_empleados(bd: BaseDatos) -> list:
    """Opciones de los empleados (código - nombres)."""
    return [(f[0], f"{f[0]} - {f[2]}") for f in bd.llamar("sp_empleado_listar", "").filas]


def opciones_periodos(bd: BaseDatos) -> list[str]:
    """Códigos de los periodos registrados (más reciente primero)."""
    return [f[0] for f in bd.llamar("sp_periodo_listar").filas]


# ---------------------------------------------------------------------- maestros
class PantallaMaestros(tk.Frame):
    """Pestañas para centros de coste, áreas, turnos y periodos."""

    def __init__(self, padre, bd: BaseDatos):
        super().__init__(padre, bg=e.FONDO)
        self.bd = bd
        c.encabezado(self, "Datos maestros",
                     "Tablas de referencia que usan los empleados, las asistencias y la consolidación SAP.",
                     e.ICONO["maestros"], e.VIOLETA, e.VIOLETA_SUAVE).pack(fill="x", pady=(0, 16))
        cuaderno = ttk.Notebook(self)
        cuaderno.pack(fill="both", expand=True)
        self.pestanas = [self._centros(cuaderno), self._areas(cuaderno), self._turnos(cuaderno),
                         self._periodos(cuaderno)]
        for pestana, texto in zip(self.pestanas, ("Centros de coste", "Áreas", "Turnos", "Periodos")):
            cuaderno.add(pestana, text=texto, padding=(0, 14, 0, 0))
        cuaderno.bind("<<NotebookTabChanged>>", lambda _e: self.actualizar())
        self.cuaderno = cuaderno

    def actualizar(self) -> None:
        """Recarga la pestaña visible."""
        indice = self.cuaderno.index(self.cuaderno.select())
        self.pestanas[indice].actualizar_datos()

    def _centros(self, padre) -> PantallaCrud:
        bd = self.bd
        return PantallaCrud(
            padre, titulo="Centros de coste", descripcion="", mostrar_encabezado=False,
            listar=lambda t, d, h: bd.llamar("sp_centro_coste_listar", t),
            campos=lambda modo: [
                Campo("codigo", "Código", solo_lectura=modo == "editar", ayuda="8 caracteres"),
                Campo("nombre", "Centro de coste")],
            valores_fila=lambda f: {"codigo": f["Código"], "nombre": f["Centro de coste"]},
            insertar=lambda d: bd.llamar("sp_centro_coste_insertar", v.longitud(d["codigo"], 8, "código"),
                                         v.obligatorio(d["nombre"], "el nombre")),
            actualizar=lambda d: bd.llamar("sp_centro_coste_actualizar", d["codigo"],
                                           v.obligatorio(d["nombre"], "el nombre")),
            eliminar=lambda f: bd.llamar("sp_centro_coste_eliminar", f["Código"]),
            descripcion_fila=lambda f: f"el centro de coste {f['Código']} - {f['Centro de coste']}")

    def _areas(self, padre) -> PantallaCrud:
        bd = self.bd
        return PantallaCrud(
            padre, titulo="Áreas", descripcion="", mostrar_encabezado=False,
            listar=lambda t, d, h: bd.llamar("sp_area_listar", t),
            campos=lambda modo: [
                Campo("codigo", "Código", solo_lectura=True, ayuda="Se genera automáticamente"),
                Campo("nombre", "Unidad organizativa")],
            valores_nuevo=lambda: {"codigo": bd.llamar("sp_area_siguiente_codigo").filas[0][0]},
            valores_fila=lambda f: {"codigo": f["Código"], "nombre": f["Unidad organizativa"]},
            insertar=lambda d: bd.llamar("sp_area_insertar", d["codigo"], v.obligatorio(d["nombre"], "el nombre")),
            actualizar=lambda d: bd.llamar("sp_area_actualizar", d["codigo"],
                                           v.obligatorio(d["nombre"], "el nombre")),
            eliminar=lambda f: bd.llamar("sp_area_eliminar", f["Código"]),
            descripcion_fila=lambda f: f"el área {f['Código']} - {f['Unidad organizativa']}")

    def _turnos(self, padre) -> PantallaCrud:
        bd = self.bd
        return PantallaCrud(
            padre, titulo="Turnos", descripcion="", mostrar_encabezado=False,
            listar=lambda t, d, h: bd.llamar("sp_turno_listar"),
            campos=lambda modo: [
                Campo("codigo", "Código", solo_lectura=modo == "editar", ayuda="3 caracteres, p. ej. A10"),
                Campo("entrada", "Hora de entrada", "hora", ayuda="HH:MM"),
                Campo("salida", "Hora de salida", "hora", ayuda="HH:MM (si es menor, es nocturno)")],
            valores_fila=lambda f: {"codigo": f["Código"], "entrada": f["Entrada"], "salida": f["Salida"]},
            insertar=lambda d: bd.llamar("sp_turno_insertar", v.longitud(d["codigo"], 3, "código del turno"),
                                         d["entrada"], d["salida"]),
            actualizar=lambda d: bd.llamar("sp_turno_actualizar", d["codigo"], d["entrada"], d["salida"]),
            eliminar=lambda f: bd.llamar("sp_turno_eliminar", f["Código"]),
            descripcion_fila=lambda f: f"el turno {f['Código']}")

    def _periodos(self, padre) -> PantallaCrud:
        bd = self.bd

        def nuevo_periodo() -> dict:
            hoy = dt.date.today()
            ultimo = calendar.monthrange(hoy.year, hoy.month)[1]
            return {"codigo": f"{hoy:%Y%m}", "inicio": hoy.replace(day=1), "fin": hoy.replace(day=ultimo)}

        return PantallaCrud(
            padre, titulo="Periodos", descripcion="", mostrar_encabezado=False,
            listar=lambda t, d, h: bd.llamar("sp_periodo_listar"),
            campos=lambda modo: [
                Campo("codigo", "Código", solo_lectura=modo == "editar", ayuda="AAAAMM"),
                Campo("inicio", "Fecha de inicio", "fecha", ayuda="DD/MM/AAAA"),
                Campo("fin", "Fecha de fin", "fecha", ayuda="DD/MM/AAAA")],
            valores_nuevo=nuevo_periodo,
            valores_fila=lambda f: {"codigo": f["Código"], "inicio": f["Inicio"], "fin": f["Fin"]},
            insertar=lambda d: bd.llamar("sp_periodo_insertar", v.digitos(d["codigo"], 6, "código del periodo"),
                                         d["inicio"], d["fin"]),
            actualizar=lambda d: bd.llamar("sp_periodo_actualizar", d["codigo"], d["inicio"], d["fin"]),
            eliminar=lambda f: bd.llamar("sp_periodo_eliminar", f["Código"]),
            descripcion_fila=lambda f: f"el periodo {f['Código']}")


# --------------------------------------------------------------------- empleados
class PantallaEmpleados(PantallaCrud):
    """Mantenimiento de empleados (sp_empleado_*)."""

    def __init__(self, padre, bd: BaseDatos):
        self.bd = bd
        super().__init__(
            padre, titulo="Empleados",
            descripcion="Registro de trabajadores. El código se genera automáticamente y el nombre se "
                        "guarda en mayúsculas (disparador trg_empleado_bi).",
            icono=e.ICONO["empleados"], color=e.CIAN, color_suave=e.CIAN_SUAVE,
            texto_busqueda="Código, DNI o nombre",
            listar=lambda t, d, h: bd.llamar("sp_empleado_listar", t),
            campos=self._campos_empleado,
            valores_nuevo=lambda: {"codigo": bd.llamar("sp_empleado_siguiente_codigo").filas[0][0],
                                   "subdivision": "Arequipa"},
            valores_fila=lambda f: {"codigo": f["Código"], "dni": f["DNI"], "nombres": f["Nombres"],
                                    "puesto": f["Puesto"], "subdivision": f["Subdivisión"],
                                    "centro": f["Cód. centro"], "area": f["Cód. área"]},
            insertar=lambda d: self._guardar("sp_empleado_insertar", d),
            actualizar=lambda d: self._guardar("sp_empleado_actualizar", d),
            eliminar=lambda f: bd.llamar("sp_empleado_eliminar", f["Código"]),
            descripcion_fila=lambda f: f"al empleado {f['Código']} - {f['Nombres']}",
            ocultar=("Cód. área", "Cód. centro"))

    def actualizar(self) -> None:
        """Recarga la lista al mostrar la pantalla."""
        self.actualizar_datos()

    def _campos_empleado(self, modo: str) -> list[Campo]:
        return [
            Campo("codigo", "Código", solo_lectura=True, ayuda="6 dígitos"),
            Campo("dni", "DNI", ayuda="8 dígitos"),
            Campo("nombres", "Apellidos y nombres", ayuda="APELLIDOS, NOMBRES"),
            Campo("puesto", "Puesto"),
            Campo("subdivision", "Subdivisión", ayuda="Local, p. ej. Arequipa"),
            Campo("centro", "Centro de coste", "combo", opciones_centros(self.bd)),
            Campo("area", "Unidad organizativa", "combo", opciones_areas(self.bd)),
        ]

    def _guardar(self, procedimiento: str, d: dict) -> None:
        self.bd.llamar(procedimiento, v.digitos(d["codigo"], 6, "código del empleado"),
                       v.digitos(d["dni"], 8, "DNI"), v.obligatorio(d["nombres"], "los nombres"),
                       v.obligatorio(d["puesto"], "el puesto"), v.obligatorio(d["subdivision"], "la subdivisión"),
                       v.obligatorio(d["centro"], "el centro de coste"), v.obligatorio(d["area"], "el área"))


# ------------------------------------------------------------------- asistencias
class PantallaAsistencias(PantallaCrud):
    """Registro de asistencias (sp_asistencia_*). El sobretiempo lo calculan los disparadores."""

    def __init__(self, padre, bd: BaseDatos):
        self.bd = bd
        super().__init__(
            padre, titulo="Asistencias",
            descripcion="Marcaciones diarias. Al guardar, los disparadores calculan y clasifican el "
                        "sobretiempo en H25, H35 y H100. Las filas en rojo requieren revisión.",
            icono=e.ICONO["asistencias"], color=e.VERDE, color_suave=e.VERDE_SUAVE,
            fechas=True, texto_busqueda="Código o nombre",
            listar=lambda t, d, h: bd.llamar("sp_asistencia_listar", t, d, h),
            campos=self._campos_asistencia,
            valores_nuevo=lambda: {"fecha": dt.date.today(), "turno": "A10"},
            valores_fila=lambda f: {"empleado": f["Código"], "fecha": f["Fecha"], "turno": f["Turno"],
                                    "entrada": f["Entrada"], "salida": f["Salida"],
                                    "centro": f["C. coste provisional"]},
            insertar=lambda d: self._guardar("sp_asistencia_insertar", d),
            actualizar=lambda d: self._guardar("sp_asistencia_actualizar", d),
            eliminar=lambda f: bd.llamar("sp_asistencia_eliminar", f["Código"], f["Fecha"]),
            descripcion_fila=lambda f: f"la asistencia de {f['Nombres']} del {v.mostrar(f['Fecha'])}",
            alerta=lambda f: f["Estado"] in ("Incompleta", "Sin marcaciones"))

    def actualizar(self) -> None:
        """Recarga la lista al mostrar la pantalla."""
        self.actualizar_datos()

    def _campos_asistencia(self, modo: str) -> list[Campo]:
        editar = modo == "editar"
        return [
            Campo("empleado", "Empleado", "combo", opciones_empleados(self.bd), solo_lectura=editar),
            Campo("fecha", "Fecha", "fecha", solo_lectura=editar, ayuda="DD/MM/AAAA (inicio del turno)"),
            Campo("turno", "Turno", "combo", opciones_turnos(self.bd)),
            Campo("entrada", "Marca de entrada", "hora", ayuda="HH:MM, vacío si no marcó"),
            Campo("salida", "Marca de salida", "hora", ayuda="HH:MM, vacío si no marcó"),
            Campo("centro", "C. coste provisional", ayuda="Opcional, 8 caracteres"),
        ]

    def _guardar(self, procedimiento: str, d: dict) -> None:
        self.bd.llamar(procedimiento, v.obligatorio(d["empleado"], "el empleado"),
                       d["fecha"] or v.fecha("", "fecha"), v.obligatorio(d["turno"], "el turno"),
                       d["entrada"], d["salida"], d["centro"].upper())


# ------------------------------------------------------------------ sobretiempos
class PantallaSobretiempos(PantallaCrud):
    """Consulta del sobretiempo calculado (solo lectura) y recálculo de un periodo."""

    def __init__(self, padre, bd: BaseDatos):
        self.bd = bd
        super().__init__(
            padre, titulo="Sobretiempos",
            descripcion="Horas extra generadas automáticamente por los disparadores a partir de las "
                        "asistencias. No se digitan: se corrigen modificando la asistencia.",
            icono=e.ICONO["sobretiempos"], color=e.AMBAR_HOVER, color_suave=e.AMBAR_SUAVE,
            fechas=True, texto_busqueda="Código o nombre",
            listar=lambda t, d, h: bd.llamar("sp_sobretiempo_listar", t, d, h),
            campos=lambda modo: [])
        self.periodo = tk.StringVar()
        tk.Label(self.barra, text="Periodo", font=e.FUENTE_NEGRITA, bg=e.FONDO, fg=e.TEXTO_2).pack(side="left")
        self.combo = ttk.Combobox(self.barra, textvariable=self.periodo, width=10, state="readonly",
                                  font=e.FUENTE)
        self.combo.pack(side="left", padx=8)
        c.Boton(self.barra, "Recalcular periodo", self.recalcular, "aviso", e.ICONO["recargar"]).pack(side="left")

    def actualizar(self) -> None:
        """Recarga la lista y los periodos."""
        if c.ejecutar_seguro(self, lambda: self.combo.configure(values=opciones_periodos(self.bd))):
            if not self.periodo.get() and self.combo["values"]:
                self.periodo.set(self.combo["values"][0])
        self.actualizar_datos()

    def recalcular(self) -> None:
        """Llama a sp_recalcular_periodo para volver a aplicar las reglas a todo el periodo."""
        if not self.periodo.get():
            c.mostrar_info(self, "Seleccione un periodo.", "Recalcular")
            return
        if c.ejecutar_seguro(self, self.bd.llamar, "sp_recalcular_periodo", self.periodo.get(),
                             exito=f"Se recalculó el sobretiempo del periodo {self.periodo.get()}."):
            self.actualizar_datos()
