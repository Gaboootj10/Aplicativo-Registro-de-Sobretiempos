-- =====================================================================
-- BASE DE DATOS: sobretiempos  (Industrias San Miguel del Sur S.A.C. - Kola Real)
-- Funcionalidad: Registro de sobretiempos  |  Entrega 5: aplicativo
-- Gestor: MySQL 8.0  |  Motor: InnoDB  |  Juego de caracteres: utf8mb4
-- Contenido: 1)   Creación de la base de datos (tablas)
--            1.1) Reglas de negocio: vistas, procedimientos y disparadores
--            1.2) Procedimientos y disparadores del aplicativo (CRUD,
--                 listados, panel y 14 reportes)
--            2)   Inserción de datos de prueba
--            3)   Consultas
-- =====================================================================

-- =====================================================================
-- 1. CREACIÓN DE LA BASE DE DATOS
-- =====================================================================
DROP DATABASE IF EXISTS sobretiempos;
CREATE DATABASE sobretiempos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sobretiempos;

-- Tabla Centro_Coste
CREATE TABLE centro_coste (
    codigo_centro_coste CHAR(8)     NOT NULL,
    centro_coste        VARCHAR(50) NOT NULL,
    PRIMARY KEY (codigo_centro_coste)
) ENGINE=InnoDB;

-- Tabla Area
CREATE TABLE area (
    codigo_area         CHAR(4)     NOT NULL,
    unidad_organizativa VARCHAR(50) NOT NULL,
    PRIMARY KEY (codigo_area)
) ENGINE=InnoDB;

-- Tabla Turno_Programado (DES = descanso obligatorio, FER = feriado)
CREATE TABLE turno_programado (
    codigo_turno            CHAR(3) NOT NULL,
    hora_entrada_programada TIME    NOT NULL,
    hora_salida_programada  TIME    NOT NULL,
    PRIMARY KEY (codigo_turno)
) ENGINE=InnoDB;

-- Tabla Tipo_Sobretiempo
CREATE TABLE tipo_sobretiempo (
    codigo_cc_nomina   CHAR(4)      NOT NULL,
    porcentaje_recargo DECIMAL(5,2) NOT NULL,
    PRIMARY KEY (codigo_cc_nomina),
    CONSTRAINT ck_recargo CHECK (porcentaje_recargo > 0)
) ENGINE=InnoDB;

-- Tabla Periodo
CREATE TABLE periodo (
    codigo_periodo CHAR(6) NOT NULL,
    fecha_inicio   DATE    NOT NULL,
    fecha_fin      DATE    NOT NULL,
    PRIMARY KEY (codigo_periodo),
    CONSTRAINT ck_periodo_codigo CHECK (codigo_periodo REGEXP '^[0-9]{6}$'),
    CONSTRAINT ck_periodo CHECK (fecha_fin >= fecha_inicio)
) ENGINE=InnoDB;

-- Tabla Empleado
CREATE TABLE empleado (
    codigo_empleado     CHAR(6)      NOT NULL,
    codigo_centro_coste CHAR(8)      NOT NULL,
    codigo_area         CHAR(4)      NOT NULL,
    dni                 CHAR(8)      NOT NULL,
    nombres             VARCHAR(255) NOT NULL,
    puesto              VARCHAR(100) NOT NULL,
    subdivision         VARCHAR(50)  NOT NULL,
    PRIMARY KEY (codigo_empleado),
    UNIQUE KEY uq_empleado_dni (dni),
    KEY idx_empleado_centro (codigo_centro_coste),
    KEY idx_empleado_area   (codigo_area),
    CONSTRAINT ck_empleado_codigo CHECK (codigo_empleado REGEXP '^[0-9]{6}$'),
    CONSTRAINT ck_empleado_dni    CHECK (dni REGEXP '^[0-9]{8}$'),
    CONSTRAINT fk_empleado_centro FOREIGN KEY (codigo_centro_coste)
        REFERENCES centro_coste (codigo_centro_coste),
    CONSTRAINT fk_empleado_area FOREIGN KEY (codigo_area)
        REFERENCES area (codigo_area)
) ENGINE=InnoDB;

-- Tabla Asistencia (un registro por empleado y fecha de inicio del turno)
CREATE TABLE asistencia (
    codigo_empleado          CHAR(6) NOT NULL,
    fecha                    DATE    NOT NULL,
    codigo_turno             CHAR(3) NOT NULL,
    marca_entrada            TIME    NULL,
    marca_salida             TIME    NULL,
    centro_costo_provisional CHAR(8) NULL,
    PRIMARY KEY (codigo_empleado, fecha),
    KEY idx_asistencia_turno (codigo_turno),
    KEY idx_asistencia_fecha (fecha),
    CONSTRAINT fk_asistencia_empleado FOREIGN KEY (codigo_empleado)
        REFERENCES empleado (codigo_empleado),
    CONSTRAINT fk_asistencia_turno FOREIGN KEY (codigo_turno)
        REFERENCES turno_programado (codigo_turno)
) ENGINE=InnoDB;

-- Tabla Sobretiempo (se llena automáticamente desde Asistencia)
CREATE TABLE sobretiempo (
    codigo_empleado  CHAR(6)      NOT NULL,
    fecha            DATE         NOT NULL,
    codigo_cc_nomina CHAR(4)      NOT NULL,
    horas            DECIMAL(4,2) NOT NULL,
    PRIMARY KEY (codigo_empleado, fecha, codigo_cc_nomina),
    KEY idx_sobretiempo_tipo (codigo_cc_nomina),
    CONSTRAINT ck_sobretiempo_horas CHECK (horas > 0),
    CONSTRAINT fk_sobretiempo_asistencia FOREIGN KEY (codigo_empleado, fecha)
        REFERENCES asistencia (codigo_empleado, fecha),
    CONSTRAINT fk_sobretiempo_tipo FOREIGN KEY (codigo_cc_nomina)
        REFERENCES tipo_sobretiempo (codigo_cc_nomina)
) ENGINE=InnoDB;

-- Tabla Registro_SAP (consolidado por empleado, tipo y periodo)
CREATE TABLE registro_sap (
    codigo_empleado   CHAR(6)      NOT NULL,
    codigo_cc_nomina  CHAR(4)      NOT NULL,
    codigo_periodo    CHAR(6)      NOT NULL,
    horas_registradas DECIMAL(5,2) NOT NULL,
    fecha_carga       DATE         NOT NULL,
    PRIMARY KEY (codigo_empleado, codigo_cc_nomina, codigo_periodo),
    KEY idx_sap_tipo    (codigo_cc_nomina),
    KEY idx_sap_periodo (codigo_periodo),
    CONSTRAINT ck_sap_horas CHECK (horas_registradas > 0),
    CONSTRAINT fk_sap_empleado FOREIGN KEY (codigo_empleado)
        REFERENCES empleado (codigo_empleado),
    CONSTRAINT fk_sap_tipo FOREIGN KEY (codigo_cc_nomina)
        REFERENCES tipo_sobretiempo (codigo_cc_nomina),
    CONSTRAINT fk_sap_periodo FOREIGN KEY (codigo_periodo)
        REFERENCES periodo (codigo_periodo)
) ENGINE=InnoDB;

-- Tabla de auditoría Registro_SAP_Historial (la llenan los disparadores)
-- No tiene claves foráneas para conservar el historial aunque se anule el registro.
CREATE TABLE registro_sap_historial (
    id_historial         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo_empleado      CHAR(6)      NOT NULL,
    codigo_cc_nomina     CHAR(4)      NOT NULL,
    codigo_periodo       CHAR(6)      NOT NULL,
    operacion            ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    horas_anteriores     DECIMAL(5,2) NULL,
    horas_nuevas         DECIMAL(5,2) NULL,
    fecha_carga_anterior DATE         NULL,
    fecha_carga_nueva    DATE         NULL,
    usuario              VARCHAR(100) NOT NULL,
    fecha_hora           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_historial),
    KEY idx_historial_registro (codigo_empleado, codigo_cc_nomina, codigo_periodo)
) ENGINE=InnoDB;

-- =====================================================================
-- 1.1 REGLAS DE NEGOCIO: VISTAS, PROCEDIMIENTOS Y DISPARADORES
-- (deben crearse antes de insertar: calculan el sobretiempo automáticamente)
-- =====================================================================
-- Reglas (sección 3.2.1 del informe):
--   * Sobretiempo = minutos antes de la entrada programada + minutos
--     después de la salida programada.
--   * Turno nocturno: si la salida programada es <= que la entrada, la
--     salida corresponde al día siguiente; si la marca de salida es <= que
--     la de entrada, también. La asistencia se registra en la fecha de inicio.
--   * Primeros 120 min -> 1250 (25 %), siguientes 120 min -> 1252 (35 %),
--     exceso -> 1260 (100 %).
--   * Trabajo en descanso (DES) o feriado (FER): todo el tiempo -> 1260.
--   * Marcación incompleta: no se calcula; queda para revisión manual.
--   * Horas = minutos / 60 redondeadas a dos decimales, sin tolerancia.
USE sobretiempos;

-- ---------------------------------------------------------------------
-- Vista v_minutos_extra: minutos extra de cada asistencia
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_minutos_extra AS
SELECT b.codigo_empleado, b.fecha, b.codigo_turno,
       b.marca_entrada, b.marca_salida, b.es_descanso,
       b.inicio_programado, b.fin_programado, b.entrada_real, b.salida_real,
       CASE WHEN b.entrada_real IS NULL OR b.salida_real IS NULL THEN NULL
            WHEN b.es_descanso = 1 THEN 0
            ELSE GREATEST(0, TIMESTAMPDIFF(MINUTE, b.entrada_real, b.inicio_programado))
       END AS minutos_antes,
       CASE WHEN b.entrada_real IS NULL OR b.salida_real IS NULL THEN NULL
            WHEN b.es_descanso = 1 THEN 0
            ELSE GREATEST(0, TIMESTAMPDIFF(MINUTE, b.fin_programado, b.salida_real))
       END AS minutos_despues,
       CASE WHEN b.entrada_real IS NULL OR b.salida_real IS NULL THEN NULL
            WHEN b.es_descanso = 1 THEN TIMESTAMPDIFF(MINUTE, b.entrada_real, b.salida_real)
            ELSE GREATEST(0, TIMESTAMPDIFF(MINUTE, b.entrada_real, b.inicio_programado))
               + GREATEST(0, TIMESTAMPDIFF(MINUTE, b.fin_programado, b.salida_real))
       END AS minutos_extra
