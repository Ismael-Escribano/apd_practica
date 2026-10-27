-- =====================================================================
-- Almacén de datos: Turismo en España por Comunidad Autónoma
-- Apartado 3 (diseño físico) - Adquisición y preparación de datos
-- Motor: MySQL 8 (compatible con MariaDB 10.x)
-- Modelo: ESQUEMA EN ESTRELLA con una única tabla de hechos
--         (fact_ocupacion) y 6 dimensiones.
-- =====================================================================

DROP DATABASE IF EXISTS turismo_dw;
CREATE DATABASE turismo_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE turismo_dw;

-- ---------------------------------------------------------------------
-- DIMENSIONES (atributos descriptivos y categóricos)
-- ---------------------------------------------------------------------

-- Tiempo: granularidad mensual. Clave inteligente AAAAMM (p. ej. 202403)
CREATE TABLE dim_tiempo (
  tiempo_key  INT          NOT NULL COMMENT 'AAAAMM',
  anio        SMALLINT     NOT NULL,
  mes         TINYINT      NOT NULL,
  nombre_mes  VARCHAR(12)  NOT NULL,
  trimestre   TINYINT      NOT NULL,
  temporada   VARCHAR(5)   NOT NULL COMMENT 'Alta / Media / Baja (regla derivada, ver memoria)',
  PRIMARY KEY (tiempo_key),
  UNIQUE KEY uq_tiempo_anio_mes (anio, mes),
  CONSTRAINT ck_tiempo_mes  CHECK (mes BETWEEN 1 AND 12),
  CONSTRAINT ck_tiempo_trim CHECK (trimestre BETWEEN 1 AND 4)
) ENGINE=InnoDB;

-- Comunidad / ciudad autónoma (19 filas): perfil estable del territorio.
-- Incluye la población de referencia (INE) y el patrimonio (Wikidata)
-- como descriptores, junto con su categoría obtenida por discretización.
CREATE TABLE dim_ccaa (
  ccaa_key                     INT          NOT NULL AUTO_INCREMENT,
  codigo_ine                   CHAR(2)      NOT NULL COMMENT 'Código INE 01-19',
  codigo_iso                   VARCHAR(5)   NULL     COMMENT 'ISO 3166-2, p. ej. ES-AN',
  nombre                       VARCHAR(80)  NOT NULL,
  wikidata_qid                 VARCHAR(15)  NULL,
  latitud                      DECIMAL(9,6) NULL,
  longitud                     DECIMAL(9,6) NULL,
  habitantes_ref               INT UNSIGNED NULL     COMMENT 'Población de referencia (INE, ECP)',
  poblacion_fecha_ref          DATE         NULL     COMMENT 'Fecha a la que se refiere la población',
  nivel_poblacion              VARCHAR(10)  NULL     COMMENT 'Muy grande / Grande / Mediana / Pequeña',
  n_bic                        INT UNSIGNED NULL     COMMENT 'Bienes de Interés Cultural en Wikidata',
  nivel_patrimonio             VARCHAR(5)   NULL     COMMENT 'Alto / Medio / Bajo',
  patrimonio_fecha_extraccion  DATE         NULL,
  PRIMARY KEY (ccaa_key),
  UNIQUE KEY uq_ccaa_codigo_ine (codigo_ine)
) ENGINE=InnoDB;

-- Tipo de alojamiento: viene dado por la encuesta INE de origen
CREATE TABLE dim_tipo_alojamiento (
  tipo_key      TINYINT      NOT NULL AUTO_INCREMENT,
  codigo        CHAR(3)      NOT NULL COMMENT 'HOT, APT, CAM, RUR',
  nombre        VARCHAR(40)  NOT NULL,
  encuesta_ine  VARCHAR(5)   NOT NULL COMMENT 'EOH, EOAP, EOAC, EOTR',
  grupo         VARCHAR(15)  NOT NULL COMMENT 'Hotelero / Extrahotelero',
  PRIMARY KEY (tipo_key),
  UNIQUE KEY uq_tipo_codigo (codigo)
) ENGINE=InnoDB;

-- Origen (residencia) del viajero. Solo se cargan los niveles más bajos
-- (ESP y EXT) para que las medidas sean aditivas: el total del INE se usa
-- como control en el ETL (TOT = ESP + EXT), no como fila de la tabla de hechos.
CREATE TABLE dim_origen (
  origen_key  TINYINT      NOT NULL AUTO_INCREMENT,
  codigo      CHAR(3)      NOT NULL COMMENT 'ESP, EXT',
  nombre      VARCHAR(40)  NOT NULL,
  PRIMARY KEY (origen_key),
  UNIQUE KEY uq_origen_codigo (codigo)
) ENGINE=InnoDB;

-- Nivel de estancia: discretización (binning) de la estancia media
CREATE TABLE dim_nivel_estancia (
  nivel_key  TINYINT      NOT NULL,
  nombre     VARCHAR(10)  NOT NULL COMMENT 'Corta / Media / Larga / Sin dato',
  min_dias   DECIMAL(4,1) NULL,
  max_dias   DECIMAL(4,1) NULL,
  PRIMARY KEY (nivel_key),
  UNIQUE KEY uq_nivel_nombre (nombre)
) ENGINE=InnoDB;

