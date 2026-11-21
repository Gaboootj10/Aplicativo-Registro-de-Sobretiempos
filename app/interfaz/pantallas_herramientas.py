"""Pantallas de herramientas: importación de asistencias, respaldo y conexión."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from datos.conexion import BaseDatos, ErrorBaseDatos, Resultado
from datos.configuracion import ConfiguracionMySQL, carpeta_usuario
from interfaz import componentes as c
from interfaz import estilos as e
from logica import respaldo
from logica import validaciones as v
from logica.importador import leer_excel


def tarjeta_resumen(padre, icono, color, suave):
    """Pequeña tarjeta con ícono y texto (para resúmenes de procesos)."""
    tarjeta = c.Tarjeta(padre, relleno=14)
    c.Insignia(tarjeta.cuerpo, icono, color, suave, 40).pack(side="left")
    etiqueta = tk.Label(tarjeta.cuerpo, text="", font=e.FUENTE_NEGRITA, bg=e.BLANCO, fg=e.TEXTO, anchor="w",
                        justify="left")
    etiqueta.pack(side="left", padx=12, fill="x")
    return tarjeta, etiqueta


# --------------------------------------------------------------------- importar
class PantallaImportar(tk.Frame):
    """Importa el Reporte de Asistencia Detallado de Humana (Excel)."""

    def __init__(self, padre, bd: BaseDatos):
        super().__init__(padre, bg=e.FONDO)
        self.bd = bd
        self.filas = []
        c.encabezado(self, "Importar asistencias",
                     "Carga el Excel «Reporte de Asistencia Detallado» exportado desde Humana. Cada fila se registra "
                     "con sp_asistencia_importar (inserta o actualiza) y los disparadores calculan el sobretiempo.",
                     e.ICONO["importar"], e.VERDE, e.VERDE_SUAVE).pack(fill="x", pady=(0, 16))
        barra = tk.Frame(self, bg=e.FONDO)
        barra.pack(fill="x", pady=(0, 12))
        self.ruta = tk.StringVar()
        c.Boton(barra, "Seleccionar archivo", self.seleccionar, "secundario", e.ICONO["archivo"]).pack(side="left")
        self.archivo = tk.Label(barra, text="Ningún archivo seleccionado", font=e.FUENTE, bg=e.FONDO, fg=e.GRIS)
        self.archivo.pack(side="left", padx=12)
        self.boton = c.Boton(barra, "Importar filas válidas", self.importar, "exito", e.ICONO["importar"])
        self.boton.pack(side="right")
        self.boton.configure(state="disabled")

        fila = tk.Frame(self, bg=e.FONDO)
        fila.pack(fill="x", pady=(0, 12))
        self.resumen_tarjeta, self.resumen = tarjeta_resumen(fila, e.ICONO["info"], e.PRIMARIO, e.PRIMARIO_SUAVE)
        self.resumen_tarjeta.pack(fill="x")
        self.resumen.configure(text="Seleccione el archivo exportado desde Humana para ver la vista previa.")
        self.progreso = ttk.Progressbar(self, mode="determinate", style="Horizontal.TProgressbar")

        tarjeta = c.Tarjeta(self, relleno=14, expandir=True)
        tarjeta.pack(fill="both", expand=True)
        self.tabla = c.Tabla(tarjeta.cuerpo)
        self.tabla.pack(fill="both", expand=True)

    def actualizar(self) -> None:
        """No requiere recarga al mostrarse."""

    def seleccionar(self) -> None:
        """Lee el Excel y muestra la vista previa con el estado de cada fila."""
        ruta = filedialog.askopenfilename(parent=self, title="Reporte de Asistencia Detallado",
                                          filetypes=[("Libro de Excel", "*.xlsx")])
        if not ruta:
            return
        try:
            turnos = {f[0] for f in self.bd.llamar("sp_turno_listar").filas}
            empleados = {f[0] for f in self.bd.llamar("sp_empleado_listar", "").filas}
            self.filas = leer_excel(ruta, turnos, empleados)
        except (ErrorBaseDatos, v.ErrorValidacion, OSError) as error:
            c.mostrar_error(self, error, "No se pudo leer el archivo")
            return
        self.ruta.set(ruta)
        self.archivo.configure(text=Path(ruta).name, fg=e.TEXTO)
        self._mostrar([("Pendiente" if f.valida else f.observacion) for f in self.filas])
        validas = sum(f.valida for f in self.filas)
        self.resumen.configure(text=f"{len(self.filas)} fila(s) leídas:  {validas} válida(s)  ·  "
                                    f"{len(self.filas) - validas} con observaciones")
        self.boton.configure(state="normal" if validas else "disabled")

    def _mostrar(self, estados: list[str]) -> None:
        columnas = ["Fila", "Código", "Fecha", "Turno", "Entrada", "Salida", "Estado"]
        filas = [(f.fila_excel, f.codigo, f.fecha, f.turno, f.entrada and f.entrada.strftime("%H:%M"),
                  f.salida and f.salida.strftime("%H:%M"), estado) for f, estado in zip(self.filas, estados)]
        self.tabla.cargar(Resultado(columnas, filas),
                          alerta=lambda x: x["Estado"] not in ("Pendiente", "INSERTADA", "ACTUALIZADA"))

    def importar(self) -> None:
        """Envía cada fila válida al procedimiento sp_asistencia_importar, con barra de progreso."""
        if not c.confirmar(self, "Las asistencias que ya existan se actualizarán con los datos del archivo.",
                           "¿Importar las filas válidas?", "Sí, importar"):
            return
        estados, insertadas, actualizadas, errores = [], 0, 0, 0
        self.progreso.pack(fill="x", pady=(0, 12), before=self.resumen_tarjeta)
        self.progreso.configure(maximum=len(self.filas), value=0)
        for numero, fila in enumerate(self.filas, start=1):
            if fila.valida:
                try:
                    resultado = self.bd.llamar("sp_asistencia_importar", fila.codigo, fila.fecha, fila.turno,
                                               fila.entrada, fila.salida).filas[0][0]
                    estados.append(resultado)
                    insertadas += resultado == "INSERTADA"
                    actualizadas += resultado == "ACTUALIZADA"
                except ErrorBaseDatos as error:
                    estados.append(str(error))
                    errores += 1
            else:
                estados.append(fila.observacion)
            self.progreso.configure(value=numero)
            self.update_idletasks()
        self.after(600, self.progreso.pack_forget)
        self._mostrar(estados)
        self.boton.configure(state="disabled")
        self.resumen.configure(text=f"Importación terminada:  {insertadas} insertada(s)  ·  "
                                    f"{actualizadas} actualizada(s)  ·  {errores} con error")
        c.Notificacion(self, f"Insertadas: {insertadas}   Actualizadas: {actualizadas}   Con error: {errores}",
                       "exito" if not errores else "alerta", "Importación terminada")


# ---------------------------------------------------------------------- respaldo
class PantallaRespaldo(tk.Frame):
    """Genera respaldos con mysqldump y los restaura con el cliente mysql."""

    def __init__(self, padre, bd: BaseDatos):
        super().__init__(padre, bg=e.FONDO)
        self.bd = bd
        c.encabezado(self, "Respaldo y restauración",
                     "Copia completa de la base de datos (tablas, datos, procedimientos y disparadores) con "
                     "mysqldump --single-transaction.", e.ICONO["respaldo"], e.PRIMARIO, e.PRIMARIO_SUAVE
                     ).pack(fill="x", pady=(0, 16))
        barra = tk.Frame(self, bg=e.FONDO)
        barra.pack(fill="x", pady=(0, 12))
        self.carpeta = tk.StringVar(value=str(carpeta_usuario() / "respaldos"))
        tk.Label(barra, text=e.ICONO["carpeta"], font=(e.ICONOS, 11), bg=e.FONDO, fg=e.GRIS).pack(side="left")
        ttk.Entry(barra, textvariable=self.carpeta, width=62, font=e.FUENTE).pack(side="left", padx=8)
        c.Boton(barra, "Cambiar", self.cambiar_carpeta, "secundario").pack(side="left")
        c.Boton(barra, "Restaurar seleccionado", self.restaurar, "peligro", e.ICONO["restaurar"]).pack(side="right")
        c.Boton(barra, "Generar respaldo", self.generar, "primario", e.ICONO["guardar"]).pack(side="right", padx=8)
        self.progreso = ttk.Progressbar(self, mode="indeterminate", style="Horizontal.TProgressbar")
        tarjeta = c.Tarjeta(self, relleno=14, expandir=True)
        tarjeta.pack(fill="both", expand=True)
        self.tarjeta = tarjeta
        self.tabla = c.Tabla(tarjeta.cuerpo)
        self.tabla.pack(fill="both", expand=True)

    def actualizar(self) -> None:
        """Lista los respaldos de la carpeta."""
        self.tabla.cargar(Resultado(["Archivo", "Fecha", "Tamaño"], respaldo.listar_respaldos(self.carpeta.get())))

    def cambiar_carpeta(self) -> None:
        carpeta = filedialog.askdirectory(parent=self, initialdir=self.carpeta.get())
        if carpeta:
            self.carpeta.set(carpeta)
            self.actualizar()

    def _ocupado(self, activo: bool) -> None:
        if activo:
            self.progreso.pack(fill="x", pady=(0, 12), before=self.tarjeta)
            self.progreso.start(12)
            self.configure(cursor="watch")
        else:
            self.progreso.stop()
            self.progreso.pack_forget()
            self.configure(cursor="")
        self.update()

    def generar(self) -> None:
        """Genera un respaldo nuevo."""
        self._ocupado(True)
        try:
            archivo = respaldo.generar_respaldo(self.bd.config, self.carpeta.get())
            c.Notificacion(self, archivo.name, "exito", "Respaldo generado")
        except (respaldo.ErrorRespaldo, OSError) as error:
            c.mostrar_error(self, error, "No se pudo generar el respaldo")
        finally:
            self._ocupado(False)
        self.actualizar()

    def restaurar(self) -> None:
        """Restaura el respaldo seleccionado sobre la base de datos."""
        fila = self.tabla.seleccion()
        if fila is None:
            c.Notificacion(self, "Seleccione un respaldo de la lista.", "alerta", "Restaurar")
            return
        if not c.confirmar(self, f"Los datos actuales se reemplazarán por los del respaldo {fila['Archivo']}.",
                           "¿Restaurar el respaldo?", "Sí, restaurar"):
            return
        self._ocupado(True)
        try:
            self.bd.cerrar()
            respaldo.restaurar_respaldo(self.bd.config, Path(self.carpeta.get()) / fila["Archivo"])
            c.Notificacion(self, "La base de datos se restauró correctamente.", "exito", "Restauración completa")
        except (respaldo.ErrorRespaldo, OSError) as error:
            c.mostrar_error(self, error, "No se pudo restaurar")
        finally:
            self._ocupado(False)


# ---------------------------------------------------------------------- conexión
class DialogoConexion(c.VentanaFlotante):
    """Configura y prueba la conexión con MySQL (se guarda en config.ini)."""

    def __init__(self, padre, config: ConfiguracionMySQL, al_conectar, al_cancelar=None):
        super().__init__(padre, 560)
        self.al_conectar = al_conectar
        self.al_cancelar = al_cancelar
        cabecera = tk.Frame(self.contenido, bg=e.BLANCO, padx=26, pady=20)
        cabecera.pack(fill="x")
        c.Insignia(cabecera, e.ICONO["conexion"], e.PRIMARIO, e.PRIMARIO_SUAVE, 42).pack(side="left")
        textos = tk.Frame(cabecera, bg=e.BLANCO)
        textos.pack(side="left", padx=14)
        tk.Label(textos, text="Conexión con MySQL", font=e.FUENTE_SUBTITULO, bg=e.BLANCO, fg=e.TEXTO).pack(anchor="w")
        tk.Label(textos, text="Datos del servidor donde está la base de datos sobretiempos", font=e.FUENTE_PEQUENA,
                 bg=e.BLANCO, fg=e.GRIS).pack(anchor="w")
        tk.Frame(self.contenido, bg=e.BORDE, height=1).pack(fill="x")

        cuerpo = tk.Frame(self.contenido, bg=e.BLANCO, padx=26, pady=14)
        cuerpo.pack(fill="x")
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=1)
        self.vars = {
            "host": tk.StringVar(value=config.host), "puerto": tk.StringVar(value=str(config.puerto)),
            "usuario": tk.StringVar(value=config.usuario), "contrasena": tk.StringVar(value=config.contrasena),
            "base_datos": tk.StringVar(value=config.base_datos), "mysqldump": tk.StringVar(value=config.mysqldump),
            "mysql": tk.StringVar(value=config.mysql),
        }
        disposicion = [("host", "Servidor", 0, 0, 1), ("puerto", "Puerto", 0, 1, 1), ("usuario", "Usuario", 1, 0, 1),
                       ("base_datos", "Base de datos", 1, 1, 1), ("contrasena", "Contraseña", 2, 0, 2),
                       ("mysqldump", "Ruta de mysqldump.exe", 3, 0, 2), ("mysql", "Ruta de mysql.exe", 4, 0, 2)]
        for clave, texto, fila, columna, ancho in disposicion:
            celda = tk.Frame(cuerpo, bg=e.BLANCO)
            celda.grid(row=fila, column=columna, columnspan=ancho, sticky="ew", pady=5,
                       padx=(0, 12) if columna == 0 and ancho == 1 else 0)
            ttk.Label(celda, text=texto, style="Campo.TLabel").pack(anchor="w")
            linea = tk.Frame(celda, bg=e.BLANCO)
            linea.pack(fill="x", pady=(4, 0))
            ttk.Entry(linea, textvariable=self.vars[clave], show="•" if clave == "contrasena" else "", font=e.FUENTE).pack(
                side="left", fill="x", expand=True)
            if clave in ("mysqldump", "mysql"):
                c.Boton(linea, "", lambda k=clave: self._buscar(k), "secundario", e.ICONO["carpeta"], ancho=40,
                        alto=34).pack(side="left", padx=(6, 0))

        self.estado = tk.Label(self.contenido, text="", font=e.FUENTE_NEGRITA, bg=e.BLANCO, anchor="w",
                               padx=26, wraplength=500, justify="left")
        self.estado.pack(fill="x", pady=(0, 10))
        pie = tk.Frame(self.contenido, bg=e.SUPERFICIE, padx=26, pady=14)
        pie.pack(fill="x")
        c.Boton(pie, "Guardar y conectar", self.guardar, "primario", e.ICONO["ok"]).pack(side="right")
        c.Boton(pie, "Probar conexión", self.probar, "suave", e.ICONO["conexion"]).pack(side="right", padx=8)
        c.Boton(pie, "Cerrar", self._cancelar, "secundario").pack(side="left")
        self.bind("<Escape>", lambda _e: self._cancelar())
        self.mostrar()

    def _buscar(self, clave: str) -> None:
        ruta = filedialog.askopenfilename(parent=self, filetypes=[("Ejecutable", "*.exe")])
        if ruta:
            self.vars[clave].set(ruta)

    def _config(self) -> ConfiguracionMySQL:
        try:
            puerto = int(self.vars["puerto"].get())
        except ValueError:
            raise v.ErrorValidacion("El puerto debe ser un número (por defecto 3306).")
        return ConfiguracionMySQL(self.vars["host"].get().strip(), puerto, self.vars["usuario"].get().strip(),
                                  self.vars["contrasena"].get(), self.vars["base_datos"].get().strip(),
                                  self.vars["mysqldump"].get().strip(), self.vars["mysql"].get().strip())

    def _mensaje(self, texto: str, correcto: bool) -> None:
        self.estado.configure(text=f"{'✔' if correcto else '✖'}  {texto}",
                              fg=e.VERDE_HOVER if correcto else e.ROJO_HOVER)
        if not correcto:
            self.sacudir()

    def probar(self) -> bool:
        """Intenta conectarse y muestra el resultado."""
        self.estado.configure(text="Conectando...", fg=e.GRIS)
        self.update_idletasks()
        try:
            version = BaseDatos(self._config()).probar()
        except (ErrorBaseDatos, v.ErrorValidacion) as error:
            self._mensaje(str(error), False)
            return False
        self._mensaje(f"Conexión exitosa con MySQL {version}", True)
        return True

    def guardar(self) -> None:
        """Guarda la configuración y conecta el aplicativo si la prueba es exitosa."""
        if not self.probar():
            return
        config = self._config()
        config.guardar()
        self.cerrar()
        self.raiz.after(150, lambda: self.al_conectar(config))

    def _cancelar(self) -> None:
        self.cerrar()
        if self.al_cancelar:
            self.al_cancelar()