FROM (
    SELECT a.codigo_empleado, a.fecha, a.codigo_turno, a.marca_entrada, a.marca_salida,
           IF(a.codigo_turno IN ('DES', 'FER'), 1, 0) AS es_descanso,
           TIMESTAMP(a.fecha, t.hora_entrada_programada) AS inicio_programado,
           TIMESTAMP(a.fecha + INTERVAL IF(t.hora_salida_programada <= t.hora_entrada_programada, 1, 0) DAY,
                     t.hora_salida_programada) AS fin_programado,
           -- en un turno nocturno, una entrada de madrugada pertenece al día siguiente
           TIMESTAMP(a.fecha + INTERVAL IF(t.hora_salida_programada < t.hora_entrada_programada
                                           AND a.marca_entrada < t.hora_salida_programada, 1, 0) DAY,
                     a.marca_entrada) AS entrada_real,
           TIMESTAMP(a.fecha + INTERVAL (IF(t.hora_salida_programada < t.hora_entrada_programada
                                            AND a.marca_entrada < t.hora_salida_programada, 1, 0)
                                        + IF(a.marca_salida <= a.marca_entrada, 1, 0)) DAY,
                     a.marca_salida) AS salida_real
    FROM asistencia a
    JOIN turno_programado t ON t.codigo_turno = a.codigo_turno
) b;

-- ---------------------------------------------------------------------
-- Vista v_verificacion_sobretiempo: recalcula H25, H35 y H100 y los
-- compara con lo almacenado en Sobretiempo (consulta 8)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_verificacion_sobretiempo AS
SELECT v.codigo_empleado, v.fecha, v.codigo_turno, v.marca_entrada, v.marca_salida,
       v.minutos_extra,
       ROUND(IF(v.es_descanso = 1, 0, LEAST(v.minutos_extra, 120)) / 60, 2)                  AS h25_calculado,
       ROUND(IF(v.es_descanso = 1, 0, LEAST(GREATEST(v.minutos_extra - 120, 0), 120)) / 60, 2) AS h35_calculado,
       ROUND(IF(v.es_descanso = 1, v.minutos_extra, GREATEST(v.minutos_extra - 240, 0)) / 60, 2) AS h100_calculado,
       COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1250' THEN s.horas END), 0) AS h25_registrado,
       COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1252' THEN s.horas END), 0) AS h35_registrado,
       COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1260' THEN s.horas END), 0) AS h100_registrado,
       CASE
         WHEN v.minutos_extra IS NULL AND v.es_descanso = 1
              AND v.marca_entrada IS NULL AND v.marca_salida IS NULL THEN 'DESCANSO'
         WHEN v.minutos_extra IS NULL THEN 'INCOMPLETA'
         WHEN ROUND(IF(v.es_descanso = 1, 0, LEAST(v.minutos_extra, 120)) / 60, 2)
                = COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1250' THEN s.horas END), 0)
          AND ROUND(IF(v.es_descanso = 1, 0, LEAST(GREATEST(v.minutos_extra - 120, 0), 120)) / 60, 2)
                = COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1252' THEN s.horas END), 0)
          AND ROUND(IF(v.es_descanso = 1, v.minutos_extra, GREATEST(v.minutos_extra - 240, 0)) / 60, 2)
                = COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1260' THEN s.horas END), 0)
         THEN 'OK' ELSE 'REVISAR'
       END AS resultado
FROM v_minutos_extra v
LEFT JOIN sobretiempo s ON s.codigo_empleado = v.codigo_empleado AND s.fecha = v.fecha
GROUP BY v.codigo_empleado, v.fecha, v.codigo_turno, v.marca_entrada, v.marca_salida,
         v.minutos_extra, v.es_descanso;

-- ---------------------------------------------------------------------
-- Vista v_asistencia_incompleta: faltas y marcaciones incompletas
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_asistencia_incompleta AS
SELECT a.codigo_empleado, e.nombres, a.fecha, a.codigo_turno,
       a.marca_entrada, a.marca_salida,
       CASE WHEN a.marca_entrada IS NULL AND a.marca_salida IS NULL THEN 'SIN MARCACIONES'
            WHEN a.marca_entrada IS NULL THEN 'FALTA MARCA DE ENTRADA'
            ELSE 'FALTA MARCA DE SALIDA' END AS observacion
FROM asistencia a
JOIN empleado e ON e.codigo_empleado = a.codigo_empleado
WHERE (a.marca_entrada IS NULL OR a.marca_salida IS NULL)
  AND NOT (a.codigo_turno IN ('DES', 'FER') AND a.marca_entrada IS NULL AND a.marca_salida IS NULL);

-- ---------------------------------------------------------------------
-- Vista v_conciliacion_sap: compara Registro_SAP con la suma de Sobretiempo
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_conciliacion_sap AS
SELECT c.codigo_empleado, c.codigo_cc_nomina, c.codigo_periodo,
       c.horas_calculadas, r.horas_registradas, r.fecha_carga,
       CASE WHEN r.horas_registradas IS NULL THEN 'PENDIENTE DE CARGA'
            WHEN r.horas_registradas = c.horas_calculadas THEN 'CONCILIADO'
            ELSE 'DESACTUALIZADO' END AS estado
FROM (SELECT s.codigo_empleado, s.codigo_cc_nomina, p.codigo_periodo,
             SUM(s.horas) AS horas_calculadas
      FROM sobretiempo s
      JOIN periodo p ON s.fecha BETWEEN p.fecha_inicio AND p.fecha_fin
      GROUP BY s.codigo_empleado, s.codigo_cc_nomina, p.codigo_periodo) c
LEFT JOIN registro_sap r
       ON r.codigo_empleado = c.codigo_empleado
      AND r.codigo_cc_nomina = c.codigo_cc_nomina
      AND r.codigo_periodo = c.codigo_periodo
UNION ALL
SELECT r.codigo_empleado, r.codigo_cc_nomina, r.codigo_periodo,
       0, r.horas_registradas, r.fecha_carga, 'SIN SUSTENTO'
FROM registro_sap r
JOIN periodo p ON p.codigo_periodo = r.codigo_periodo
WHERE NOT EXISTS (SELECT 1 FROM sobretiempo s
                  WHERE s.codigo_empleado = r.codigo_empleado
                    AND s.codigo_cc_nomina = r.codigo_cc_nomina
                    AND s.fecha BETWEEN p.fecha_inicio AND p.fecha_fin);

DELIMITER $$

-- ---------------------------------------------------------------------
-- sp_calcular_sobretiempo: calcula y clasifica el sobretiempo de una asistencia
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_calcular_sobretiempo $$
CREATE PROCEDURE sp_calcular_sobretiempo(IN p_empleado CHAR(6), IN p_fecha DATE)
BEGIN
    DECLARE v_minutos   INT DEFAULT NULL;
    DECLARE v_descanso  TINYINT DEFAULT 0;
    DECLARE v_m25       INT DEFAULT 0;
    DECLARE v_m35       INT DEFAULT 0;
    DECLARE v_m100      INT DEFAULT 0;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_minutos = NULL;

    DELETE FROM sobretiempo WHERE codigo_empleado = p_empleado AND fecha = p_fecha;

    SELECT minutos_extra, es_descanso INTO v_minutos, v_descanso
    FROM v_minutos_extra
    WHERE codigo_empleado = p_empleado AND fecha = p_fecha;

    IF v_minutos IS NOT NULL AND v_minutos > 0 THEN
        IF v_descanso = 1 THEN
            SET v_m100 = v_minutos;
        ELSE
            SET v_m25  = LEAST(v_minutos, 120);
            SET v_m35  = LEAST(GREATEST(v_minutos - 120, 0), 120);
            SET v_m100 = GREATEST(v_minutos - 240, 0);
        END IF;
        IF v_m25 > 0 THEN
            INSERT INTO sobretiempo VALUES (p_empleado, p_fecha, '1250', ROUND(v_m25 / 60, 2));
        END IF;
        IF v_m35 > 0 THEN
            INSERT INTO sobretiempo VALUES (p_empleado, p_fecha, '1252', ROUND(v_m35 / 60, 2));
        END IF;
        IF v_m100 > 0 THEN
            INSERT INTO sobretiempo VALUES (p_empleado, p_fecha, '1260', ROUND(v_m100 / 60, 2));
        END IF;
    END IF;
END $$

-- ---------------------------------------------------------------------
-- sp_recalcular_periodo: vuelve a calcular todas las asistencias de un periodo
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_recalcular_periodo $$
CREATE PROCEDURE sp_recalcular_periodo(IN p_periodo CHAR(6))
BEGIN
    DECLARE v_fin INT DEFAULT 0;
    DECLARE v_emp CHAR(6);
    DECLARE v_fec DATE;
    DECLARE cur CURSOR FOR
        SELECT a.codigo_empleado, a.fecha
        FROM asistencia a JOIN periodo p ON a.fecha BETWEEN p.fecha_inicio AND p.fecha_fin
        WHERE p.codigo_periodo = p_periodo;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_fin = 1;
    OPEN cur;
    bucle: LOOP
        FETCH cur INTO v_emp, v_fec;
        IF v_fin = 1 THEN LEAVE bucle; END IF;
        CALL sp_calcular_sobretiempo(v_emp, v_fec);
    END LOOP;
    CLOSE cur;
END $$

-- ---------------------------------------------------------------------
-- sp_consolidar_periodo: genera o actualiza Registro_SAP de un periodo.
-- Los cambios quedan en Registro_SAP_Historial mediante los disparadores.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_consolidar_periodo $$
CREATE PROCEDURE sp_consolidar_periodo(IN p_periodo CHAR(6), IN p_fecha_carga DATE)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM periodo WHERE codigo_periodo = p_periodo) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El periodo indicado no existe';
    END IF;

    -- anulación de consolidados que ya no tienen sobretiempo que los sustente
    DELETE r FROM registro_sap r
    JOIN periodo p ON p.codigo_periodo = r.codigo_periodo
    WHERE r.codigo_periodo = p_periodo
      AND NOT EXISTS (SELECT 1 FROM sobretiempo s
                      WHERE s.codigo_empleado = r.codigo_empleado
                        AND s.codigo_cc_nomina = r.codigo_cc_nomina
                        AND s.fecha BETWEEN p.fecha_inicio AND p.fecha_fin);

    -- inserción de nuevos consolidados o actualización (reproceso)
    INSERT INTO registro_sap (codigo_empleado, codigo_cc_nomina, codigo_periodo,
                              horas_registradas, fecha_carga)
    SELECT s.codigo_empleado, s.codigo_cc_nomina, p.codigo_periodo, SUM(s.horas), p_fecha_carga
    FROM sobretiempo s
    JOIN periodo p ON s.fecha BETWEEN p.fecha_inicio AND p.fecha_fin
    WHERE p.codigo_periodo = p_periodo
    GROUP BY s.codigo_empleado, s.codigo_cc_nomina, p.codigo_periodo
    ON DUPLICATE KEY UPDATE
        fecha_carga = IF(registro_sap.horas_registradas <> VALUES(horas_registradas),
                         VALUES(fecha_carga), registro_sap.fecha_carga),
        horas_registradas = VALUES(horas_registradas);
END $$

-- ---------------------------------------------------------------------
-- Disparadores de Asistencia: asignación automática del sobretiempo
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_asistencia_ai $$
CREATE TRIGGER trg_asistencia_ai AFTER INSERT ON asistencia
FOR EACH ROW
BEGIN
    CALL sp_calcular_sobretiempo(NEW.codigo_empleado, NEW.fecha);
