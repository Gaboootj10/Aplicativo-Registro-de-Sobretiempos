"""Pantalla genérica de mantenimiento (CRUD): listar, nuevo, editar y eliminar.

Cada operación recibe una función que llama al procedimiento almacenado
correspondiente, por lo que la pantalla no conoce SQL.
"""
from __future__ import annotations

import tkinter as tk

from interfaz import componentes as c
from interfaz import estilos as e


class PantallaCrud(tk.Frame):
    """Lista de registros con botones Nuevo, Editar, Eliminar y Exportar."""

    def __init__(self, padre, *, titulo: str, descripcion: str, listar, campos, insertar=None,
                 actualizar=None, eliminar=None, valores_fila=None, valores_nuevo=None,
                 descripcion_fila=None, fechas: bool = False, texto_busqueda: str = "Buscar",
                 ocultar: tuple[str, ...] = (), alerta=None, mostrar_encabezado: bool = True,
                 icono: str = "", color: str = e.PRIMARIO, color_suave: str = e.PRIMARIO_SUAVE):
        super().__init__(padre, bg=c.fondo_de(padre))
        self.titulo = titulo
        self.icono = icono
        self._listar = listar
        self._campos = campos
        self._insertar = insertar
        self._actualizar = actualizar
        self._eliminar = eliminar
        self._valores_fila = valores_fila or (lambda fila: fila)
        self._valores_nuevo = valores_nuevo or (lambda: {})
        self._descripcion_fila = descripcion_fila or (lambda fila: str(next(iter(fila.values()))))
        self._ocultar = ocultar
        self._alerta = alerta

        if mostrar_encabezado:
            c.encabezado(self, titulo, descripcion, icono, color, color_suave).pack(fill="x", pady=(0, 16))

        barra = tk.Frame(self, bg=c.fondo_de(self))
        barra.pack(fill="x", pady=(0, 12))
        if insertar:
            c.Boton(barra, "Nuevo", self.nuevo, "primario", e.ICONO["agregar"]).pack(side="left")
        if actualizar:
            c.Boton(barra, "Editar", self.editar, "secundario", e.ICONO["editar"]).pack(side="left", padx=8)
        if eliminar:
            c.Boton(barra, "Eliminar", self.borrar, "secundario", e.ICONO["eliminar"]).pack(side="left")
        c.Boton(barra, "Exportar a Excel", lambda: self.tabla.exportar(self, self.titulo), "secundario",
                e.ICONO["exportar"]).pack(side="right")
        self.contador = tk.Label(barra, text="", font=e.FUENTE_NEGRITA, bg=e.PRIMARIO_SUAVE, fg=e.PRIMARIO,
                                 padx=10, pady=3)
        self.contador.pack(side="right", padx=12)
        self.barra = barra

        tarjeta = c.Tarjeta(self, relleno=16, expandir=True)
        tarjeta.pack(fill="both", expand=True)
        self.filtros = c.BarraFiltros(tarjeta.cuerpo, self.actualizar_datos, fechas=fechas,
                                      texto_busqueda=texto_busqueda)
        self.filtros.pack(fill="x", pady=(0, 12))
        self.tabla = c.Tabla(tarjeta.cuerpo, al_doble_clic=self.editar if actualizar else None)
        self.tabla.pack(fill="both", expand=True)

    # ----------------------------------------------------------------- acciones
    def actualizar_datos(self) -> None:
        """Vuelve a consultar el procedimiento de listado con los filtros actuales."""
        def consultar():
            texto, desde, hasta = self.filtros.valores()
            resultado = self._listar(texto, desde, hasta)
            self.tabla.cargar(resultado, ocultar=self._ocultar, alerta=self._alerta)
            self.contador.configure(text=f"{len(resultado.filas)} registro(s)")
        c.ejecutar_seguro(self, consultar)

    def nuevo(self) -> None:
        """Abre el formulario vacío y llama al procedimiento de inserción."""
        def guardar(datos):
            self._insertar(datos)
            self.actualizar_datos()
            c.Notificacion(self, "El registro se guardó correctamente.", "exito", "Registro guardado")
        campos = c.ejecutar_seguro(self, self._campos, "nuevo")
        valores = c.ejecutar_seguro(self, self._valores_nuevo)
        if campos is None or valores is None:
            return
        c.Formulario(self, f"Nuevo registro - {self.titulo}", campos, valores if valores is not True else {},
                     guardar)

    def editar(self) -> None:
        """Abre el formulario con el registro seleccionado y llama al procedimiento de actualización."""
        fila = self.tabla.seleccion()
        if fila is None:
            c.Notificacion(self, "Seleccione un registro de la lista.", "alerta", "Editar")
            return

        def guardar(datos):
            self._actualizar(datos)
            self.actualizar_datos()
            c.Notificacion(self, "Los cambios se guardaron correctamente.", "exito", "Cambios guardados")
        campos = c.ejecutar_seguro(self, self._campos, "editar")
        if campos is None:
            return
        c.Formulario(self, f"Editar - {self.titulo}", campos, self._valores_fila(fila), guardar)

    def borrar(self) -> None:
        """Pide confirmación y llama al procedimiento de eliminación."""
        fila = self.tabla.seleccion()
        if fila is None:
            c.Notificacion(self, "Seleccione un registro de la lista.", "alerta", "Eliminar")
            return
        if not c.confirmar(self, f"¿Eliminar {self._descripcion_fila(fila)}? Esta acción no se puede deshacer.",
                           "Eliminar registro", "Sí, eliminar"):
            return
        if c.ejecutar_seguro(self, self._eliminar, fila, exito="El registro se eliminó correctamente."):
            self.actualizar_datos()