-- Calidad del dato (dimensión "basura"): marcas del proceso de limpieza
CREATE TABLE dim_calidad_dato (
  calidad_key    TINYINT      NOT NULL,
  descripcion    VARCHAR(30)  NOT NULL,
  dato_imputado  TINYINT(1)   NOT NULL,
  es_atipico     TINYINT(1)   NOT NULL,
  PRIMARY KEY (calidad_key),
  UNIQUE KEY uq_calidad_desc (descripcion)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- TABLA DE HECHOS (solo claves ajenas + medidas numéricas)
-- Grano: 1 fila por mes x CCAA x tipo de alojamiento x origen
-- Clave primaria: compuesta por las claves de TODAS las dimensiones (convención
-- de la asignatura). Como nivel_key y calidad_key dependen de las otras cuatro,
-- el grano se garantiza además con una restricción UNIQUE sobre esas cuatro.
-- ---------------------------------------------------------------------
CREATE TABLE fact_ocupacion (
  tiempo_key      INT           NOT NULL,
  ccaa_key        INT           NOT NULL,
  tipo_key        TINYINT       NOT NULL,
  origen_key      TINYINT       NOT NULL,
  nivel_key       TINYINT       NOT NULL DEFAULT 4,
  calidad_key     TINYINT       NOT NULL DEFAULT 1,
  viajeros        INT UNSIGNED  NULL,
  pernoctaciones  INT UNSIGNED  NULL,
  estancia_media  DECIMAL(6,2)  NULL COMMENT 'Derivada: pernoctaciones / viajeros',
  PRIMARY KEY (tiempo_key, ccaa_key, tipo_key, origen_key, nivel_key, calidad_key),
  UNIQUE KEY uq_fo_grano (tiempo_key, ccaa_key, tipo_key, origen_key),
  KEY ix_fo_ccaa    (ccaa_key),
  KEY ix_fo_tipo    (tipo_key),
  KEY ix_fo_origen  (origen_key),
  KEY ix_fo_nivel   (nivel_key),
  KEY ix_fo_calidad (calidad_key),
  CONSTRAINT fk_fo_tiempo  FOREIGN KEY (tiempo_key)  REFERENCES dim_tiempo (tiempo_key),
  CONSTRAINT fk_fo_ccaa    FOREIGN KEY (ccaa_key)    REFERENCES dim_ccaa (ccaa_key),
  CONSTRAINT fk_fo_tipo    FOREIGN KEY (tipo_key)    REFERENCES dim_tipo_alojamiento (tipo_key),
  CONSTRAINT fk_fo_origen  FOREIGN KEY (origen_key)  REFERENCES dim_origen (origen_key),
  CONSTRAINT fk_fo_nivel   FOREIGN KEY (nivel_key)   REFERENCES dim_nivel_estancia (nivel_key),
  CONSTRAINT fk_fo_calidad FOREIGN KEY (calidad_key) REFERENCES dim_calidad_dato (calidad_key)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- DATOS ESTÁTICOS DE LAS DIMENSIONES PEQUEÑAS
-- (dim_tiempo y dim_ccaa se cargan desde Pentaho)
-- ---------------------------------------------------------------------
INSERT INTO dim_tipo_alojamiento (codigo, nombre, encuesta_ine, grupo) VALUES
  ('HOT', 'Hotel',                 'EOH',  'Hotelero'),
  ('APT', 'Apartamento turístico', 'EOAP', 'Extrahotelero'),
  ('CAM', 'Camping',               'EOAC', 'Extrahotelero'),
  ('RUR', 'Turismo rural',         'EOTR', 'Extrahotelero');

INSERT INTO dim_origen (codigo, nombre) VALUES
  ('ESP', 'Residentes en España'),
  ('EXT', 'Residentes en el extranjero');

-- Cortes iniciales del binning (revisables tras ver la distribución real)
INSERT INTO dim_nivel_estancia (nivel_key, nombre, min_dias, max_dias) VALUES
  (1, 'Corta',    0.0, 2.0),
  (2, 'Media',    2.0, 4.0),
  (3, 'Larga',    4.0, NULL),
  (4, 'Sin dato', NULL, NULL);

INSERT INTO dim_calidad_dato (calidad_key, descripcion, dato_imputado, es_atipico) VALUES
  (1, 'Dato original',        0, 0),
  (2, 'Dato imputado',        1, 0),
  (3, 'Valor atípico',        0, 1),
  (4, 'Imputado y atípico',   1, 1);

-- ---------------------------------------------------------------------
-- VISTAS DE APOYO
-- ---------------------------------------------------------------------
-- Total por mes, CCAA y tipo: suma de residentes en España y en el extranjero
CREATE VIEW v_ocupacion_total AS
SELECT tiempo_key, ccaa_key, tipo_key,
       SUM(viajeros)       AS viajeros,
       SUM(pernoctaciones) AS pernoctaciones
FROM fact_ocupacion
GROUP BY tiempo_key, ccaa_key, tipo_key;

-- Pernoctaciones por habitante y año (con la población de referencia)
CREATE VIEW v_ocupacion_anual_ccaa AS
SELECT t.anio, c.ccaa_key, c.codigo_ine, c.nombre,
       SUM(v.viajeros)       AS viajeros,
       SUM(v.pernoctaciones) AS pernoctaciones,
       ROUND(SUM(v.pernoctaciones) / NULLIF(c.habitantes_ref, 0), 2) AS pernoctaciones_por_habitante
FROM v_ocupacion_total v
JOIN dim_tiempo t ON t.tiempo_key = v.tiempo_key
JOIN dim_ccaa   c ON c.ccaa_key   = v.ccaa_key
GROUP BY t.anio, c.ccaa_key, c.codigo_ine, c.nombre, c.habitantes_ref;