END $$

DROP TRIGGER IF EXISTS trg_asistencia_au $$
CREATE TRIGGER trg_asistencia_au AFTER UPDATE ON asistencia
FOR EACH ROW
BEGIN
    CALL sp_calcular_sobretiempo(NEW.codigo_empleado, NEW.fecha);
END $$

DROP TRIGGER IF EXISTS trg_asistencia_bd $$
CREATE TRIGGER trg_asistencia_bd BEFORE DELETE ON asistencia
FOR EACH ROW
BEGIN
    DELETE FROM sobretiempo
    WHERE codigo_empleado = OLD.codigo_empleado AND fecha = OLD.fecha;
END $$

-- ---------------------------------------------------------------------
-- Disparadores de Registro_SAP: control de consistencia y auditoría
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_sap_bi $$
CREATE TRIGGER trg_sap_bi BEFORE INSERT ON registro_sap
FOR EACH ROW
BEGIN
    DECLARE v_suma DECIMAL(6,2);
    SELECT SUM(s.horas) INTO v_suma
    FROM sobretiempo s JOIN periodo p ON p.codigo_periodo = NEW.codigo_periodo
    WHERE s.codigo_empleado = NEW.codigo_empleado
      AND s.codigo_cc_nomina = NEW.codigo_cc_nomina
      AND s.fecha BETWEEN p.fecha_inicio AND p.fecha_fin;
    IF v_suma IS NULL OR v_suma <> NEW.horas_registradas THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Horas_Registradas no coincide con la suma de Sobretiempo del periodo';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_sap_bu $$
CREATE TRIGGER trg_sap_bu BEFORE UPDATE ON registro_sap
FOR EACH ROW
BEGIN
    DECLARE v_suma DECIMAL(6,2);
    SELECT SUM(s.horas) INTO v_suma
    FROM sobretiempo s JOIN periodo p ON p.codigo_periodo = NEW.codigo_periodo
    WHERE s.codigo_empleado = NEW.codigo_empleado
      AND s.codigo_cc_nomina = NEW.codigo_cc_nomina
      AND s.fecha BETWEEN p.fecha_inicio AND p.fecha_fin;
    IF v_suma IS NULL OR v_suma <> NEW.horas_registradas THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Horas_Registradas no coincide con la suma de Sobretiempo del periodo';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_sap_ai $$
CREATE TRIGGER trg_sap_ai AFTER INSERT ON registro_sap
FOR EACH ROW
BEGIN
    INSERT INTO registro_sap_historial (codigo_empleado, codigo_cc_nomina, codigo_periodo, operacion,
                                        horas_anteriores, horas_nuevas,
                                        fecha_carga_anterior, fecha_carga_nueva, usuario)
    VALUES (NEW.codigo_empleado, NEW.codigo_cc_nomina, NEW.codigo_periodo, 'INSERT',
            NULL, NEW.horas_registradas, NULL, NEW.fecha_carga, CURRENT_USER());
END $$

DROP TRIGGER IF EXISTS trg_sap_au $$
CREATE TRIGGER trg_sap_au AFTER UPDATE ON registro_sap
FOR EACH ROW
BEGIN
    IF OLD.horas_registradas <> NEW.horas_registradas OR OLD.fecha_carga <> NEW.fecha_carga THEN
        INSERT INTO registro_sap_historial (codigo_empleado, codigo_cc_nomina, codigo_periodo, operacion,
                                            horas_anteriores, horas_nuevas,
                                            fecha_carga_anterior, fecha_carga_nueva, usuario)
        VALUES (NEW.codigo_empleado, NEW.codigo_cc_nomina, NEW.codigo_periodo, 'UPDATE',
                OLD.horas_registradas, NEW.horas_registradas, OLD.fecha_carga, NEW.fecha_carga,
                CURRENT_USER());
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_sap_ad $$
CREATE TRIGGER trg_sap_ad AFTER DELETE ON registro_sap
FOR EACH ROW
BEGIN
    INSERT INTO registro_sap_historial (codigo_empleado, codigo_cc_nomina, codigo_periodo, operacion,
                                        horas_anteriores, horas_nuevas,
                                        fecha_carga_anterior, fecha_carga_nueva, usuario)
    VALUES (OLD.codigo_empleado, OLD.codigo_cc_nomina, OLD.codigo_periodo, 'DELETE',
            OLD.horas_registradas, NULL, OLD.fecha_carga, NULL, CURRENT_USER());
END $$

DELIMITER ;

-- =====================================================================
-- 1.2 PROCEDIMIENTOS Y DISPARADORES DEL APLICATIVO
-- Todas las inserciones, modificaciones y eliminaciones que realiza el
-- aplicativo se hacen mediante estos procedimientos almacenados. Los
-- disparadores normalizan los datos, protegen los registros y calculan
-- el sobretiempo automáticamente.
-- =====================================================================
USE sobretiempos;

DELIMITER $$

-- ---------------------------------------------------------------------
-- Utilidad: devuelve un mensaje de error legible para el usuario
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_error $$
CREATE PROCEDURE sp_error(IN p_mensaje VARCHAR(128))
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = p_mensaje;
END $$

-- =====================================================================
-- DISPARADORES DE VALIDACIÓN Y NORMALIZACIÓN
-- =====================================================================
DROP TRIGGER IF EXISTS trg_centro_coste_bi $$
CREATE TRIGGER trg_centro_coste_bi BEFORE INSERT ON centro_coste
FOR EACH ROW
BEGIN
    SET NEW.codigo_centro_coste = UPPER(TRIM(NEW.codigo_centro_coste));
    SET NEW.centro_coste = TRIM(NEW.centro_coste);
END $$

DROP TRIGGER IF EXISTS trg_centro_coste_bu $$
CREATE TRIGGER trg_centro_coste_bu BEFORE UPDATE ON centro_coste
FOR EACH ROW
BEGIN
    SET NEW.centro_coste = TRIM(NEW.centro_coste);
END $$

DROP TRIGGER IF EXISTS trg_area_bi $$
CREATE TRIGGER trg_area_bi BEFORE INSERT ON area
FOR EACH ROW
BEGIN
    SET NEW.codigo_area = UPPER(TRIM(NEW.codigo_area));
    SET NEW.unidad_organizativa = TRIM(NEW.unidad_organizativa);
END $$

DROP TRIGGER IF EXISTS trg_area_bu $$
CREATE TRIGGER trg_area_bu BEFORE UPDATE ON area
FOR EACH ROW
BEGIN
    SET NEW.unidad_organizativa = TRIM(NEW.unidad_organizativa);
END $$

DROP TRIGGER IF EXISTS trg_empleado_bi $$
CREATE TRIGGER trg_empleado_bi BEFORE INSERT ON empleado
FOR EACH ROW
BEGIN
    SET NEW.nombres     = UPPER(TRIM(NEW.nombres));
    SET NEW.puesto      = UPPER(TRIM(NEW.puesto));
    SET NEW.subdivision = TRIM(NEW.subdivision);
END $$

DROP TRIGGER IF EXISTS trg_empleado_bu $$
CREATE TRIGGER trg_empleado_bu BEFORE UPDATE ON empleado
FOR EACH ROW
BEGIN
    SET NEW.nombres     = UPPER(TRIM(NEW.nombres));
    SET NEW.puesto      = UPPER(TRIM(NEW.puesto));
    SET NEW.subdivision = TRIM(NEW.subdivision);
END $$

-- Un empleado con asistencias no se elimina: se conserva su historial.
DROP TRIGGER IF EXISTS trg_empleado_bd $$
CREATE TRIGGER trg_empleado_bd BEFORE DELETE ON empleado
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM asistencia WHERE codigo_empleado = OLD.codigo_empleado) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El empleado tiene asistencias registradas y no puede eliminarse';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_turno_bi $$
CREATE TRIGGER trg_turno_bi BEFORE INSERT ON turno_programado
FOR EACH ROW
BEGIN
    SET NEW.codigo_turno = UPPER(TRIM(NEW.codigo_turno));
END $$

-- Los turnos de descanso (DES) y feriado (FER) son necesarios para las reglas.
DROP TRIGGER IF EXISTS trg_turno_bd $$
CREATE TRIGGER trg_turno_bd BEFORE DELETE ON turno_programado
FOR EACH ROW
BEGIN
    IF OLD.codigo_turno IN ('DES', 'FER') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Los turnos DES y FER son parte de las reglas de cálculo y no pueden eliminarse';
    END IF;
END $$

-- =====================================================================
-- CENTRO DE COSTE
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_centro_coste_listar $$
CREATE PROCEDURE sp_centro_coste_listar(IN p_buscar VARCHAR(50))
BEGIN
    SELECT cc.codigo_centro_coste AS `Código`, cc.centro_coste AS `Centro de coste`,
           COUNT(e.codigo_empleado) AS `Empleados`
    FROM centro_coste cc
    LEFT JOIN empleado e ON e.codigo_centro_coste = cc.codigo_centro_coste
    WHERE p_buscar IS NULL OR p_buscar = ''
       OR cc.codigo_centro_coste LIKE CONCAT('%', p_buscar, '%')
       OR cc.centro_coste LIKE CONCAT('%', p_buscar, '%')
    GROUP BY cc.codigo_centro_coste, cc.centro_coste
    ORDER BY cc.codigo_centro_coste;
END $$

DROP PROCEDURE IF EXISTS sp_centro_coste_insertar $$
CREATE PROCEDURE sp_centro_coste_insertar(IN p_codigo CHAR(8), IN p_nombre VARCHAR(50))
BEGIN
    IF CHAR_LENGTH(TRIM(p_codigo)) <> 8 THEN
        CALL sp_error('El código del centro de coste debe tener 8 caracteres');
    END IF;
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        CALL sp_error('Ingrese el nombre del centro de coste');
    END IF;
    IF EXISTS (SELECT 1 FROM centro_coste WHERE codigo_centro_coste = p_codigo) THEN
        CALL sp_error(CONCAT('Ya existe el centro de coste ', p_codigo));
    END IF;
    INSERT INTO centro_coste (codigo_centro_coste, centro_coste) VALUES (p_codigo, p_nombre);
END $$

DROP PROCEDURE IF EXISTS sp_centro_coste_actualizar $$
CREATE PROCEDURE sp_centro_coste_actualizar(IN p_codigo CHAR(8), IN p_nombre VARCHAR(50))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM centro_coste WHERE codigo_centro_coste = p_codigo) THEN
        CALL sp_error(CONCAT('No existe el centro de coste ', p_codigo));
    END IF;
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        CALL sp_error('Ingrese el nombre del centro de coste');
    END IF;
    UPDATE centro_coste SET centro_coste = p_nombre WHERE codigo_centro_coste = p_codigo;
END $$

