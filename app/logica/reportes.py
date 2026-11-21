"""Catálogo de los 14 reportes del aplicativo.

Cada reporte es un procedimiento almacenado que recibe la fecha desde, la
fecha hasta y el código de empleado (vacío = sin filtro).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Reporte:
    """Datos de un reporte: título, procedimiento, descripción y si usa JOIN."""

    numero: int
    titulo: str
    procedimiento: str
    descripcion: str
    usa_join: bool


REPORTES = [
    Reporte(1, "Horas extra por empleado y tipo", "sp_reporte_empleado_tipo",
            "Desglose de horas de cada trabajador por código CC Nómina (1250, 1252, 1260) "
            "y su recargo. Sirve para preparar la nómina.", True),
    Reporte(2, "Total de horas extra por empleado", "sp_reporte_total_empleado",
            "Ranking de trabajadores con H25, H35, H100 y el total de horas extra.", True),
    Reporte(3, "Resumen por tipo de sobretiempo", "sp_reporte_resumen_tipo",
            "Total de horas por concepto de nómina, incluso los que no tienen horas.", True),
    Reporte(4, "Horas extra por centro de coste", "sp_reporte_centro_coste",
            "Horas extra agrupadas por centro de coste para el control de costos.", True),
    Reporte(5, "Horas extra por unidad organizativa", "sp_reporte_unidad",
            "Horas extra por área para planificar recursos y horarios.", True),
    Reporte(6, "Empleados por puesto y unidad", "sp_reporte_puestos",
            "Cantidad de empleados de cada puesto en cada unidad organizativa.", True),
    Reporte(7, "Detalle diario de asistencia", "sp_reporte_detalle_diario",
            "Asistencia día por día con turno, marcaciones y horas extra calculadas.", True),
    Reporte(8, "Verificación del cálculo H25/H35/H100", "sp_reporte_verificacion",
            "Recalcula las horas extra y las compara con lo almacenado (OK / REVISAR).", False),
    Reporte(9, "Conciliación SAP vs. sobretiempo", "sp_reporte_conciliacion",
            "Compara lo consolidado para SAP con la suma diaria de sobretiempo.", True),
    Reporte(10, "Horas cargadas a SAP por periodo", "sp_reporte_sap_periodo",
            "Horas consolidadas por periodo, empleado y código de nómina.", True),
    Reporte(11, "Empleados sin sobretiempo", "sp_reporte_sin_sobretiempo",
            "Trabajadores que no registraron horas extra en el rango de fechas.", True),
    Reporte(12, "Faltas y marcaciones incompletas", "sp_reporte_incompletas",
            "Días sin marcaciones o con una sola marca, para revisión manual.", False),
    Reporte(13, "Horas extra por mes", "sp_reporte_mensual",
            "Evolución mensual de las horas extra por tipo de recargo.", False),
    Reporte(14, "Días con más horas extra", "sp_reporte_dias_mayor",
            "Los 10 días con más horas extra acumuladas y los turnos involucrados.", True),
]