DROP PROCEDURE IF EXISTS sp_centro_coste_eliminar $$
CREATE PROCEDURE sp_centro_coste_eliminar(IN p_codigo CHAR(8))
BEGIN
    IF EXISTS (SELECT 1 FROM empleado WHERE codigo_centro_coste = p_codigo) THEN
        CALL sp_error('El centro de coste tiene empleados asignados y no puede eliminarse');
    END IF;
    DELETE FROM centro_coste WHERE codigo_centro_coste = p_codigo;
END $$

-- =====================================================================
-- ÁREA (UNIDAD ORGANIZATIVA)
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_area_listar $$
CREATE PROCEDURE sp_area_listar(IN p_buscar VARCHAR(50))
BEGIN
    SELECT a.codigo_area AS `Código`, a.unidad_organizativa AS `Unidad organizativa`,
           COUNT(e.codigo_empleado) AS `Empleados`
    FROM area a
    LEFT JOIN empleado e ON e.codigo_area = a.codigo_area
    WHERE p_buscar IS NULL OR p_buscar = ''
       OR a.codigo_area LIKE CONCAT('%', p_buscar, '%')
       OR a.unidad_organizativa LIKE CONCAT('%', p_buscar, '%')
    GROUP BY a.codigo_area, a.unidad_organizativa
    ORDER BY a.codigo_area;
END $$

DROP PROCEDURE IF EXISTS sp_area_siguiente_codigo $$
CREATE PROCEDURE sp_area_siguiente_codigo()
BEGIN
    SELECT CONCAT('A', LPAD(COALESCE(MAX(CAST(SUBSTRING(codigo_area, 2) AS UNSIGNED)), 0) + 1, 3, '0'))
           AS codigo
    FROM area WHERE codigo_area REGEXP '^A[0-9]{3}$';
END $$

DROP PROCEDURE IF EXISTS sp_area_insertar $$
CREATE PROCEDURE sp_area_insertar(IN p_codigo CHAR(4), IN p_nombre VARCHAR(50))
BEGIN
    IF CHAR_LENGTH(TRIM(p_codigo)) <> 4 THEN
        CALL sp_error('El código del área debe tener 4 caracteres');
    END IF;
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        CALL sp_error('Ingrese el nombre de la unidad organizativa');
    END IF;
    IF EXISTS (SELECT 1 FROM area WHERE codigo_area = p_codigo) THEN
        CALL sp_error(CONCAT('Ya existe el área ', p_codigo));
    END IF;
    IF EXISTS (SELECT 1 FROM area WHERE unidad_organizativa = TRIM(p_nombre)) THEN
        CALL sp_error('Ya existe una unidad organizativa con ese nombre');
    END IF;
    INSERT INTO area (codigo_area, unidad_organizativa) VALUES (p_codigo, p_nombre);
END $$

DROP PROCEDURE IF EXISTS sp_area_actualizar $$
CREATE PROCEDURE sp_area_actualizar(IN p_codigo CHAR(4), IN p_nombre VARCHAR(50))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM area WHERE codigo_area = p_codigo) THEN
        CALL sp_error(CONCAT('No existe el área ', p_codigo));
    END IF;
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        CALL sp_error('Ingrese el nombre de la unidad organizativa');
    END IF;
    UPDATE area SET unidad_organizativa = p_nombre WHERE codigo_area = p_codigo;
END $$

DROP PROCEDURE IF EXISTS sp_area_eliminar $$
CREATE PROCEDURE sp_area_eliminar(IN p_codigo CHAR(4))
BEGIN
    IF EXISTS (SELECT 1 FROM empleado WHERE codigo_area = p_codigo) THEN
        CALL sp_error('El área tiene empleados asignados y no puede eliminarse');
    END IF;
    DELETE FROM area WHERE codigo_area = p_codigo;
END $$

-- =====================================================================
-- TURNO PROGRAMADO
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_turno_listar $$
CREATE PROCEDURE sp_turno_listar()
BEGIN
    SELECT t.codigo_turno AS `Código`,
           TIME_FORMAT(t.hora_entrada_programada, '%H:%i') AS `Entrada`,
           TIME_FORMAT(t.hora_salida_programada, '%H:%i')  AS `Salida`,
           CASE WHEN t.codigo_turno = 'DES' THEN 'Descanso'
                WHEN t.codigo_turno = 'FER' THEN 'Feriado'
                WHEN t.hora_salida_programada <= t.hora_entrada_programada THEN 'Nocturno'
                ELSE 'Diurno' END AS `Tipo`,
           COUNT(a.fecha) AS `Asistencias`
    FROM turno_programado t
    LEFT JOIN asistencia a ON a.codigo_turno = t.codigo_turno
    GROUP BY t.codigo_turno, t.hora_entrada_programada, t.hora_salida_programada
    ORDER BY t.codigo_turno;
END $$

DROP PROCEDURE IF EXISTS sp_turno_insertar $$
CREATE PROCEDURE sp_turno_insertar(IN p_codigo CHAR(3), IN p_entrada TIME, IN p_salida TIME)
BEGIN
    IF CHAR_LENGTH(TRIM(p_codigo)) <> 3 THEN
        CALL sp_error('El código del turno debe tener 3 caracteres');
    END IF;
    IF p_entrada IS NULL OR p_salida IS NULL THEN
        CALL sp_error('Ingrese la hora de entrada y de salida del turno');
    END IF;
    IF EXISTS (SELECT 1 FROM turno_programado WHERE codigo_turno = p_codigo) THEN
        CALL sp_error(CONCAT('Ya existe el turno ', p_codigo));
    END IF;
    INSERT INTO turno_programado (codigo_turno, hora_entrada_programada, hora_salida_programada)
    VALUES (p_codigo, p_entrada, p_salida);
END $$

-- Al cambiar el horario se recalcula el sobretiempo de las asistencias del turno.
DROP PROCEDURE IF EXISTS sp_turno_actualizar $$
CREATE PROCEDURE sp_turno_actualizar(IN p_codigo CHAR(3), IN p_entrada TIME, IN p_salida TIME)
BEGIN
    DECLARE v_fin INT DEFAULT 0;
    DECLARE v_emp CHAR(6);
    DECLARE v_fec DATE;
    DECLARE cur CURSOR FOR
        SELECT codigo_empleado, fecha FROM asistencia WHERE codigo_turno = p_codigo;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_fin = 1;

    IF NOT EXISTS (SELECT 1 FROM turno_programado WHERE codigo_turno = p_codigo) THEN
        CALL sp_error(CONCAT('No existe el turno ', p_codigo));
    END IF;
    IF p_codigo IN ('DES', 'FER') THEN
        CALL sp_error('Los turnos DES y FER no tienen horario y no se modifican');
    END IF;
    IF p_entrada IS NULL OR p_salida IS NULL THEN
        CALL sp_error('Ingrese la hora de entrada y de salida del turno');
    END IF;
    UPDATE turno_programado
    SET hora_entrada_programada = p_entrada, hora_salida_programada = p_salida
    WHERE codigo_turno = p_codigo;

    OPEN cur;
    bucle: LOOP
        FETCH cur INTO v_emp, v_fec;
        IF v_fin = 1 THEN LEAVE bucle; END IF;
        CALL sp_calcular_sobretiempo(v_emp, v_fec);
    END LOOP;
    CLOSE cur;
END $$

DROP PROCEDURE IF EXISTS sp_turno_eliminar $$
CREATE PROCEDURE sp_turno_eliminar(IN p_codigo CHAR(3))
BEGIN
    IF EXISTS (SELECT 1 FROM asistencia WHERE codigo_turno = p_codigo) THEN
        CALL sp_error('El turno se usa en asistencias registradas y no puede eliminarse');
    END IF;
    DELETE FROM turno_programado WHERE codigo_turno = p_codigo;
END $$

-- =====================================================================
-- PERIODO
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_periodo_listar $$
CREATE PROCEDURE sp_periodo_listar()
BEGIN
    SELECT p.codigo_periodo AS `Código`, p.fecha_inicio AS `Inicio`, p.fecha_fin AS `Fin`,
           COUNT(r.codigo_empleado) AS `Consolidados SAP`,
           COALESCE(SUM(r.horas_registradas), 0) AS `Horas cargadas`
    FROM periodo p
    LEFT JOIN registro_sap r ON r.codigo_periodo = p.codigo_periodo
    GROUP BY p.codigo_periodo, p.fecha_inicio, p.fecha_fin
    ORDER BY p.codigo_periodo DESC;
END $$

DROP PROCEDURE IF EXISTS sp_periodo_validar $$
CREATE PROCEDURE sp_periodo_validar(IN p_codigo CHAR(6), IN p_inicio DATE, IN p_fin DATE)
BEGIN
    IF p_codigo NOT REGEXP '^[0-9]{6}$' THEN
        CALL sp_error('El código del periodo debe tener 6 dígitos (AAAAMM)');
    END IF;
    IF p_inicio IS NULL OR p_fin IS NULL THEN
        CALL sp_error('Ingrese la fecha de inicio y de fin del periodo');
    END IF;
    IF p_fin < p_inicio THEN
        CALL sp_error('La fecha de fin no puede ser anterior a la fecha de inicio');
    END IF;
    IF EXISTS (SELECT 1 FROM periodo
               WHERE codigo_periodo <> p_codigo
                 AND p_inicio <= fecha_fin AND p_fin >= fecha_inicio) THEN
        CALL sp_error('Las fechas se cruzan con otro periodo registrado');
    END IF;
END $$

DROP PROCEDURE IF EXISTS sp_periodo_insertar $$
CREATE PROCEDURE sp_periodo_insertar(IN p_codigo CHAR(6), IN p_inicio DATE, IN p_fin DATE)
BEGIN
    IF EXISTS (SELECT 1 FROM periodo WHERE codigo_periodo = p_codigo) THEN
        CALL sp_error(CONCAT('Ya existe el periodo ', p_codigo));
    END IF;
    CALL sp_periodo_validar(p_codigo, p_inicio, p_fin);
    INSERT INTO periodo (codigo_periodo, fecha_inicio, fecha_fin) VALUES (p_codigo, p_inicio, p_fin);
END $$

DROP PROCEDURE IF EXISTS sp_periodo_actualizar $$
CREATE PROCEDURE sp_periodo_actualizar(IN p_codigo CHAR(6), IN p_inicio DATE, IN p_fin DATE)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM periodo WHERE codigo_periodo = p_codigo) THEN
        CALL sp_error(CONCAT('No existe el periodo ', p_codigo));
    END IF;
    IF EXISTS (SELECT 1 FROM registro_sap WHERE codigo_periodo = p_codigo) THEN
        CALL sp_error('El periodo ya fue consolidado para SAP y sus fechas no pueden cambiar');
    END IF;
    CALL sp_periodo_validar(p_codigo, p_inicio, p_fin);
    UPDATE periodo SET fecha_inicio = p_inicio, fecha_fin = p_fin WHERE codigo_periodo = p_codigo;
END $$

DROP PROCEDURE IF EXISTS sp_periodo_eliminar $$
CREATE PROCEDURE sp_periodo_eliminar(IN p_codigo CHAR(6))
BEGIN
    IF EXISTS (SELECT 1 FROM registro_sap WHERE codigo_periodo = p_codigo) THEN
        CALL sp_error('El periodo tiene consolidados SAP y no puede eliminarse');
    END IF;
    DELETE FROM periodo WHERE codigo_periodo = p_codigo;
END $$

-- =====================================================================
-- EMPLEADO
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_empleado_listar $$
CREATE PROCEDURE sp_empleado_listar(IN p_buscar VARCHAR(100))
BEGIN
    SELECT e.codigo_empleado AS `Código`, e.dni AS `DNI`, e.nombres AS `Nombres`,
           e.puesto AS `Puesto`, a.unidad_organizativa AS `Unidad organizativa`,
           cc.centro_coste AS `Centro de coste`, e.subdivision AS `Subdivisión`,
           e.codigo_area AS `Cód. área`, e.codigo_centro_coste AS `Cód. centro`
    FROM empleado e
    JOIN area a          ON a.codigo_area = e.codigo_area
    JOIN centro_coste cc ON cc.codigo_centro_coste = e.codigo_centro_coste
    WHERE p_buscar IS NULL OR p_buscar = ''
       OR e.codigo_empleado LIKE CONCAT('%', p_buscar, '%')
       OR e.dni LIKE CONCAT('%', p_buscar, '%')
       OR e.nombres LIKE CONCAT('%', p_buscar, '%')
    ORDER BY e.codigo_empleado;
END $$

DROP PROCEDURE IF EXISTS sp_empleado_siguiente_codigo $$
CREATE PROCEDURE sp_empleado_siguiente_codigo()
BEGIN
    SELECT LPAD(COALESCE(MAX(CAST(codigo_empleado AS UNSIGNED)), 700000) + 1, 6, '0') AS codigo
    FROM empleado;
END $$

DROP PROCEDURE IF EXISTS sp_empleado_validar $$
CREATE PROCEDURE sp_empleado_validar(IN p_codigo CHAR(6), IN p_dni CHAR(8), IN p_nombres VARCHAR(255),
                                     IN p_puesto VARCHAR(100), IN p_subdivision VARCHAR(50),
                                     IN p_centro CHAR(8), IN p_area CHAR(4))
BEGIN
    IF p_codigo NOT REGEXP '^[0-9]{6}$' THEN
        CALL sp_error('El código del empleado debe tener 6 dígitos');
    END IF;
    IF p_dni NOT REGEXP '^[0-9]{8}$' THEN
        CALL sp_error('El DNI debe tener 8 dígitos');
    END IF;
    IF TRIM(COALESCE(p_nombres, '')) = '' OR TRIM(COALESCE(p_puesto, '')) = ''
       OR TRIM(COALESCE(p_subdivision, '')) = '' THEN
        CALL sp_error('Complete los nombres, el puesto y la subdivisión');
    END IF;
    IF EXISTS (SELECT 1 FROM empleado WHERE dni = p_dni AND codigo_empleado <> p_codigo) THEN
        CALL sp_error(CONCAT('El DNI ', p_dni, ' ya pertenece a otro empleado'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM centro_coste WHERE codigo_centro_coste = p_centro) THEN
        CALL sp_error('Seleccione un centro de coste válido');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM area WHERE codigo_area = p_area) THEN
        CALL sp_error('Seleccione un área válida');
    END IF;
END $$

DROP PROCEDURE IF EXISTS sp_empleado_insertar $$
CREATE PROCEDURE sp_empleado_insertar(IN p_codigo CHAR(6), IN p_dni CHAR(8), IN p_nombres VARCHAR(255),
                                      IN p_puesto VARCHAR(100), IN p_subdivision VARCHAR(50),
                                      IN p_centro CHAR(8), IN p_area CHAR(4))
BEGIN
    IF EXISTS (SELECT 1 FROM empleado WHERE codigo_empleado = p_codigo) THEN
        CALL sp_error(CONCAT('Ya existe un empleado con el código ', p_codigo));
    END IF;
    CALL sp_empleado_validar(p_codigo, p_dni, p_nombres, p_puesto, p_subdivision, p_centro, p_area);
    INSERT INTO empleado (codigo_empleado, codigo_centro_coste, codigo_area, dni, nombres, puesto, subdivision)
    VALUES (p_codigo, p_centro, p_area, p_dni, p_nombres, p_puesto, p_subdivision);
END $$

DROP PROCEDURE IF EXISTS sp_empleado_actualizar $$
CREATE PROCEDURE sp_empleado_actualizar(IN p_codigo CHAR(6), IN p_dni CHAR(8), IN p_nombres VARCHAR(255),
                                        IN p_puesto VARCHAR(100), IN p_subdivision VARCHAR(50),
                                        IN p_centro CHAR(8), IN p_area CHAR(4))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM empleado WHERE codigo_empleado = p_codigo) THEN
        CALL sp_error(CONCAT('No existe el empleado ', p_codigo));
    END IF;
    CALL sp_empleado_validar(p_codigo, p_dni, p_nombres, p_puesto, p_subdivision, p_centro, p_area);
    UPDATE empleado
    SET dni = p_dni, nombres = p_nombres, puesto = p_puesto, subdivision = p_subdivision,
        codigo_centro_coste = p_centro, codigo_area = p_area
    WHERE codigo_empleado = p_codigo;
END $$

-- La protección del historial la realiza el disparador trg_empleado_bd.
DROP PROCEDURE IF EXISTS sp_empleado_eliminar $$
CREATE PROCEDURE sp_empleado_eliminar(IN p_codigo CHAR(6))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM empleado WHERE codigo_empleado = p_codigo) THEN
        CALL sp_error(CONCAT('No existe el empleado ', p_codigo));
    END IF;
    DELETE FROM empleado WHERE codigo_empleado = p_codigo;
END $$

-- =====================================================================
-- ASISTENCIA (el sobretiempo lo calculan los disparadores de Asistencia)
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_asistencia_listar $$
CREATE PROCEDURE sp_asistencia_listar(IN p_buscar VARCHAR(100), IN p_desde DATE, IN p_hasta DATE)
BEGIN
    SELECT a.codigo_empleado AS `Código`, e.nombres AS `Nombres`, a.fecha AS `Fecha`,
           ELT(DAYOFWEEK(a.fecha), 'Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb') AS `Día`,
           a.codigo_turno AS `Turno`,
           CONCAT(TIME_FORMAT(t.hora_entrada_programada, '%H:%i'), '-',
                  TIME_FORMAT(t.hora_salida_programada, '%H:%i')) AS `Horario`,
           TIME_FORMAT(a.marca_entrada, '%H:%i') AS `Entrada`,
           TIME_FORMAT(a.marca_salida, '%H:%i')  AS `Salida`,
           COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1250' THEN s.horas END), 0) AS `H25`,
           COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1252' THEN s.horas END), 0) AS `H35`,
           COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1260' THEN s.horas END), 0) AS `H100`,
           CASE WHEN a.marca_entrada IS NULL AND a.marca_salida IS NULL
                     THEN IF(a.codigo_turno IN ('DES', 'FER'), 'Descanso', 'Sin marcaciones')
                WHEN a.marca_entrada IS NULL OR a.marca_salida IS NULL THEN 'Incompleta'
                ELSE 'Completa' END AS `Estado`,
           a.centro_costo_provisional AS `C. coste provisional`
    FROM asistencia a
    JOIN empleado e          ON e.codigo_empleado = a.codigo_empleado
    JOIN turno_programado t  ON t.codigo_turno = a.codigo_turno
    LEFT JOIN sobretiempo s  ON s.codigo_empleado = a.codigo_empleado AND s.fecha = a.fecha
    WHERE (p_buscar IS NULL OR p_buscar = ''
           OR a.codigo_empleado LIKE CONCAT('%', p_buscar, '%')
           OR e.nombres LIKE CONCAT('%', p_buscar, '%'))
      AND (p_desde IS NULL OR a.fecha >= p_desde)
      AND (p_hasta IS NULL OR a.fecha <= p_hasta)
    GROUP BY a.codigo_empleado, e.nombres, a.fecha, a.codigo_turno, t.hora_entrada_programada,
             t.hora_salida_programada, a.marca_entrada, a.marca_salida, a.centro_costo_provisional
    ORDER BY a.fecha DESC, a.codigo_empleado;
END $$

DROP PROCEDURE IF EXISTS sp_asistencia_validar $$
CREATE PROCEDURE sp_asistencia_validar(IN p_empleado CHAR(6), IN p_turno CHAR(3),
                                       IN p_centro_prov CHAR(8))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM empleado WHERE codigo_empleado = p_empleado) THEN
        CALL sp_error(CONCAT('No existe el empleado ', COALESCE(p_empleado, '')));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM turno_programado WHERE codigo_turno = p_turno) THEN
        CALL sp_error(CONCAT('No existe el turno ', COALESCE(p_turno, '')));
    END IF;
    IF p_centro_prov IS NOT NULL AND p_centro_prov <> '' AND CHAR_LENGTH(p_centro_prov) <> 8 THEN
        CALL sp_error('El centro de coste provisional debe tener 8 caracteres');
    END IF;
END $$

DROP PROCEDURE IF EXISTS sp_asistencia_insertar $$
CREATE PROCEDURE sp_asistencia_insertar(IN p_empleado CHAR(6), IN p_fecha DATE, IN p_turno CHAR(3),
                                        IN p_entrada TIME, IN p_salida TIME, IN p_centro_prov CHAR(8))
BEGIN
    IF p_fecha IS NULL THEN
        CALL sp_error('Ingrese la fecha de la asistencia');
    END IF;
    CALL sp_asistencia_validar(p_empleado, p_turno, p_centro_prov);
    IF EXISTS (SELECT 1 FROM asistencia WHERE codigo_empleado = p_empleado AND fecha = p_fecha) THEN
        CALL sp_error('El empleado ya tiene una asistencia registrada en esa fecha');
    END IF;
    INSERT INTO asistencia (codigo_empleado, fecha, codigo_turno, marca_entrada, marca_salida,
                            centro_costo_provisional)
    VALUES (p_empleado, p_fecha, p_turno, p_entrada, p_salida, NULLIF(p_centro_prov, ''));
END $$

DROP PROCEDURE IF EXISTS sp_asistencia_actualizar $$
CREATE PROCEDURE sp_asistencia_actualizar(IN p_empleado CHAR(6), IN p_fecha DATE, IN p_turno CHAR(3),
                                          IN p_entrada TIME, IN p_salida TIME, IN p_centro_prov CHAR(8))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM asistencia WHERE codigo_empleado = p_empleado AND fecha = p_fecha) THEN
        CALL sp_error('No existe la asistencia indicada');
    END IF;
    CALL sp_asistencia_validar(p_empleado, p_turno, p_centro_prov);
    UPDATE asistencia
    SET codigo_turno = p_turno, marca_entrada = p_entrada, marca_salida = p_salida,
        centro_costo_provisional = NULLIF(p_centro_prov, '')
    WHERE codigo_empleado = p_empleado AND fecha = p_fecha;
END $$

DROP PROCEDURE IF EXISTS sp_asistencia_eliminar $$
CREATE PROCEDURE sp_asistencia_eliminar(IN p_empleado CHAR(6), IN p_fecha DATE)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM asistencia WHERE codigo_empleado = p_empleado AND fecha = p_fecha) THEN
        CALL sp_error('No existe la asistencia indicada');
    END IF;
    DELETE FROM asistencia WHERE codigo_empleado = p_empleado AND fecha = p_fecha;
END $$

-- Importación del Reporte de Asistencia Detallado: inserta o actualiza.
DROP PROCEDURE IF EXISTS sp_asistencia_importar $$
CREATE PROCEDURE sp_asistencia_importar(IN p_empleado CHAR(6), IN p_fecha DATE, IN p_turno CHAR(3),
                                        IN p_entrada TIME, IN p_salida TIME)
BEGIN
    IF EXISTS (SELECT 1 FROM asistencia WHERE codigo_empleado = p_empleado AND fecha = p_fecha) THEN
        CALL sp_asistencia_actualizar(p_empleado, p_fecha, p_turno, p_entrada, p_salida, NULL);
        SELECT 'ACTUALIZADA' AS resultado;
    ELSE
        CALL sp_asistencia_insertar(p_empleado, p_fecha, p_turno, p_entrada, p_salida, NULL);
        SELECT 'INSERTADA' AS resultado;
    END IF;
END $$

-- =====================================================================
-- SOBRETIEMPO, CONSOLIDACIÓN SAP Y PANEL
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_sobretiempo_listar $$
CREATE PROCEDURE sp_sobretiempo_listar(IN p_buscar VARCHAR(100), IN p_desde DATE, IN p_hasta DATE)
BEGIN
    SELECT s.codigo_empleado AS `Código`, e.nombres AS `Nombres`, s.fecha AS `Fecha`,
           a.codigo_turno AS `Turno`, s.codigo_cc_nomina AS `CC Nómina`,
           CONCAT(FORMAT(t.porcentaje_recargo, 0), ' %') AS `Recargo`, s.horas AS `Horas`
    FROM sobretiempo s
    JOIN empleado e          ON e.codigo_empleado = s.codigo_empleado
    JOIN asistencia a        ON a.codigo_empleado = s.codigo_empleado AND a.fecha = s.fecha
    JOIN tipo_sobretiempo t  ON t.codigo_cc_nomina = s.codigo_cc_nomina
    WHERE (p_buscar IS NULL OR p_buscar = ''
           OR s.codigo_empleado LIKE CONCAT('%', p_buscar, '%')
           OR e.nombres LIKE CONCAT('%', p_buscar, '%'))
      AND (p_desde IS NULL OR s.fecha >= p_desde)
      AND (p_hasta IS NULL OR s.fecha <= p_hasta)
    ORDER BY s.fecha DESC, s.codigo_empleado, s.codigo_cc_nomina;
END $$

DROP PROCEDURE IF EXISTS sp_registro_sap_listar $$
CREATE PROCEDURE sp_registro_sap_listar(IN p_periodo CHAR(6))
BEGIN
    SELECT c.codigo_periodo AS `Periodo`, c.codigo_empleado AS `Código`, e.nombres AS `Nombres`,
           c.codigo_cc_nomina AS `CC Nómina`, c.horas_calculadas AS `Horas calculadas`,
           c.horas_registradas AS `Horas registradas`, c.fecha_carga AS `Fecha de carga`,
           c.estado AS `Estado`
    FROM v_conciliacion_sap c
    JOIN empleado e ON e.codigo_empleado = c.codigo_empleado
    WHERE p_periodo IS NULL OR p_periodo = '' OR c.codigo_periodo = p_periodo
    ORDER BY c.codigo_periodo DESC, c.codigo_empleado, c.codigo_cc_nomina;
END $$

DROP PROCEDURE IF EXISTS sp_historial_sap_listar $$
CREATE PROCEDURE sp_historial_sap_listar(IN p_periodo CHAR(6))
BEGIN
    SELECT h.id_historial AS `N.°`, h.fecha_hora AS `Fecha y hora`, h.operacion AS `Operación`,
           h.codigo_periodo AS `Periodo`, h.codigo_empleado AS `Código`,
           COALESCE(e.nombres, '(eliminado)') AS `Nombres`, h.codigo_cc_nomina AS `CC Nómina`,
           h.horas_anteriores AS `Horas anteriores`, h.horas_nuevas AS `Horas nuevas`,
           h.usuario AS `Usuario`
    FROM registro_sap_historial h
    LEFT JOIN empleado e ON e.codigo_empleado = h.codigo_empleado
    WHERE p_periodo IS NULL OR p_periodo = '' OR h.codigo_periodo = p_periodo
    ORDER BY h.id_historial DESC;
END $$

DROP PROCEDURE IF EXISTS sp_dashboard $$
CREATE PROCEDURE sp_dashboard()
BEGIN
    SELECT (SELECT COUNT(*) FROM empleado)                                   AS empleados,
           (SELECT COUNT(*) FROM asistencia)                                 AS asistencias,
           (SELECT COALESCE(SUM(horas), 0) FROM sobretiempo)                 AS horas_extra,
           (SELECT COUNT(DISTINCT codigo_empleado) FROM sobretiempo)         AS empleados_con_extra,
           (SELECT COUNT(*) FROM v_asistencia_incompleta)                    AS incompletas,
           (SELECT COUNT(*) FROM v_conciliacion_sap WHERE estado <> 'CONCILIADO') AS pendientes_sap;
END $$

DROP PROCEDURE IF EXISTS sp_dashboard_top $$
CREATE PROCEDURE sp_dashboard_top()
BEGIN
    SELECT e.codigo_empleado AS `Código`, e.nombres AS `Nombres`, a.unidad_organizativa AS `Unidad`,
           SUM(s.horas) AS `Horas extra`
    FROM sobretiempo s
    JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
    JOIN area a     ON a.codigo_area = e.codigo_area
    GROUP BY e.codigo_empleado, e.nombres, a.unidad_organizativa
    ORDER BY `Horas extra` DESC
    LIMIT 5;
END $$

-- =====================================================================
-- REPORTES (todos reciben: fecha desde, fecha hasta y código de empleado;
-- un valor NULL o vacío significa "sin filtro")
-- =====================================================================

-- R01. Horas extra por empleado y tipo de sobretiempo (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_empleado_tipo $$
CREATE PROCEDURE sp_reporte_empleado_tipo(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT e.codigo_empleado AS `Código`, e.nombres AS `Nombres`, s.codigo_cc_nomina AS `CC Nómina`,
           CONCAT(FORMAT(t.porcentaje_recargo, 0), ' %') AS `Recargo`, SUM(s.horas) AS `Total horas`
    FROM sobretiempo s
    JOIN empleado e         ON e.codigo_empleado = s.codigo_empleado
    JOIN tipo_sobretiempo t ON t.codigo_cc_nomina = s.codigo_cc_nomina
    WHERE (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY e.codigo_empleado, e.nombres, s.codigo_cc_nomina, t.porcentaje_recargo
    ORDER BY e.codigo_empleado, s.codigo_cc_nomina;
END $$

-- R02. Total de horas extra por empleado (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_total_empleado $$
CREATE PROCEDURE sp_reporte_total_empleado(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT e.codigo_empleado AS `Código`, e.nombres AS `Nombres`, e.puesto AS `Puesto`,
           SUM(CASE WHEN s.codigo_cc_nomina = '1250' THEN s.horas ELSE 0 END) AS `H25`,
           SUM(CASE WHEN s.codigo_cc_nomina = '1252' THEN s.horas ELSE 0 END) AS `H35`,
           SUM(CASE WHEN s.codigo_cc_nomina = '1260' THEN s.horas ELSE 0 END) AS `H100`,
           SUM(s.horas) AS `Total horas`
    FROM sobretiempo s
    JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
    WHERE (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY e.codigo_empleado, e.nombres, e.puesto
    ORDER BY `Total horas` DESC;
END $$

-- R03. Resumen de horas por tipo de sobretiempo (LEFT JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_resumen_tipo $$
CREATE PROCEDURE sp_reporte_resumen_tipo(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT t.codigo_cc_nomina AS `CC Nómina`, CONCAT(FORMAT(t.porcentaje_recargo, 0), ' %') AS `Recargo`,
           COUNT(s.fecha) AS `Registros`, COALESCE(SUM(s.horas), 0) AS `Total horas`
    FROM tipo_sobretiempo t
    LEFT JOIN sobretiempo s
           ON s.codigo_cc_nomina = t.codigo_cc_nomina
          AND (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
          AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY t.codigo_cc_nomina, t.porcentaje_recargo
    ORDER BY t.codigo_cc_nomina;
END $$

-- R04. Horas extra por centro de coste (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_centro_coste $$
CREATE PROCEDURE sp_reporte_centro_coste(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT cc.codigo_centro_coste AS `Código`, cc.centro_coste AS `Centro de coste`,
           COUNT(DISTINCT s.codigo_empleado) AS `Empleados`, SUM(s.horas) AS `Total horas`
    FROM sobretiempo s
    JOIN empleado e      ON e.codigo_empleado = s.codigo_empleado
    JOIN centro_coste cc ON cc.codigo_centro_coste = e.codigo_centro_coste
    WHERE (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY cc.codigo_centro_coste, cc.centro_coste
    ORDER BY `Total horas` DESC;
END $$

-- R05. Horas extra por unidad organizativa (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_unidad $$
CREATE PROCEDURE sp_reporte_unidad(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT a.codigo_area AS `Código`, a.unidad_organizativa AS `Unidad organizativa`,
           COUNT(DISTINCT s.codigo_empleado) AS `Empleados`, SUM(s.horas) AS `Total horas`
    FROM sobretiempo s
    JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
    JOIN area a     ON a.codigo_area = e.codigo_area
    WHERE (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY a.codigo_area, a.unidad_organizativa
    ORDER BY `Total horas` DESC;
END $$

-- R06. Empleados por puesto y unidad organizativa (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_puestos $$
CREATE PROCEDURE sp_reporte_puestos(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT e.puesto AS `Puesto`, a.unidad_organizativa AS `Unidad organizativa`,
           COUNT(*) AS `Empleados`
    FROM empleado e
    JOIN area a ON a.codigo_area = e.codigo_area
    WHERE p_empleado IS NULL OR p_empleado = '' OR e.codigo_empleado = p_empleado
    GROUP BY e.puesto, a.unidad_organizativa
    ORDER BY e.puesto, a.unidad_organizativa;
END $$

-- R07. Detalle diario de asistencia y sobretiempo (JOIN y LEFT JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_detalle_diario $$
CREATE PROCEDURE sp_reporte_detalle_diario(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT a.codigo_empleado AS `Código`, e.nombres AS `Nombres`, a.fecha AS `Fecha`,
           ELT(DAYOFWEEK(a.fecha), 'Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb') AS `Día`,
           a.codigo_turno AS `Turno`,
           TIME_FORMAT(a.marca_entrada, '%H:%i') AS `Entrada`,
           TIME_FORMAT(a.marca_salida, '%H:%i')  AS `Salida`,
           COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1250' THEN s.horas END), 0) AS `H25`,
           COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1252' THEN s.horas END), 0) AS `H35`,
           COALESCE(SUM(CASE WHEN s.codigo_cc_nomina = '1260' THEN s.horas END), 0) AS `H100`
    FROM asistencia a
    JOIN empleado e         ON e.codigo_empleado = a.codigo_empleado
    LEFT JOIN sobretiempo s ON s.codigo_empleado = a.codigo_empleado AND s.fecha = a.fecha
    WHERE (p_desde IS NULL OR a.fecha >= p_desde) AND (p_hasta IS NULL OR a.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR a.codigo_empleado = p_empleado)
    GROUP BY a.codigo_empleado, e.nombres, a.fecha, a.codigo_turno, a.marca_entrada, a.marca_salida
    ORDER BY a.codigo_empleado, a.fecha;
END $$

-- R08. Verificación del cálculo de H25, H35 y H100
DROP PROCEDURE IF EXISTS sp_reporte_verificacion $$
CREATE PROCEDURE sp_reporte_verificacion(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT v.codigo_empleado AS `Código`, v.fecha AS `Fecha`, v.codigo_turno AS `Turno`,
           TIME_FORMAT(v.marca_entrada, '%H:%i') AS `Entrada`,
           TIME_FORMAT(v.marca_salida, '%H:%i')  AS `Salida`,
           v.minutos_extra AS `Minutos extra`,
           v.h25_calculado AS `H25 calc.`, v.h25_registrado AS `H25 reg.`,
           v.h35_calculado AS `H35 calc.`, v.h35_registrado AS `H35 reg.`,
           v.h100_calculado AS `H100 calc.`, v.h100_registrado AS `H100 reg.`,
           v.resultado AS `Resultado`
    FROM v_verificacion_sobretiempo v
    WHERE (v.minutos_extra > 0 OR v.minutos_extra IS NULL)
      AND (p_desde IS NULL OR v.fecha >= p_desde) AND (p_hasta IS NULL OR v.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR v.codigo_empleado = p_empleado)
    ORDER BY v.fecha, v.codigo_empleado;
END $$

-- R09. Conciliación entre Registro_SAP y Sobretiempo (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_conciliacion $$
CREATE PROCEDURE sp_reporte_conciliacion(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT c.codigo_periodo AS `Periodo`, c.codigo_empleado AS `Código`, e.nombres AS `Nombres`,
           c.codigo_cc_nomina AS `CC Nómina`, c.horas_calculadas AS `Horas calculadas`,
           c.horas_registradas AS `Horas registradas`, c.estado AS `Estado`
    FROM v_conciliacion_sap c
    JOIN empleado e ON e.codigo_empleado = c.codigo_empleado
    JOIN periodo p  ON p.codigo_periodo = c.codigo_periodo
    WHERE (p_desde IS NULL OR p.fecha_fin >= p_desde) AND (p_hasta IS NULL OR p.fecha_inicio <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR c.codigo_empleado = p_empleado)
    ORDER BY c.codigo_periodo, c.codigo_empleado, c.codigo_cc_nomina;
END $$

-- R10. Horas cargadas a SAP por periodo y empleado (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_sap_periodo $$
CREATE PROCEDURE sp_reporte_sap_periodo(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT r.codigo_periodo AS `Periodo`, e.codigo_empleado AS `Código`, e.nombres AS `Nombres`,
           SUM(CASE WHEN r.codigo_cc_nomina = '1250' THEN r.horas_registradas ELSE 0 END) AS `1250`,
           SUM(CASE WHEN r.codigo_cc_nomina = '1252' THEN r.horas_registradas ELSE 0 END) AS `1252`,
           SUM(CASE WHEN r.codigo_cc_nomina = '1260' THEN r.horas_registradas ELSE 0 END) AS `1260`,
           SUM(r.horas_registradas) AS `Total cargado`, MAX(r.fecha_carga) AS `Fecha de carga`
    FROM registro_sap r
    JOIN empleado e ON e.codigo_empleado = r.codigo_empleado
    JOIN periodo p  ON p.codigo_periodo = r.codigo_periodo
    WHERE (p_desde IS NULL OR p.fecha_fin >= p_desde) AND (p_hasta IS NULL OR p.fecha_inicio <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR r.codigo_empleado = p_empleado)
    GROUP BY r.codigo_periodo, e.codigo_empleado, e.nombres
    ORDER BY r.codigo_periodo, `Total cargado` DESC;
END $$

-- R11. Empleados sin sobretiempo en el rango (subconsulta NOT EXISTS y JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_sin_sobretiempo $$
CREATE PROCEDURE sp_reporte_sin_sobretiempo(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT e.codigo_empleado AS `Código`, e.nombres AS `Nombres`, a.unidad_organizativa AS `Unidad`
    FROM empleado e
    JOIN area a ON a.codigo_area = e.codigo_area
    WHERE (p_empleado IS NULL OR p_empleado = '' OR e.codigo_empleado = p_empleado)
      AND NOT EXISTS (SELECT 1 FROM sobretiempo s
                      WHERE s.codigo_empleado = e.codigo_empleado
                        AND (p_desde IS NULL OR s.fecha >= p_desde)
                        AND (p_hasta IS NULL OR s.fecha <= p_hasta))
    ORDER BY e.codigo_empleado;
END $$

-- R12. Faltas y marcaciones incompletas
DROP PROCEDURE IF EXISTS sp_reporte_incompletas $$
CREATE PROCEDURE sp_reporte_incompletas(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT v.codigo_empleado AS `Código`, v.nombres AS `Nombres`, v.fecha AS `Fecha`,
           v.codigo_turno AS `Turno`, TIME_FORMAT(v.marca_entrada, '%H:%i') AS `Entrada`,
           TIME_FORMAT(v.marca_salida, '%H:%i') AS `Salida`, v.observacion AS `Observación`
    FROM v_asistencia_incompleta v
    WHERE (p_desde IS NULL OR v.fecha >= p_desde) AND (p_hasta IS NULL OR v.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR v.codigo_empleado = p_empleado)
    ORDER BY v.fecha, v.nombres;
END $$

-- R13. Horas extra por mes
DROP PROCEDURE IF EXISTS sp_reporte_mensual $$
CREATE PROCEDURE sp_reporte_mensual(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT DATE_FORMAT(s.fecha, '%Y-%m') AS `Mes`,
           SUM(CASE WHEN s.codigo_cc_nomina = '1250' THEN s.horas ELSE 0 END) AS `H25`,
           SUM(CASE WHEN s.codigo_cc_nomina = '1252' THEN s.horas ELSE 0 END) AS `H35`,
           SUM(CASE WHEN s.codigo_cc_nomina = '1260' THEN s.horas ELSE 0 END) AS `H100`,
           SUM(s.horas) AS `Total horas`
    FROM sobretiempo s
    WHERE (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY `Mes`
    ORDER BY `Mes`;
END $$

-- R14. Días con mayor cantidad de horas extra (JOIN)
DROP PROCEDURE IF EXISTS sp_reporte_dias_mayor $$
CREATE PROCEDURE sp_reporte_dias_mayor(IN p_desde DATE, IN p_hasta DATE, IN p_empleado CHAR(6))
BEGIN
    SELECT s.fecha AS `Fecha`,
           ELT(DAYOFWEEK(s.fecha), 'Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb') AS `Día`,
           COUNT(DISTINCT s.codigo_empleado) AS `Empleados`,
           GROUP_CONCAT(DISTINCT a.codigo_turno ORDER BY a.codigo_turno) AS `Turnos`,
           SUM(s.horas) AS `Total horas`
    FROM sobretiempo s
    JOIN asistencia a ON a.codigo_empleado = s.codigo_empleado AND a.fecha = s.fecha
    WHERE (p_desde IS NULL OR s.fecha >= p_desde) AND (p_hasta IS NULL OR s.fecha <= p_hasta)
      AND (p_empleado IS NULL OR p_empleado = '' OR s.codigo_empleado = p_empleado)
    GROUP BY s.fecha
    ORDER BY `Total horas` DESC, s.fecha
    LIMIT 10;
END $$

DELIMITER ;


-- =====================================================================
-- 2. INSERCIÓN DE DATOS
-- =====================================================================
USE sobretiempos;
START TRANSACTION;

-- Centros de coste (códigos y nombres tomados de la Figura 1)
INSERT INTO centro_coste (codigo_centro_coste, centro_coste) VALUES
('2A210612', 'Mnto Eléctrico'),
('2A210402', 'Línea 02 Pet'),
('2A210406', 'Línea 06 Agua 7/20 L'),
('2A210501', 'Gestión de Calidad'),
('2A110801', 'Soporte Funcional A'),
('2A210301', 'Línea 01');

-- Unidades organizativas
INSERT INTO area (codigo_area, unidad_organizativa) VALUES
('A001', 'Mantenimiento Eléctrico'),
('A002', 'Línea 1'),
('A003', 'Línea 2'),
('A004', 'Línea 6'),
('A005', 'Sostenibilidad'),
('A006', 'Sistemas');

-- Turnos programados (Figura 2). DES = descanso obligatorio, FER = feriado
INSERT INTO turno_programado (codigo_turno, hora_entrada_programada, hora_salida_programada) VALUES
('A10', '07:00:00', '15:00:00'),
('A18', '22:00:00', '06:00:00'),
('DES', '00:00:00', '00:00:00'),
('FER', '00:00:00', '00:00:00');

-- Tipos de sobretiempo (CC Nómina)
INSERT INTO tipo_sobretiempo (codigo_cc_nomina, porcentaje_recargo) VALUES
('1250', 25.00),
('1252', 35.00),
('1260', 100.00);

-- Periodos
INSERT INTO periodo (codigo_periodo, fecha_inicio, fecha_fin) VALUES
('202606', '2026-06-01', '2026-06-30'),
('202607', '2026-07-01', '2026-07-31');

-- Empleados (códigos de las Figuras 1 y 2; nombres y DNI de prueba)
INSERT INTO empleado (codigo_empleado, codigo_centro_coste, codigo_area, dni, nombres, puesto, subdivision) VALUES
('703117', '2A210612', 'A001', '70311701', 'MAMANI QUISPE, JORGE LUIS',    'MECANICO ELECTRICO',          'Arequipa'),
('703118', '2A210402', 'A003', '70311802', 'FLORES CHAVEZ, DIEGO ARMANDO', 'OPERARIO ROTATIVO DE LINEA',  'Arequipa'),
('703121', '2A210501', 'A005', '70312103', 'RAMOS CONDORI, MARIA ELENA',   'AUXILIAR DE OPERACIONES',     'Arequipa'),
('703123', '2A210406', 'A004', '70312304', 'HUAMAN SALAS, CARLOS ENRIQUE', 'OPERARIO ROTATIVO DE LINEA',  'Arequipa'),
('703124', '2A210406', 'A004', '70312405', 'CCAMA TORRES, LUIS MIGUEL',    'OPERARIO ROTATIVO DE LINEA',  'Arequipa'),
('703125', '2A210402', 'A003', '70312506', 'PEREZ VILCA, ANA LUCIA',       'OPERARIO ROTATIVO DE LINEA',  'Arequipa'),
('703127', '2A110801', 'A006', '70312707', 'QUISPE MAMANI, JOSE ANTONIO',  'ASISTENTE DE AUTOMATIZACION', 'Arequipa'),
('701863', '2A210301', 'A002', '42156558', 'GARCIA RIVERA, EDDY BENITO',   'OPERARIO ROTATIVO DE LINEA',  'Arequipa');

-- Asistencia de junio (escenarios de prueba)
INSERT INTO asistencia (codigo_empleado, fecha, codigo_turno, marca_entrada, marca_salida, centro_costo_provisional) VALUES
-- jornadas normales y sobretiempo menor a 120 minutos
('703117','2026-06-02','A10','06:50:00','15:40:00',NULL),
('703117','2026-06-03','A10','07:00:00','15:00:00',NULL),
('703117','2026-06-04','A10','07:05:00','17:30:00',NULL),   -- 150 min: 120 al 25 % y 30 al 35 %
('703118','2026-06-02','A10','07:00:00','16:00:00',NULL),
('703118','2026-06-03','A10','07:00:00','15:00:00',NULL),
('703118','2026-06-04','A10',NULL,NULL,NULL),               -- falta
('703118','2026-06-05','A10','07:00:00','20:00:00',NULL),   -- 300 min: 120 / 120 / 60
('703121','2026-06-02','A10','07:00:00','15:00:00',NULL),
('703121','2026-06-03','A10','07:00:00','15:30:00',NULL),
('703121','2026-06-04','A10','07:00:00','15:00:00',NULL),
('703121','2026-06-07','DES','08:00:00','12:30:00',NULL),   -- trabajo en descanso: todo al 100 %
('703123','2026-06-02','A10','06:45:00','15:15:00',NULL),
('703123','2026-06-03','A10','07:00:00','15:00:00',NULL),
('703123','2026-06-04','A10','07:00:00','16:30:00',NULL),
('703123','2026-06-05','A10','07:00:00',NULL,NULL),         -- marcación incompleta
('703124','2026-06-02','A10','07:00:00','15:00:00',NULL),
('703124','2026-06-03','A10','07:00:00','15:45:00',NULL),
('703124','2026-06-04','A10','07:00:00','15:00:00',NULL),
('703124','2026-06-05','A18','21:30:00','08:00:00',NULL),   -- nocturno: 30 + 120 = 150 min
('703125','2026-06-02','A10','07:00:00','15:20:00',NULL),
('703125','2026-06-03','A10','07:00:00','15:00:00',NULL),
('703125','2026-06-04','A10','06:30:00','15:00:00',NULL),
('703127','2026-06-02','A10','07:00:00','15:00:00',NULL),
('703127','2026-06-03','A10','07:00:00','15:00:00',NULL),
('703127','2026-06-04','A10','07:00:00','15:10:00',NULL),
('703127','2026-06-29','FER','07:00:00','15:00:00',NULL);   -- feriado trabajado: 480 min al 100 %

-- Asistencia de julio del trabajador 701863: datos reales del Reporte de
-- Asistencia Detallado (Figura 2). Su descanso rotativo es el lunes.
INSERT INTO asistencia (codigo_empleado, fecha, codigo_turno, marca_entrada, marca_salida, centro_costo_provisional) VALUES
('701863','2026-07-02','A10','06:27:00','15:24:00',NULL),
('701863','2026-07-03','A10','07:00:00','15:23:00',NULL),
('701863','2026-07-04','A10',NULL,NULL,NULL),
('701863','2026-07-05','A10','06:36:00','15:31:00',NULL),
('701863','2026-07-06','DES',NULL,NULL,NULL),
('701863','2026-07-07','A18','21:16:00','06:20:00',NULL),
('701863','2026-07-08','A18','21:25:00','06:22:00',NULL),
('701863','2026-07-09','A18','21:44:00','06:11:00',NULL),
('701863','2026-07-10','A18','21:15:00','06:15:00',NULL),
('701863','2026-07-11','A18','21:28:00','06:23:00',NULL),
('701863','2026-07-12','A18',NULL,NULL,NULL),
('701863','2026-07-13','DES',NULL,NULL,NULL),
('701863','2026-07-14','A10','06:35:00','15:17:00',NULL),
('701863','2026-07-15','A10','06:16:00','15:20:00',NULL),
('701863','2026-07-16','A10','06:47:00','15:19:00',NULL),
('701863','2026-07-17','A10','06:35:00','15:06:00',NULL),
('701863','2026-07-18','A10',NULL,NULL,NULL);

COMMIT;

-- Consolidación para SAP (simulación de la carga mediante la transacción PA70)
CALL sp_consolidar_periodo('202606', '2026-07-05');
CALL sp_consolidar_periodo('202607', '2026-08-05');

-- =====================================================================
-- 3. CONSULTAS
-- =====================================================================
USE sobretiempos;
SET lc_time_names = 'es_ES';

-- Consulta 1. Horas extra por empleado y tipo en el periodo 202606
SELECT e.codigo_empleado, e.nombres,
       s.codigo_cc_nomina, t.porcentaje_recargo,
       SUM(s.horas) AS total_horas
FROM sobretiempo s
JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
JOIN tipo_sobretiempo t ON t.codigo_cc_nomina = s.codigo_cc_nomina
WHERE s.fecha BETWEEN '2026-06-01' AND '2026-06-30'
GROUP BY e.codigo_empleado, e.nombres, s.codigo_cc_nomina, t.porcentaje_recargo
ORDER BY e.codigo_empleado, s.codigo_cc_nomina;

-- Consulta 2. Total de horas extra por empleado
SELECT e.codigo_empleado, e.nombres, SUM(s.horas) AS total_horas_extra
FROM sobretiempo s
JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
GROUP BY e.codigo_empleado, e.nombres
ORDER BY total_horas_extra DESC;

-- Consulta 3. Resumen de horas por tipo de sobretiempo
SELECT t.codigo_cc_nomina, t.porcentaje_recargo,
       COALESCE(SUM(s.horas), 0) AS total_horas
FROM tipo_sobretiempo t
LEFT JOIN sobretiempo s ON s.codigo_cc_nomina = t.codigo_cc_nomina
GROUP BY t.codigo_cc_nomina, t.porcentaje_recargo
ORDER BY t.codigo_cc_nomina;

-- Consulta 4. Horas extra por centro de coste
SELECT cc.codigo_centro_coste, cc.centro_coste, SUM(s.horas) AS total_horas_extra
FROM sobretiempo s
JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
JOIN centro_coste cc ON cc.codigo_centro_coste = e.codigo_centro_coste
GROUP BY cc.codigo_centro_coste, cc.centro_coste
ORDER BY total_horas_extra DESC;

-- Consulta 5. Horas extra por unidad organizativa
SELECT a.unidad_organizativa, SUM(s.horas) AS total_horas_extra
FROM sobretiempo s
JOIN empleado e ON e.codigo_empleado = s.codigo_empleado
JOIN area a ON a.codigo_area = e.codigo_area
GROUP BY a.unidad_organizativa
ORDER BY total_horas_extra DESC;

-- Consulta 6. Puestos por unidad organizativa
SELECT e.puesto, a.unidad_organizativa, COUNT(*) AS empleados
FROM empleado e
JOIN area a ON a.codigo_area = e.codigo_area
GROUP BY e.puesto, a.unidad_organizativa
ORDER BY e.puesto, a.unidad_organizativa;

-- Consulta 7. Detalle diario de asistencia de un empleado
SELECT a.fecha, DAYNAME(a.fecha) AS dia, a.codigo_turno,
       a.marca_entrada, a.marca_salida,
       COALESCE(SUM(s.horas), 0) AS horas_extra
FROM asistencia a
LEFT JOIN sobretiempo s ON s.codigo_empleado = a.codigo_empleado AND s.fecha = a.fecha
WHERE a.codigo_empleado = '701863'
GROUP BY a.fecha, a.codigo_turno, a.marca_entrada, a.marca_salida
ORDER BY a.fecha;

-- Consulta 8. Verificación del cálculo de H25, H35 y H100 (incluye turnos nocturnos)
SELECT codigo_empleado, fecha, codigo_turno, marca_entrada, marca_salida, minutos_extra,
       h25_calculado, h25_registrado, h35_calculado, h35_registrado,
       h100_calculado, h100_registrado, resultado
FROM v_verificacion_sobretiempo
WHERE minutos_extra > 0 OR minutos_extra IS NULL
ORDER BY fecha, codigo_empleado;

-- Consulta 9. Trazabilidad entre Registro_SAP y Sobretiempo
SELECT codigo_empleado, codigo_cc_nomina, codigo_periodo,
       horas_calculadas, horas_registradas, fecha_carga, estado
FROM v_conciliacion_sap
ORDER BY codigo_periodo, codigo_empleado, codigo_cc_nomina;

-- Consulta 10. Horas cargadas a SAP por periodo
SELECT r.codigo_periodo, e.nombres, SUM(r.horas_registradas) AS horas_cargadas
FROM registro_sap r
JOIN empleado e ON e.codigo_empleado = r.codigo_empleado
GROUP BY r.codigo_periodo, e.nombres
ORDER BY r.codigo_periodo, horas_cargadas DESC;

-- Consulta 11. Empleados sin sobretiempo en el periodo 202606
SELECT e.codigo_empleado, e.nombres
FROM empleado e
WHERE NOT EXISTS (
    SELECT 1 FROM sobretiempo s
    WHERE s.codigo_empleado = e.codigo_empleado
      AND s.fecha BETWEEN '2026-06-01' AND '2026-06-30');

-- Consulta 12. Faltas y marcaciones incompletas (para revisión manual)
SELECT nombres, fecha, codigo_turno, marca_entrada, marca_salida, observacion
FROM v_asistencia_incompleta
ORDER BY fecha, nombres;

-- Consulta 13. Horas extra por mes
SELECT DATE_FORMAT(fecha, '%Y-%m') AS anio_mes, SUM(horas) AS total_horas_extra
FROM sobretiempo
GROUP BY anio_mes
ORDER BY anio_mes;

-- Consulta 14. Días con mayor cantidad de horas extra
SELECT fecha, DAYNAME(fecha) AS dia, SUM(horas) AS total_horas_extra
FROM sobretiempo
GROUP BY fecha
ORDER BY total_horas_extra DESC
LIMIT 5;
