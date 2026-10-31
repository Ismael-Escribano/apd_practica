# Turismo en España por Comunidad Autónoma: almacén de datos y ETL

Proyecto de la asignatura **Adquisición y preparación de datos**
Grado en Ingeniería en Inteligencia Artificial · Escuela Politécnica Superior · Universidad de Alicante · Curso 2026-27

**Autores:** _(J, S, P, I)_
**Fecha de entrega:** 11 de diciembre de 2026

---

## Índice

1. [Resumen](#1-resumen)
2. [Apartado 1: Temática, problema y objetivos](#2-apartado-1-temática-problema-y-objetivos)
3. [Apartado 2: Análisis y selección de datos](#3-apartado-2-análisis-y-selección-de-datos)
4. [Apartado 3: Diseño del almacén de datos](#4-apartado-3-diseño-del-almacén-de-datos)
5. [Apartado 4: Extracción, limpieza y carga (Pentaho)](#5-apartado-4-extracción-limpieza-y-carga-pentaho)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Cómo reproducir el trabajo](#7-cómo-reproducir-el-trabajo)
8. [Estado del proyecto](#8-estado-del-proyecto)
9. [Fuentes y referencias](#9-fuentes-y-referencias)
10. [Licencia](#10-licencia)

---

## 1. Resumen

El proyecto integra estadísticas oficiales de ocupación turística de España (hoteles, apartamentos turísticos, campings y turismo rural), desagregadas por **Comunidad Autónoma (CCAA)** y mes, en un **almacén de datos MySQL**. Los datos se extraen, limpian, transforman y cargan con **Pentaho Data Integration (PDI)** y se enriquecen con **Wikidata** (identificadores, coordenadas y patrimonio cultural) y con los límites administrativos oficiales del **CNIG/IGN**.

El objetivo final es poder comparar la demanda turística entre territorios, relacionarla con la población y con el patrimonio cultural reconocido, publicar los datos como tripletas **schema.org** y visualizarlos en mapas y gráficas.

---

## 2. Apartado 1: Temática, problema y objetivos

### Temática
**Turismo**: demanda y oferta turística en España, analizada de forma comparativa entre Comunidades Autónomas.

### Problema
No existe una visión integrada, actualizada y comparable de cómo se distribuye la demanda turística entre las CCAA, ni de cómo esa distribución se relaciona con el tipo de alojamiento, el perfil del turista (procedencia) y la riqueza patrimonial de cada territorio. Esto dificulta la planificación turística, tanto pública como privada.

### Preguntas de investigación
1. ¿Cómo se distribuye la demanda turística (pernoctaciones, ocupación, estancia media) entre las CCAA y qué papel juega el tipo de alojamiento (hotel, apartamento, camping, turismo rural)?
2. ¿Ha cambiado la composición de la demanda (turista residente en España frente a residente en el extranjero) por CCAA en los últimos años?
3. ¿Las CCAA con más patrimonio cultural reconocido concentran también más demanda turística?

### Lienzo del problema (4W)

| | |
|---|---|
| **Who** | Administraciones turísticas (Ministerio de Industria, Comercio y Turismo y consejerías autonómicas), sector empresarial (hoteles, apartamentos, campings, turismo rural), investigadores y analistas, turistas y ciudadanía |
| **What** | No existe una herramienta abierta y unificada que permita comparar la evolución de la demanda turística entre CCAA y tipos de alojamiento, ni relacionarla con la oferta cultural de cada territorio |
| **Where** | España, por Comunidad Autónoma (17 CCAA + Ceuta y Melilla), con un horizonte de aproximadamente los últimos 10 años, según la cobertura real de los datos |
| **Why** | Facilitar la planificación turística y la asignación de recursos (infraestructuras, promoción, desestacionalización); ayudar al sector privado a detectar oportunidades por región y tipo de alojamiento; dar transparencia al fenómeno turístico |

### Objetivos
1. Integrar y homogeneizar en un almacén de datos las principales estadísticas oficiales de ocupación turística (EOH, EOAP, EOAC, EOTR), por CCAA y periodo.
2. Enriquecer los datos con información semántica y geográfica externa (Wikidata, CNIG).
3. Representar los datos con el vocabulario schema.org para facilitar su reutilización.
4. Generar visualizaciones que respondan a las preguntas de investigación.

### Casos de uso
1. Un técnico de una consejería de turismo consulta la evolución de pernoctaciones de su CCAA por tipo de alojamiento para justificar una campaña de promoción fuera de temporada alta.
2. Una empresa hotelera analiza en qué CCAA ha crecido más la demanda de apartamentos o turismo rural para valorar una expansión.
3. Un ciudadano o periodista de datos compara, en un mapa interactivo, qué comunidades reciben más turismo en relación con su patrimonio cultural.
4. Un tercero reutiliza las tripletas schema.org publicadas en otro proyecto de datos abiertos.

### Métricas clave
- Nº de pernoctaciones y viajeros (totales y por tipo de alojamiento), por CCAA y periodo.
- Estancia media (días) por CCAA.
- Grado de ocupación (%) por CCAA y tipo de alojamiento.
- % de viajeros residentes en España frente a residentes en el extranjero, por CCAA.
- Nº de Bienes de Interés Cultural (BIC) por CCAA, como indicador de oferta cultural.
- Pernoctaciones por habitante (con la población de referencia de cada CCAA).
- % de registros sin valores perdidos tras la limpieza (métrica de calidad del ETL).

---

## 3. Apartado 2: Análisis y selección de datos

### Necesidades de datos

| Necesidad | Tipo | Formato |
|---|---|---|
| Viajeros, pernoctaciones y estancia media (P1) | Cuantitativo, serie temporal mensual | CSV / JSON |
| Procedencia del viajero: residente en España o en el extranjero (P2) | Categórico | CSV / JSON |
| Tipo de alojamiento (P1) | Categórico (determinado por la encuesta de origen) | CSV / JSON |
| Patrimonio cultural por CCAA (P3) | Conteo de entidades enlazadas | SPARQL → JSON/CSV |
| Población por CCAA (normalización por habitante) | Cuantitativo (valor de referencia más reciente) | CSV |
| Geometría de las CCAA (mapa) | Geoespacial | Shapefile / GeoJSON |

### Requisitos de calidad
- **Oficialidad:** fuente institucional y citable.
- **Granularidad:** CCAA × mes.
- **Cobertura temporal:** al menos 10 años.
- **Homogeneidad:** códigos y nombres de CCAA conciliables entre fuentes (se resuelve en el ETL).
- **Licencia abierta** y reutilizable.
- **Trazabilidad:** identificador de tabla y fecha de descarga documentados.

**Datos ficticios:** no se utilizan. Todos los datos proceden de fuentes reales.

### Fuentes analizadas

| Fuente | Decisión | Motivo |
|---|---|---|
| TData (portal de turismo de la UA) | Descartada | Servidor no disponible durante un periodo prolongado, riesgo para la entrega |
| Portales de datos abiertos regionales (GVA, Ayuntamiento de Alicante) | Descartadas | Cobertura regional, no comparable entre todas las CCAA |
| **INE** | **Elegida** | Oficial, estable, CCAA homogéneas, descarga CSV y API |
| **Wikidata** | **Elegida** | Enriquecimiento semántico y geográfico (requisito del apartado 5) |
| **CNIG / IGN** | **Elegida** | Límites administrativos oficiales para el mapa |

> El enfoque inicial se centraba en Alicante. Se amplió a todas las CCAA para trabajar con fuentes oficiales, estables y comparables.

### Datasets seleccionados

| ID | Dataset | Pregunta | Enlace |
|---|---|---|---|
| D1 | Encuesta de Ocupación Hotelera (EOH): viajeros y pernoctaciones por CCAA y provincias · API 67190 | P1, P2 | [INE t=67190](https://www.ine.es/jaxiT3/Tabla.htm?t=67190) · [catálogo datos.gob.es](https://datos.gob.es/es/catalogo/ea0042823-viajeros-y-pernoctaciones-por-comunidades-autonomas-y-provincias-eoh-identificador-api-67190) |
| D2 | Encuesta de Ocupación en Apartamentos Turísticos (EOAP): viajeros y pernoctaciones por CCAA · API 67191 | P1, P2 | [INE t=67191](https://www.ine.es/jaxiT3/Tabla.htm?t=67191) · [catálogo](https://datos.gob.es/gl/catalogo/ea0042823-viajeros-y-pernoctaciones-por-comunidades-autonomas-eoap-identificador-api-67191) |
| D3 | Encuesta de Ocupación en Campings (EOAC): viajeros y pernoctaciones por CCAA · API 67192 | P1, P2 | [INE t=67192](https://www.ine.es/jaxiT3/Tabla.htm?t=67192) · [catálogo](https://datos.gob.es/gl/catalogo/ea0042823-viajeros-y-pernoctaciones-por-comunidades-autonomas-eoac-identificador-api-67192) |
| D4 | Encuesta de Ocupación en Alojamientos de Turismo Rural (EOTR): viajeros y pernoctaciones por CCAA · API 67193 | P1, P2 | [INE t=67193](https://www.ine.es/jaxiT3/Tabla.htm?t=67193) · [catálogo](https://datos.gob.es/es/catalogo/ea0042823-viajeros-y-pernoctaciones-por-comunidades-y-ciudades-autonomas-eotr-identificador-api-67193) |
| D5 | Estadística Continua de Población (ECP): población residente por fecha, sexo, nacionalidad y lugar de nacimiento, CCAA y ciudades autónomas · API 56944 (alternativa: API 59238, por fecha, sexo y edad) | per cápita | [Catálogo datos.gob.es](https://datos.gob.es/en/catalogo/ea0042823-poblacion-residente-por-fecha-sexo-nacionalidad-agrupacion-de-paises-y-lugar-de-nacimiento-agrupacion-de-paises-ecp-identificador-api-56944) · [Metadatos de la operación](https://ine.es/dynt3/metadatos/es/RespuestaDatos.html?oe=30282) |
| D6 | Límites administrativos de las CCAA (CNIG/IGN) | mapa | [Centro de Descargas CNIG](https://centrodedescargas.cnig.es/CentroDescargas/index.jsp) · [WFS INSPIRE](https://www.ign.es/wfs-inspire/unidades-administrativas?request=GetCapabilities&service=WFS) |
| D7 | CCAA y Bienes de Interés Cultural en Wikidata | P3 | [Wikidata Query Service](https://query.wikidata.org/) · [endpoint SPARQL](https://query.wikidata.org/sparql) |

Punto de entrada a todas las estadísticas de turismo del INE: [INEbase, Hostelería y turismo](https://www.ine.es/dyngs/INEbase/es/categoria.htm?c=Estadistica_P&cid=1254735576863).

### Cómo obtener los datos

Los ficheros descargados se guardan en `data/raw/`. Las descargas automáticas (INE y Wikidata) se hacen con un único script y dejan un registro con URL, fecha, tamaño y huella SHA-256 en `data/raw/_descargas.log.csv`:

```bash
python scripts/descargar_fuentes.py              # ocupación y población (INE) + Wikidata
python scripts/descargar_fuentes.py --solo ine   # también: poblacion, ccaa, bic
python scripts/descargar_fuentes.py --dry-run    # solo muestra las URL y consultas
```

El script no repite lo que ya está descargado (`--forzar` para repetirlo). Wikidata limita las peticiones, así que la consulta de patrimonio se hace por lotes con una pausa de un minuto entre ellos y, si se interrumpe, al volver a ejecutarla continúa donde lo dejó.

**INE (D1 a D4).** Cada tabla se descarga por su identificador de API. Formato: CSV separado por `;`, decimales con coma, UTF-8 (con BOM al inicio) y una fila por valor.

| Acceso | Patrón |
|---|---|
| CSV (API de INEbase) | `https://ine.es/wstempus/csv_sc/es/DATOS_TABLA/{ID}` |
| CSV (descarga de la tabla) | `https://www.ine.es/jaxiT3/files/t/csv_bdsc/{ID}.csv` |
| JSON | `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{ID}` |
| Vista web | `https://www.ine.es/jaxiT3/Tabla.htm?t={ID}` o, para tablas del sistema anterior, `https://www.ine.es/jaxi/Tabla.htm?tpx={ID}` |

**INE, población (D5).** La tabla 56944 se descarga con el script (`--solo poblacion`) y se guarda comprimida en `.zip` (unos 82 MB sin comprimir). Columnas: `Sexo; Comunidades y ciudades autónomas; Nacionalidad; País de Nacimiento; Periodo; Total`. Los periodos son trimestrales y están escritos en texto (`1 de enero de 2025`, `1 de octubre de 2024`). La población total de cada territorio es la fila con Sexo, Nacionalidad y País de Nacimiento iguales a "Total"; de ellas se conserva la de **1 de enero más reciente** como población de referencia. En Pentaho, *Text file input* lee el fichero comprimido (pestaña *Content*, desplegable *Compression*). Para descomprimirlo a mano: `unzip data/raw/ine_56944_*.zip -d data/raw/`. Alternativa manual: la tabla 59238 (por sexo y edad) desde la vista web (`https://www.ine.es/jaxiT3/Tabla.htm?t=59238`), seleccionando todas las CCAA, sexo **Total**, edad **Todas las edades** y los periodos de 1 de enero, en formato **CSV separado por ;**.

**CNIG (D6).** En el [Centro de Descargas](https://centrodedescargas.cnig.es/CentroDescargas/index.jsp), producto *Límites municipales, provinciales y autonómicos*, se descarga **Límites y Unidades Administrativas Actuales (Shapefile)**, que contiene la Base de Datos de Divisiones Administrativas de España. Del zip solo se usan las dos capas de recintos autonómicos, que se copian a `data/raw/cnig/`:

| Carpeta del zip | Cobertura | Sistema |
|---|---|---|
| `SHP_ETRS89/recintos_autonomicas_inspire_peninbal_etrs89` | Península, Baleares, Ceuta y Melilla | ETRS89, coordenadas geográficas |
| `SHP_WGS84/recintos_autonomicas_inspire_canarias_wgs84` | Canarias | REGCAN95 (compatible con WGS84), coordenadas geográficas |

Atributos relevantes: `NAMEUNIT` (nombre), `NATCODE` (código nacional), `CODNUT1`-`CODNUT3` (regiones NUTS) y `NATLEVNAME`. Ambas capas están en longitud/latitud compatibles con WGS84, por lo que no se reproyectan. El zip original (unos 157 MB) no se incluye en el repositorio por superar el límite de GitHub. El script `scripts/preparar_geometrias.py` (requiere `pip install pyshp shapely`) une las dos capas, asigna a cada CCAA su código INE, simplifica la geometría y genera `data/clean/ccaa.geojson`, que usan el ETL y las visualizaciones. El shapefile incluye un recinto adicional (*Territorios no asociados a ninguna autonomía*) que el script descarta; el GeoJSON resultante tiene 19 entidades y pesa 1,1 MB.

**Wikidata (D7).** Las dos consultas siguientes se ejecutan en el [Wikidata Query Service](https://query.wikidata.org/) (botón *Download → CSV file* sobre los resultados) o con el script. Se identifican las CCAA por su código ISO 3166-2, de modo que incluyen también Ceuta y Melilla.

```sparql
# CCAA con QID, código ISO y coordenadas (19 filas)
SELECT ?ccaa ?ccaaLabel ?iso ?coord WHERE {
  VALUES ?iso { "ES-AN" "ES-AR" "ES-AS" "ES-IB" "ES-CN" "ES-CB" "ES-CL" "ES-CM" "ES-CT" "ES-VC"
                "ES-EX" "ES-GA" "ES-MD" "ES-MC" "ES-NC" "ES-PV" "ES-RI" "ES-CE" "ES-ML" }
  ?ccaa wdt:P300 ?iso ;
        wdt:P17 wd:Q29 .
  OPTIONAL { ?ccaa wdt:P625 ?coord . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
ORDER BY ?iso
```

```sparql
# Nº de Bienes de Interés Cultural por CCAA (se ejecuta por lotes de pocas CCAA para evitar el tiempo máximo de consulta)
SELECT ?iso ?ccaaLabel (COUNT(DISTINCT ?bien) AS ?n_bic) WHERE {
  VALUES ?iso { "ES-AN" "ES-AR" "ES-AS" "ES-IB" }
  ?ccaa wdt:P300 ?iso ;
        wdt:P17 wd:Q29 .
  ?bien wdt:P808 ?codigo_bic ;
        wdt:P131/wdt:P131?/wdt:P131?/wdt:P131? ?ccaa .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
GROUP BY ?iso ?ccaaLabel
ORDER BY ?iso
```

**Qué contienen los ficheros de Wikidata.**
- `wikidata_ccaa.csv` (19 filas) es la ficha de identidad de cada territorio: URI de Wikidata, etiqueta, código ISO y coordenadas de un punto representativo. Enriquece `dim_ccaa` y permite enlazar cada CCAA con `owl:sameAs` en el apartado 5.
- `wikidata_bic_por_ccaa.csv` (19 filas) es un recuento agregado: nº de elementos de Wikidata con código BIC en cada CCAA (12.967 en total). Es un indicador, no el listado de bienes, y depende de la cobertura de Wikidata en cada región; por eso se interpreta como indicador relativo entre territorios y no como registro oficial. No se ha encontrado una fuente nacional abierta y homogénea del registro de BIC por CCAA; los portales autonómicos publican cada uno su propio formato.

Las coordenadas llegan en formato WKT, `Point(longitud latitud)`, y se separan en el ETL. Alternativa para el patrimonio: OpenStreetMap con la etiqueta [`ref:bic`](https://wiki.openstreetmap.org/wiki/Key:ref:bic) mediante [Overpass Turbo](https://overpass-turbo.eu/).

**Tabla de códigos de CCAA.** `data/raw/ccaa_codigos.csv` contiene el código INE, el código ISO, el nombre oficial y el nombre tal y como lo escribe el INE en sus tablas (por ejemplo `Madrid, Comunidad de`). Es la tabla de conciliación entre fuentes que usa el ETL.

CCAA con su código INE y su código ISO 3166-2:

| INE | CCAA | ISO | INE | CCAA | ISO |
|---|---|---|---|---|---|
| 01 | Andalucía | ES-AN | 11 | Extremadura | ES-EX |
| 02 | Aragón | ES-AR | 12 | Galicia | ES-GA |
| 03 | Principado de Asturias | ES-AS | 13 | Comunidad de Madrid | ES-MD |
| 04 | Illes Balears | ES-IB | 14 | Región de Murcia | ES-MC |
| 05 | Canarias | ES-CN | 15 | Comunidad Foral de Navarra | ES-NC |
| 06 | Cantabria | ES-CB | 16 | País Vasco | ES-PV |
| 07 | Castilla y León | ES-CL | 17 | La Rioja | ES-RI |
| 08 | Castilla-La Mancha | ES-CM | 18 | Ceuta | ES-CE |
| 09 | Cataluña | ES-CT | 19 | Melilla | ES-ML |
| 10 | Comunitat Valenciana | ES-VC | | | |

### Inventario de datos descargados (`data/raw/` y `data/clean/`)

| Fichero | Contenido | Tamaño |
|---|---|---|
| `ine_67190_eoh_…csv` | EOH: 70 territorios (nacional, 19 CCAA y 50 provincias) × 2 conceptos × 3 tipos de residencia × 333 meses (1999M01–2026M09) | 139.860 filas, 13 MB |
| `ine_67191_eoap_…csv` | EOAP: apartamentos turísticos, misma estructura sin provincias (hasta 2026M08) | 38.400 filas, 3 MB |
| `ine_67192_eoac_…csv`, `ine_67193_eotr_…csv` | EOAC (campings) y EOTR (turismo rural), misma estructura | 3 MB cada uno |
| `ine_56944_ecp_…zip` | Población residente por CCAA, sexo, nacionalidad y país de nacimiento, trimestral | 82 MB sin comprimir |
| `wikidata_ccaa.csv` | Identidad y coordenadas de las 19 CCAA | 19 filas |
| `wikidata_bic_por_ccaa.csv` | Nº de BIC en Wikidata por CCAA | 19 filas |
| `ccaa_codigos.csv` | Códigos INE e ISO y nombre de cada CCAA tal y como lo escribe el INE | 19 filas |
| `cnig/…recintos_autonomicas…` | Shapefiles de CCAA (Península y Baleares, Ceuta y Melilla; Canarias) | pocos MB |
| `data/clean/ccaa.geojson` | Geometría de las 19 CCAA, simplificada | 1,1 MB |

---

## 4. Apartado 3: Diseño del almacén de datos

Modelo en **estrella**: una única tabla de hechos (`fact_ocupacion`) que contiene solo claves ajenas y medidas numéricas, rodeada de seis dimensiones con los atributos descriptivos y categóricos.

### Diseño conceptual
- **Hecho:** ocupación turística, observada cada mes para un territorio, un tipo de alojamiento y un origen del viajero.
- **Medidas:** viajeros, pernoctaciones y estancia media.
- **Dimensiones:** Tiempo, Territorio (CCAA), Tipo de alojamiento, Origen del viajero, Nivel de estancia y Calidad del dato.
- **Contexto del territorio:** la población y el patrimonio cultural describen a cada CCAA y forman parte de la dimensión Territorio.

Diagrama editable: [`docs/diseno_conceptual.drawio`](docs/diseno_conceptual.drawio) (draw.io). Exportado como `.drawio.svg` y `.drawio.png`.

![Diseño conceptual](docs/diseno_conceptual.drawio.svg)

### Diseño lógico

Diagrama editable: [`docs/diseno_logico.drawio`](docs/diseno_logico.drawio) (draw.io; exportado como `.drawio.svg` y `.drawio.png`). Muestra las siete tablas con sus tipos, claves primarias (PK), ajenas (FK) y únicas (UK), las medidas resaltadas y el grano.

![Diseño lógico](docs/diseno_logico.drawio.svg)

| Tabla | Grano | Contenido |
|---|---|---|
| `fact_ocupacion` | mes × CCAA × tipo de alojamiento × origen | Claves ajenas a las seis dimensiones y tres medidas: `viajeros`, `pernoctaciones` y `estancia_media` (derivada) |
| `dim_tiempo` | mes | Año, mes, trimestre y temporada |
| `dim_ccaa` | CCAA (19 filas) | Códigos INE e ISO, QID de Wikidata, coordenadas, población de referencia y su categoría, nº de BIC y su categoría |
| `dim_tipo_alojamiento` | tipo | Hotel, Apartamento, Camping, Turismo rural (con su encuesta INE y grupo hotelero/extrahotelero) |
| `dim_origen` | origen | Residentes en España y Residentes en el extranjero |
| `dim_nivel_estancia` | nivel | Corta, Media, Larga y Sin dato, con sus rangos en días |
| `dim_calidad_dato` | combinación de marcas | Dato original, Dato imputado, Valor atípico, Imputado y atípico |

### Las dimensiones «nivel de estancia» y «calidad del dato»

Estas dos dimensiones no vienen del INE: las crea el ETL para describir cada fila de la tabla de hechos. Es posible que causen confundisión, así que conviene explicarlas detenidamente:

| | Nivel de estancia | Calidad del dato |
|---|---|---|
| Pregunta que responde | ¿Cómo de larga es la estancia media de esa fila? | ¿Cómo se ha obtenido ese valor? |
| Se calcula a partir de | `estancia_media` (pernoctaciones / viajeros) | Lo que hizo el ETL con el dato: nada, rellenarlo o marcarlo como raro |
| Valores | Corta, Media, Larga, Sin dato | Dato original, Dato imputado, Valor atípico, Imputado y atípico |
| Para qué sirve | Agrupar y comparar (por ejemplo, ¿dónde predominan las estancias cortas?) | Saber qué cifras son originales y poder excluir las que no lo son |

**Nivel de estancia (`dim_nivel_estancia`).** Convierte la estancia media, que es un número, en una etiqueta. Los límites iniciales son: **Corta** (menos de 2 días), **Media** (de 2 a 4) y **Larga** (más de 4). Si la fila no tiene estancia media (por ejemplo, porque no hay viajeros), recibe **Sin dato**, que es el valor por defecto de la clave. Ejemplo: una fila con 1.000 viajeros y 2.500 pernoctaciones tiene una estancia media de 2,5 días, así que su nivel es *Media*. Los límites se guardan una sola vez en la dimensión (`min_dias`, `max_dias`) y se ajustarán cuando se vea la distribución real.

**Calidad del dato (`dim_calidad_dato`).** Registra qué tratamiento ha recibido el valor durante la limpieza. Nunca se borra nada: se marca.

| Valor | Cuándo se asigna |
|---|---|
| Dato original | El valor es el que publicó el INE, sin cambios |
| Dato imputado | Faltaba y lo ha calculado el ETL: o bien por diferencia (total − el otro componente), o bien como la media de los meses vecinos |
| Valor atípico | Es el que publicó el INE, pero se aleja mucho de lo normal en esa CCAA y tipo de alojamiento (se detecta con la media y la desviación). No es un error: por ejemplo, los meses de 2020 y 2021 por la pandemia son datos reales |
| Imputado y atípico | Cumple las dos condiciones a la vez |

Hay cuatro filas porque las dos marcas (imputado, atípico) se pueden combinar, y así la tabla de hechos guarda una sola clave en lugar de dos columnas de «sí/no». Para analizar solo con datos originales basta con filtrar por esta dimensión:

```sql
-- Pernoctaciones por año y CCAA sin contar valores imputados
SELECT t.anio, c.nombre AS ccaa, SUM(f.pernoctaciones) AS pernoctaciones
FROM fact_ocupacion f
JOIN dim_tiempo t       ON t.tiempo_key   = f.tiempo_key
JOIN dim_ccaa c         ON c.ccaa_key     = f.ccaa_key
JOIN dim_calidad_dato q ON q.calidad_key  = f.calidad_key
WHERE q.dato_imputado = 0
GROUP BY t.anio, c.nombre;
```

Ambas se asignan en el ETL antes de cargar la fila (`nivel_key` con *Number range* y `calidad_key` según el control, la imputación y la detección de atípicos), por lo que no cambian después.

### Diseño físico
Script de creación: [`sql/01_crear_almacen_turismo.sql`](sql/01_crear_almacen_turismo.sql). Modelo de MySQL Workbench (obtenido por ingeniería inversa del esquema creado): [`docs/almacen_turismo.mwb`](docs/almacen_turismo.mwb). Diagrama EER exportado: `docs/almacen_turismo_fisico.png` (también en `.svg` y `.pdf`).

![Diseño físico (MySQL Workbench)](docs/almacen_turismo_fisico.png)

**Verificación de la implementación** (MySQL 8, MySQL Workbench):
- El script se ejecuta completo sin errores y crea 7 tablas (`fact_ocupacion` y 6 dimensiones) y 2 vistas. Solo emite avisos informativos: la base de datos no existía antes del `DROP` y la anchura de entero de `TINYINT(1)` está obsoleta en MySQL 8.
- Las dimensiones pequeñas quedan cargadas: 4 tipos de alojamiento, 2 orígenes, 4 niveles de estancia y 4 marcas de calidad.
- `SHOW CREATE TABLE fact_ocupacion` confirma la clave primaria de seis columnas, el `UNIQUE` del grano (cuatro columnas) y las seis claves ajenas.

- Motor InnoDB, codificación `utf8mb4`.
- Clave primaria de la tabla de hechos compuesta por las seis claves de dimensión (cada dimensión conectada aporta una PK/FK, como en la convención de clase), más una restricción `UNIQUE` sobre las cuatro claves que definen el grano (mes, CCAA, tipo y origen). `nivel_key` y `calidad_key` dependen de esas cuatro, así que el `UNIQUE` impide que un mismo grano se cargue dos veces con distinta categoría.
- Claves naturales únicas (`codigo_ine`, `codigo`, `anio + mes`) para que el ETL pueda localizar las claves de cada dimensión.
- Las dimensiones pequeñas (tipo de alojamiento, origen, nivel de estancia y calidad del dato) se cargan en el propio script; `dim_tiempo` y `dim_ccaa` se cargan desde Pentaho.
- Miembro "Sin dato" en `dim_nivel_estancia` (clave 4, valor por defecto) para que la tabla de hechos no tenga claves nulas.
- Vista `v_ocupacion_total`: viajeros y pernoctaciones totales por mes, CCAA y tipo (suma de residentes en España y en el extranjero).
- Vista `v_ocupacion_anual_ccaa`: pernoctaciones por habitante y año.

### Justificación del diseño: por qué una única tabla de hechos

**Idea en una frase.** Solo hay una cosa que se mide todos los meses (la ocupación de los alojamientos), así que hay una sola tabla de hechos. Todo lo demás describe esa medición (cuándo, dónde, qué tipo de alojamiento, de qué origen) y va en tablas de dimensiones.

| Término | Qué significa aquí |
|---|---|
| Tabla de hechos | Guarda las mediciones: una fila por cada observación mensual (`fact_ocupacion`) |
| Dimensión | Tabla que describe el contexto de una medición: cuándo, dónde, qué tipo, de quién |
| Medida | Número que se mide y que cambia cada mes (viajeros, pernoctaciones) |
| Atributo | Dato descriptivo de una dimensión (el nombre de una CCAA, su población, etc.) |
| Grano | Lo que representa exactamente cada fila de la tabla de hechos. Aquí: un mes, una CCAA, un tipo de alojamiento y un origen del viajero |

**1. Cómo decidimos qué es una medida y qué es un atributo.** Es una medida lo que el INE vuelve a medir cada mes y cambia de un mes a otro. Lo que describe a un territorio o es una etiqueta es un atributo y va en una dimensión.

| Dato | ¿Se mide cada mes? | Dónde va |
|---|---|---|
| Viajeros, pernoctaciones, estancia media | Sí: el INE publica un valor nuevo cada mes | Medidas de `fact_ocupacion` |
| Población de la CCAA | No: usamos una sola cifra por CCAA (la del 1 de enero más reciente) | Atributo de `dim_ccaa` |
| Nº de BIC (bienes culturales) | No: es un recuento que sacamos una sola vez de Wikidata, en una fecha concreta | Atributo de `dim_ccaa`, con su fecha de extracción |
| Tipo de alojamiento, origen, temporada, nivel de estancia, calidad del dato | No: son etiquetas | Dimensiones |

**2. Por qué la población y el patrimonio no son hechos.** Hay un valor de ocupación por cada mes, CCAA, tipo y origen, pero solo una población y un recuento de BIC por CCAA. Si los pusiéramos en la tabla de hechos, el mismo número se repetiría en cada fila mensual y, al sumar, saldrían resultados sin sentido. Ejemplo: un territorio con 8 millones de habitantes tiene 96 filas al año (12 meses × 4 tipos × 2 orígenes); al sumar un año completo, su población saldría como 768 millones. Como atributos de `dim_ccaa`, cada dato aparece una sola vez.

**3. Las tres preguntas se responden de forma directa.** Cada consulta usa la tabla de hechos y une (`JOIN`) las dimensiones que necesita, sin combinar varias tablas de hechos:

```sql
-- P1: pernoctaciones por año, CCAA y tipo de alojamiento
SELECT t.anio, c.nombre AS ccaa, a.nombre AS tipo, SUM(f.pernoctaciones) AS pernoctaciones
FROM fact_ocupacion f
JOIN dim_tiempo t ON t.tiempo_key = f.tiempo_key
JOIN dim_ccaa c ON c.ccaa_key = f.ccaa_key
JOIN dim_tipo_alojamiento a ON a.tipo_key = f.tipo_key
GROUP BY t.anio, c.nombre, a.nombre;

-- P2: % de pernoctaciones de residentes en el extranjero
SELECT t.anio, c.nombre AS ccaa,
       ROUND(100 * SUM(CASE WHEN o.codigo = 'EXT' THEN f.pernoctaciones END) / SUM(f.pernoctaciones), 1) AS pct_extranjero
FROM fact_ocupacion f
JOIN dim_tiempo t ON t.tiempo_key = f.tiempo_key
JOIN dim_ccaa c ON c.ccaa_key = f.ccaa_key
JOIN dim_origen o ON o.origen_key = f.origen_key
WHERE o.codigo IN ('ESP', 'EXT')
GROUP BY t.anio, c.nombre;

-- P3: patrimonio frente a demanda
SELECT c.nombre, c.n_bic, c.nivel_patrimonio, SUM(v.pernoctaciones) AS pernoctaciones
FROM v_ocupacion_total v
JOIN dim_ccaa c ON c.ccaa_key = v.ccaa_key
GROUP BY c.nombre, c.n_bic, c.nivel_patrimonio;
```

**4. La carga (ETL) es más sencilla.** Hay una sola transformación de hechos, con parámetros, que se reutiliza para las cuatro encuestas. La población (82 MB en origen) y el patrimonio se reducen a 19 filas, una por CCAA, que se cargan en `dim_ccaa` en una única transformación.

**5. La tabla de hechos queda limpia.** Solo guarda claves y números. Las etiquetas que calcula el ETL (el nivel de estancia: corta, media o larga; y la marca de si un dato es original, imputado o atípico) van a dimensiones pequeñas.

**Alternativa descartada: añadir `fact_poblacion` y `fact_patrimonio`.** Tendría sentido si la población y el patrimonio se midieran con su propia frecuencia, pero aquí no es así: el patrimonio es un único recuento por CCAA y la población solo añadiría unas 500 filas. A cambio, habría más tablas, más transformaciones de carga y consultas más complicadas, porque habría que combinar varias tablas de hechos.

**Limitación asumida.** Para calcular las pernoctaciones por habitante usamos siempre la misma población, la más reciente, y no la de cada año. Ventaja: los territorios son comparables y el cambio de población no se mezcla con la evolución del turismo. Inconveniente: no es la población exacta de cada año. Si hiciera falta, se añadiría una tabla de hechos de población anual sin tocar el resto del modelo.

### Decisiones de diseño

- **Clave de tiempo `AAAAMM`** (por ejemplo, `202403` para marzo de 2024): es fácil de leer y se ordena sola.
- **Tipo de alojamiento como dimensión:** cada encuesta del INE trata un solo tipo (hoteles, apartamentos, campings o turismo rural), así que el ETL añade el tipo como una columna más.
- **Origen del viajero:** el INE da tres cifras de residencia: total, residentes en España y residentes en el extranjero. Guardamos solo las dos últimas, porque el total es su suma y guardarlo también haría que al sumar se contara todo dos veces. El total sirve para comprobar el ETL (total = España + extranjero) y para calcular por diferencia una cifra que falte.
- **Patrimonio (BIC):** `n_bic` cuenta los elementos de Wikidata con código BIC que están dentro de cada CCAA. Depende de lo completo que esté Wikidata, así que no coincide con el registro oficial. Sirve para comparar territorios entre sí, no como cifra exacta.
- **Clave primaria de la tabla de hechos:** incluye las seis claves de dimensión, como pide la convención de clase (toda clave ajena forma parte de la clave primaria). Lo que identifica de verdad cada fila son solo cuatro: mes, CCAA, tipo y origen. Por eso hay además una restricción `UNIQUE` sobre esas cuatro, que impide cargar dos veces el mismo mes, CCAA, tipo y origen. `nivel_key` y `calidad_key` se calculan a partir de la propia fila antes de cargarla y no cambian después.
- **Marcar en lugar de borrar:** los datos imputados (rellenados por el ETL) o atípicos (muy distintos de lo normal) no se eliminan, se marcan en `dim_calidad_dato`. Así se sabe qué valores son originales y cuáles no.
- **Categorías a partir de números:** para facilitar el análisis, tres números se convierten en etiquetas. Los límites son iniciales y se ajustarán cuando veamos los datos reales.
  - `nivel_estancia`: Corta (menos de 2 días), Media (de 2 a 4) o Larga (más de 4).
  - `nivel_poblacion`: Muy grande (5 millones o más), Grande (de 2 a 5), Mediana (de 1 a 2) o Pequeña (menos de 1 millón).
  - `nivel_patrimonio`: Alto, Medio o Bajo. Se reparte las CCAA en tres grupos del mismo tamaño según su nº de BIC.
- **Temporada** (criterio inicial, se puede cambiar): Alta de junio a septiembre, Media de marzo a mayo y octubre, y Baja el resto.

### Cumplimiento de las tareas del apartado

| Tarea del enunciado | Entregable |
|---|---|
| Diseño conceptual | `docs/diseno_conceptual.drawio` y exportaciones `.drawio.svg` / `.drawio.png` |
| Diseño lógico: hechos, dimensiones, medidas y granularidad | `docs/diseno_logico.drawio` y exportaciones `.drawio.svg` / `.drawio.png`; tabla de grano de esta sección |
| Diseño físico en el SGBD elegido | `sql/01_crear_almacen_turismo.sql`; `docs/almacen_turismo.mwb` y diagrama EER |
| Implementar el almacén y proporcionar los scripts de creación | Script ejecutado en MySQL 8 (verificación descrita arriba) |
| Justificar las decisiones de diseño | Secciones *Justificación del diseño* y *Decisiones de diseño* |

---

## 5. Apartado 4: Extracción, limpieza y carga (Pentaho)

Herramienta: **Pentaho Data Integration (PDI, Kettle) 10.2 Community**. El ETL son seis transformaciones (`.ktr`) y un job (`.kjb`) que las ejecuta en orden y carga las siete tablas de `turismo_dw`. Todo se hace en PDI; no se usa Python en el ETL.

### 5.1 Decisiones de diseño y su motivo

| Decisión | Motivo |
|---|---|
| Todo el ETL en PDI | El enunciado exige PDI y solo admite Python si se justifica; aquí no hace falta |
| **Alcance temporal: 2016 a 2025** | Diez años naturales completos. 2026 se excluye porque el INE publica hasta agosto (septiembre en hoteles) y un año incompleto distorsiona la comparación anual y el porcentaje de extranjeros. Incluye 2020 y 2021 (pandemia) |
| Dimensiones antes que hechos | Cada hecho lleva claves ajenas; MySQL rechaza una fila si la clave no existe. PDI ejecuta en paralelo los pasos de una transformación, así que el orden solo se puede imponer desde el job |
| Una plantilla para las encuestas del INE | Las cuatro tienen la misma estructura (la EOH con una columna más, `Provincias`). Un solo flujo que mantener y justificar |
| Los CSV del INE se leen de `data/raw/`, no por URL | Ya están descargados y verificados, y el ETL no depende de que la API del INE responda |
| Rutas relativas (`${Internal.Entry.Current.Directory}/..`) | El repositorio funciona en cualquier ordenador y sistema operativo |
| Credenciales de MySQL en variables | El repositorio es público; usuario y contraseña no se guardan en los `.ktr` |
| Se marca, no se borra | Los valores imputados o atípicos se señalan en `dim_calidad_dato`; los datos de 2020 y 2021 son reales |

### 5.2 Preparación del entorno (una sola vez)

1. **Conector JDBC.** Copiar `mysql-connector-j-*.jar` en `data-integration\lib` y reiniciar Spoon.
2. **Variables con las credenciales.** Editar `C:\Users\<usuario>\.kettle\kettle.properties` (se puede abrir desde Spoon, menú *Edit*, o a mano con el Bloc de notas; si no existe, se crea) y añadir al final, sin comillas ni espacios:
   ```
   DB_USER=tu_usuario
   DB_PASSWORD=tu_contraseña
   ```
   Spoon solo lee el fichero al arrancar: hay que cerrarlo y volver a abrirlo.
3. **Conexión `turismo_dw`.** En la pestaña *View*, *Database connections*, nueva conexión: tipo MySQL, acceso Native (JDBC), host `localhost`, puerto `3306`, base `turismo_dw`, usuario `${DB_USER}` y contraseña `${DB_PASSWORD}`. Pulsar *Test*. Clic derecho, *Share*, para que la vean todas las transformaciones.
4. **Carpeta `kettle/`** en la raíz del repositorio. Todas las transformaciones se guardan ahí.

**Cómo se trabaja en Spoon.** Los pasos se arrastran desde la pestaña *Design* (hay buscador). Se unen con un salto: arrastrar de un paso a otro con **Shift** pulsado. El icono del ojo (*Preview*) muestra las filas que salen de un paso sin cargar nada: conviene usarlo tras añadir cada paso.

### 5.3 Visión general

```mermaid
flowchart LR
    A[INE: CSV de ocupación] --> T10[T10 a T13: hechos]
    P[INE: población] --> T02[T02: dim_ccaa]
    W[Wikidata: identidad y BIC] --> T02
    C[ccaa_codigos.csv] --> T02
    C --> T10
    T01[T01: dim_tiempo] --> DB[(MySQL turismo_dw)]
    T02 --> DB
    T10 --> DB
    DB --> T40[T40: validación]
    J[J00_carga.kjb] -. orquesta .-> T01
    J -. orquesta .-> T02
    J -. orquesta .-> T10
    J -. orquesta .-> T40
```

| Fichero | Qué carga | Estado |
|---|---|---|
| `T01_dim_tiempo.ktr` | `dim_tiempo` (120 meses, 2016-2025) | Hecho y verificado |
| `T02_dim_ccaa.ktr` | `dim_ccaa` (19 filas) | Hecho y verificado |
| `T10_eoh.ktr` | `fact_ocupacion`, hoteles | Pendiente |
| `T11_eoap.ktr`, `T12_eoac.ktr`, `T13_eotr.ktr` | `fact_ocupacion`, apartamentos, campings y turismo rural | Pendiente |
| `T40_validacion.ktr` | Controles sobre el almacén cargado | Pendiente |
| `J00_carga.kjb` | Orquesta todo | Pendiente |

**Orden de ejecución:** J00 limpia las tablas, ejecuta T01 y T02, después T10 a T13, y por último T40.

### 5.4 T01_dim_tiempo

**Sale:** 120 filas (`tiempo_key`, `anio`, `mes`, `nombre_mes`, `trimestre`, `temporada`). **Idea:** se genera un contador de 0 a 119 y de él se derivan año y mes.

```
Generate rows → Add sequence → Formula → Formula → Value Mapper ×3 → Select values → Table output
```

| # | Paso (nombre) | Configuración |
|---|---|---|
| 1 | Generate rows (`Generar 120 filas`) | *Limit* = 120, sin campos |
| 2 | Add sequence (`Contador`) | Campo `n`; desmarcar *Use DB* y *Use counter*; inicio 0, incremento 1, máximo 999999 |
| 3 | Formula (`Año y mes`) | `anio` = `2016 + INT([n]/12)` y `mes` = `MOD([n];12) + 1`, ambos Integer |
| 4 | Formula (`Clave AAAAMM`) | `tiempo_key` = `[anio]*100 + [mes]`, Integer. En un paso aparte porque una fórmula no puede usar un campo creado en el mismo paso |
| 5 | Value Mapper (`Nombre mes`) | Campo `mes` a `nombre_mes`: 1 = Enero ... 12 = Diciembre |
| 6 | Value Mapper (`Trimestre`) | Campo `mes` a `trimestre`: 1 a 3 = 1; 4 a 6 = 2; 7 a 9 = 3; 10 a 12 = 4 (una fila por mes) |
| 7 | Value Mapper (`Temporada`) | Campo `mes` a `temporada`, valor por defecto `Baja`: 6, 7, 8, 9 = Alta; 3, 4, 5, 10 = Media |
| 8 | Select values (`Columnas dim_tiempo`) | Pestaña *Select & Alter*: `tiempo_key, anio, mes, nombre_mes, trimestre, temporada` en ese orden. Pestaña *Meta-data*: solo `trimestre` con tipo Integer (no pulsar *Get fields to change*: incluiría `n`, que ya se ha descartado, y da error) |
| 9 | Table output (`Carga dim_tiempo`) | Conexión `turismo_dw`, tabla `dim_tiempo`, *Commit size* 1000, **sin** *Truncate table* (MySQL no permite truncar tablas referenciadas por claves ajenas) |

El Value Mapper compara cada valor con una sola entrada de la tabla: no admite listas como `1,2,3`.

**Comprobación:**
```sql
SELECT COUNT(*), MIN(tiempo_key), MAX(tiempo_key) FROM turismo_dw.dim_tiempo;
-- esperado: 120, 201601, 202512
```

Un *Table output* solo inserta: ejecutar dos veces sin vaciar la tabla da `Duplicate entry`. Lo resuelve el job (apartado 5.8).

### 5.5 T02_dim_ccaa

**Sale:** 19 filas, una por CCAA, con las columnas de `dim_ccaa` salvo `ccaa_key`, que es autonumérica y no se informa.

**Idea:** `ccaa_codigos.csv` es la tabla base de 19 filas. Las otras tres fuentes (Wikidata, patrimonio y población) se le pegan por una clave común con un paso *Stream lookup*. Después se crean dos etiquetas con *Number range* y se carga.

| Columna de `dim_ccaa` | Origen |
|---|---|
| `codigo_ine`, `codigo_iso`, `nombre` | `ccaa_codigos.csv` |
| `wikidata_qid`, `latitud`, `longitud` | `wikidata_ccaa.csv` |
| `habitantes_ref`, `poblacion_fecha_ref` | Población INE 56944 (1 de enero más reciente) |
| `n_bic` | `wikidata_bic_por_ccaa.csv` |
| `nivel_poblacion`, `nivel_patrimonio` | Derivadas de `habitantes_ref` y `n_bic` (**Binning**) |

![Transformación T02_dim_ccaa en Spoon](docs/T02_dim_ccaa.png)

**Cómo funciona un *Stream lookup*.** Recibe dos flujos: el **principal** (aquí, el que viene de `ccaa_codigos`) y uno de **consulta**, que se elige en *Lookup step*. Para cada fila del principal busca en el de consulta la fila con la misma clave y le añade las columnas indicadas en *Specify the fields to retrieve*. Si la clave no se encuentra, la fila no se pierde: las columnas añadidas quedan a NULL. Por eso, cuando una columna sale vacía, lo primero que hay que revisar es la clave.

**Rutas.** Todos los ficheros se leen con rutas relativas, por ejemplo `${Internal.Entry.Current.Directory}/../data/raw/ccaa_codigos.csv`, de modo que el repositorio funciona en cualquier ordenador. El botón *Show filename(s)...* comprueba que la ruta se resuelve.

#### Pasos

| # | Paso (nombre) | Configuración |
|---|---|---|
| 1 | Text file input (`Leer ccaa_codigos`) | Separador `;`, UTF-8. `codigo_ine` debe ser **String** de longitud 2 y sin formato numérico: con formato `#` el código `01` se convertiría en `1` y no coincidiría con el prefijo `01 Andalucía` de las tablas del INE |
| 2 | Text file input (`Leer wikidata_ccaa`) | Separador `,`, UTF-8. Campos: URI de Wikidata, etiqueta, `iso` y `coord` (formato WKT `Point(longitud latitud)`) |
| 3 | Replace in string (`Limpiar QID y coordenada`) | Dos reemplazos con expresión regular: de la URI se conserva solo el QID (se elimina todo hasta la última `/`) y de la coordenada se quitan `Point(` y `)`, de modo que queda `longitud latitud` |
| 4 | Split Fields (`Separar longitud y latitud`) | Separador: un espacio. Campos `longitud` y `latitud`, tipo Number, **símbolo decimal `.`** (el WKT usa punto; si se deja vacío PDI usa el del sistema, que en español es la coma) |
| 5 | Text file input (`Leer wikidata_bic_por_ccaa`) | Separador `,`, **codificación UTF-8 indicada explícitamente** (si no, en Windows se usa la del sistema). Campos `iso`, etiqueta y `n_bic` (Integer) |
| 6 | Text file input (`Leer población`) | Fichero `data/raw/ine_56944_*.zip`, pestaña *Content*, *Compression* = Zip. Separador `;`, UTF-8, decimal `,` y agrupación `.`. El primer campo se llama `Sexo` (el nombre lo pone el usuario en *Fields*; la cabecera del fichero se salta) |
| 7 | Filter rows (`Solo totales, 1 de enero`) | `Sexo = Total` y `Nacionalidad = Total` y `País_de_Nacimiento = Total` y `Periodo CONTAINS "1 de enero"`. Reduce 1.015.560 filas a 480 |
| 8 | Select values (`Periodo a fecha, Total a entero`) | Solo pestaña *Meta-data*: `Periodo` pasa a tipo Date con formato `d 'de' MMMM 'de' yyyy` y *Date Locale* `es`, y se renombra `periodo_formateado`; `Total` pasa a Integer y se renombra `habitantes_ref` |
| 9 | Replace in string (`Código INE de la población`) | Campo de entrada `Comunidades_y_ciudades_autónomas` (valores como `01 Andalucía`, `04 Balears, Illes`), campo de salida **`codigo_ine_pob`**, expresión regular `^(\d{2}).*`, reemplazo `$1`. Los dos primeros caracteres son el código INE |
| 10 | Sort rows (`Ordenar CCAA y fechas desc`) | Por `codigo_ine_pob` ascendente y `periodo_formateado` **descendente** |
| 11 | Unique rows (`Última población por CCAA`) | Compara por `codigo_ine_pob`. Al venir ordenado por fecha descendente, conserva la fila del 1 de enero **más reciente** de cada CCAA |
| 12 | Stream lookup (`Stream lookup (Wikidata)`) | *Lookup step*: `Separar longitud y latitud`. Clave: `codigo_iso` = `iso`. Recupera `qid`, `longitud` y `latitud` |
| 13 | Stream lookup (`Stream lookup (BIC)`) | *Lookup step*: `Leer wikidata_bic_por_ccaa`. Clave: `codigo_iso` = `iso`. Recupera `n_bic` |
| 14 | Stream lookup (`Stream lookup (población)`) | *Lookup step*: `Última población por CCAA`. Clave: **`codigo_ine`** = `codigo_ine_pob`. Recupera `habitantes_ref` y `periodo_formateado`. La clave es el código y **no el nombre**: `nombre_ine` (`Balears, Illes`) no coincide con el nombre del fichero de población (`04 Balears, Illes`) |
| 15 | Number range (`Nivel de población`) | Campo `habitantes_ref`, salida `nivel_poblacion` (tabla siguiente) |
| 16 | Number range (`Nivel de patrimonio`) | Campo `n_bic`, salida `nivel_patrimonio` (tabla siguiente) |
| 17 | Select values (`Columnas dim_ccaa`) | Pestaña *Select & Alter*, solo estos 11 campos: `codigo_ine, codigo_iso, nombre, wikidata_qid` (renombrando `qid`), `latitud, longitud, habitantes_ref, poblacion_fecha_ref` (renombrando `periodo_formateado`), `nivel_poblacion, n_bic, nivel_patrimonio`. *Table output* inserta por **nombre de campo**: lo que falte queda a NULL y lo que sobre da error |
| 18 | Table output (`Carga dim_ccaa`) | Conexión `turismo_dw`, tabla `dim_ccaa`, *Commit size* 100, sin *Truncate table* y sin *Specify database fields* |

**Binning** (**Number range**). El límite inferior es inclusivo y el superior exclusivo; un límite vacío significa «sin límite».

| `nivel_poblacion` (`habitantes_ref`) | Inferior | Superior |
|---|---|---|
| Pequeña | (vacío) | 1000000 |
| Mediana | 1000000 | 2000000 |
| Grande | 2000000 | 5000000 |
| Muy grande | 5000000 | (vacío) |

| `nivel_patrimonio` (`n_bic`) | Inferior | Superior | CCAA |
|---|---|---|---|
| Bajo | (vacío) | 240 | 6 |
| Medio | 240 | 600 | 6 |
| Alto | 600 | (vacío) | 7 |

Los cortes de patrimonio reparten las 19 CCAA en 6, 6 y 7, un tercio cada grupo.

#### Verificar la carga

Previsualiza `Columnas dim_ccaa` antes de ejecutar: deben salir 19 filas. Tras ejecutar, en MySQL Workbench:

```sql
-- 1. Filas y nulos: esperado 19, 0, 0, 0, 0
SELECT COUNT(*),
       SUM(n_bic IS NULL),
       SUM(habitantes_ref IS NULL),
       SUM(nivel_poblacion IS NULL),
       SUM(nivel_patrimonio IS NULL)
FROM turismo_dw.dim_ccaa;

-- 2. Contenido completo
SELECT codigo_ine, nombre, habitantes_ref, nivel_poblacion, n_bic, nivel_patrimonio
FROM turismo_dw.dim_ccaa
ORDER BY codigo_ine;

-- 3. Reparto de las etiquetas: patrimonio esperado Bajo 6, Medio 6, Alto 7
SELECT nivel_patrimonio, COUNT(*) FROM turismo_dw.dim_ccaa GROUP BY nivel_patrimonio;
SELECT nivel_poblacion,  COUNT(*) FROM turismo_dw.dim_ccaa GROUP BY nivel_poblacion;
```

Casos de control (población a 1 de enero de 2025, `n_bic` de Wikidata):

| CCAA | `habitantes_ref` | `n_bic` | `nivel_poblacion` | `nivel_patrimonio` |
|---|---|---|---|---|
| Andalucía | 8.676.713 | 2448 | Muy grande | Alto |
| Comunidad de Madrid | 7.113.886 | 375 | Muy grande | Medio |
| Principado de Asturias | 1.015.128 | 236 | Mediana | Bajo |
| Cantabria | 593.623 | 248 | Pequeña | Medio |

Asturias comprueba el corte de 1.000.000 y Cantabria el de `n_bic` en 240.

#### Vaciar las tablas para repetir una carga

Un *Table output* solo inserta: ejecutar dos veces sin vaciar da `Duplicate entry`. Hay que borrar en este orden, primero los hechos y después las dimensiones, porque los hechos referencian a las dimensiones por claves ajenas:

```sql
DELETE FROM turismo_dw.fact_ocupacion WHERE tiempo_key > 0;
DELETE FROM turismo_dw.dim_ccaa       WHERE ccaa_key   > 0;
DELETE FROM turismo_dw.dim_tiempo     WHERE tiempo_key > 0;
```

- El `WHERE` sobre la clave evita el error 1175 del modo seguro de MySQL Workbench (*You are using safe update mode...*). La alternativa es desactivar *Safe Updates* en *Edit → Preferences → SQL Editor* y reconectar.
- No se usa `TRUNCATE`: MySQL no permite truncar tablas referenciadas por claves ajenas.
- Si se borra una dimensión antes de vaciar los hechos, MySQL rechaza el borrado (error 1451).
- `dim_tipo_alojamiento`, `dim_origen`, `dim_nivel_estancia` y `dim_calidad_dato` no se vacían: las carga el script SQL.
- El job `J00_carga.kjb` ejecuta estos borrados antes de cargar, por lo que no hay que hacerlos a mano.

### 5.6 T10 a T13: plantillas de ocupación

**Entra:** el CSV del INE de la encuesta (una fila por valor). **Sale:** filas de `fact_ocupacion` solo para origen ESP y EXT.

**Parámetros** (*Transformation properties*, pestaña *Parameters*):

| | `ID_TABLA` | `COD_TIPO` |
|---|---|---|
| T10 hoteles (EOH) | `67190` | `HOT` |
| T11 apartamentos (EOAP) | `67191` | `APT` |
| T12 campings (EOAC) | `67192` | `CAM` |
| T13 turismo rural (EOTR) | `67193` | `RUR` |

**Cómo se obtienen T11 a T13:** la EOH tiene 8 columnas (con `Provincias`) y las otras tres 7. T10 se hace primero y se prueba. T11 se obtiene duplicando T10 y quitando el campo `Provincias` del *Text file input* y su condición en el filtro. T12 y T13 son copias de T11 con otros parámetros.

**Estructura de las filas de origen** (verificada sobre el contenido real): `Totales Territoriales` vale siempre `Total Nacional`; las CCAA son las filas con `Comunidades y Ciudades Autónomas` informada (`01 Andalucía`...); `Residencia: Nivel 2` vacío significa total; `Viajeros y pernoctaciones` vale `Viajero` o `Pernoctaciones`; `Periodo` tiene la forma `2026M08`.

**Flujo, paso a paso:**

| # | Paso | Qué se hace |
|---|---|---|
| 1 | Text file input (`Leer INE`) | Fichero: `${Internal.Entry.Current.Directory}/../data/raw`, expresión regular `ine_${ID_TABLA}_.*\.csv`. UTF-8, separador `;`, cabecera, *Date locale* `es`. Campo `Total`: Number, decimal `,`, grupo `.`, *Null if* `..` |
| 2 | Select values | Renombra columnas a nombres simples (`ccaa`, `concepto`, `residencia`, `periodo`, `total`...). El primer nombre de columna puede traer el BOM del fichero: se corrige aquí |
| 3 | Filter rows (`Solo CCAA`) | Se conservan las filas con `ccaa` no vacío. En la EOH, además, `Provincias` vacío (las provincias son redundantes con su CCAA). Se descarta así `Total Nacional` |
| 4 | Concilar CCAA | Los dos primeros caracteres de `ccaa` son el `codigo_ine` (*Replace in string* o *Formula* con `LEFT`). Se contrasta con `ccaa_codigos.csv` mediante *Stream lookup*; las que no coincidan se desvían a una salida de errores |
| 5 | Split Fields (`Año y mes`) | `2026M08` se separa en `anio` y `mes` con el separador `M` (**Splitting**, técnica obligatoria de ingeniería de características). Se pasan a Integer |
| 6 | Filter rows (`Alcance`) | `anio >= 2016` y `anio <= 2025`. Evita claves ajenas huérfanas y reduce el volumen |
| 7 | Value Mapper (`Origen`) | `Residentes en España` a `ESP`, `Residentes en el Extranjero` a `EXT`, valor por defecto `TOT` (el total, que va a la rama de control) |
| 8 | Value Mapper (`Medida`) | `Viajero` a `viajeros`, `Pernoctaciones` a `pernoctaciones` |
| 9 | Sort rows + Row denormaliser | Se ordena por `codigo_ine, anio, mes, origen`. *Row denormaliser* (clave: `medida`) coloca `viajeros` y `pernoctaciones` en columnas |
| 10 | Control del total (rama TOT) | *Filter rows* separa `origen = TOT` de ESP y EXT. En la rama ESP y EXT, *Group by* suma por `codigo_ine, anio, mes`. *Merge join* con el total compara total frente a ESP + EXT; las diferencias van a una salida de registro |
| 11 | Valores ausentes | `..` es NULL. Si falta un componente (ESP o EXT) y el total existe, se calcula por diferencia (total menos el otro) y `calidad_key = 2`. Un hueco aislado en una serie se imputa con la media de los meses vecinos (*Analytic Query*, funciones LAG y LEAD, sobre datos ordenados por CCAA, origen y mes) con `calidad_key = 2`. Los huecos largos se dejan en NULL |
| 12 | Calculator (`Estancia media`) | `estancia_media = pernoctaciones / viajeros`, con NULL si `viajeros` es 0 o nulo |
| 13 | Number range (`Binning`) | `estancia_media` a `nivel_key`: menos de 2 a 1 (Corta), de 2 a 4 a 2 (Media), más de 4 a 3 (Larga), sin dato a 4 (Sin dato). Cortes iniciales, revisables con la distribución real |
| 14 | Outliers | *Group by* por `codigo_ine, tipo, origen` calcula media y desviación de `pernoctaciones`; *Merge join* o *Stream lookup* lo une a cada fila; *Calculator* obtiene el z-score `(x - media) / desviación`. Si `|z| > 3` (umbral inicial) la fila se marca como atípica. La marca se combina con la imputación para fijar `calidad_key`: 1 original, 2 imputado, 3 atípico, 4 imputado y atípico. **No se borra ninguna fila** |
| 15 | Claves | *Constant* o `COD_TIPO` como campo; `tiempo_key = anio*100 + mes`; *Database lookup* en `dim_ccaa` (por `codigo_ine`), `dim_tipo_alojamiento` (por `codigo`) y `dim_origen` (por `codigo`). Las filas sin clave se desvían a una salida de errores |
| 16 | Unique rows + Table output | Se eliminan duplicados del grano (`tiempo_key, ccaa_key, tipo_key, origen_key`) y se carga en `fact_ocupacion` (*Commit size* 1000, sin *Truncate table*) |

**Comprobación tras cada carga:**
```sql
SELECT t.codigo, COUNT(*) AS filas, MIN(f.tiempo_key), MAX(f.tiempo_key)
FROM turismo_dw.fact_ocupacion f
JOIN turismo_dw.dim_tipo_alojamiento t ON t.tipo_key = f.tipo_key
GROUP BY t.codigo;
```
El máximo no debe superar `202512` ni el mínimo bajar de `201601`.

### 5.7 T40_validacion

Un *Table input* por control, que devuelve el número de filas incorrectas. Después, *Filter rows* (`n > 0`) y *Abort* detienen el job si algún control falla:

| Control | Consulta |
|---|---|
| Sin claves huérfanas | filas de `fact_ocupacion` sin fila en alguna dimensión |
| Sin negativos | `viajeros < 0` o `pernoctaciones < 0` |
| Coherencia | `pernoctaciones < viajeros` |
| Estancia razonable | `estancia_media` fuera de un rango (por ejemplo, de 1 a 30 días) |
| Grano único | duplicados de `(tiempo_key, ccaa_key, tipo_key, origen_key)` |
| Volumen | filas cargadas frente a las filas de origen filtradas (se registra) |
| Total = ESP + EXT | resultado de la rama de control de T10 a T13 |

### 5.8 J00_carga.kjb

```
Start → SQL (limpieza) → T01 → T02 → T10 → T11 → T12 → T13 → T40 → Success
```

- **SQL** (entrada de job, conexión `turismo_dw`): `DELETE FROM fact_ocupacion; DELETE FROM dim_ccaa; DELETE FROM dim_tiempo;` (primero los hechos y después las dimensiones, por las claves ajenas). Así el job se puede repetir.
- **Transformation** (una entrada por `.ktr`; en T10 a T13 se rellenan los parámetros `ID_TABLA` y `COD_TIPO` de la tabla del apartado 5.6).
- Cada salto del job se marca *Follow when result is true*: si algo falla, no continúa.

Ejecución:

```bash
./kitchen.sh -file=kettle/J00_carga.kjb -level:Basic          # Linux
data-integration\Kitchen.bat /file:kettle\J00_carga.kjb /level:Basic   # Windows
```

### 5.9 Cumplimiento de los requisitos del apartado

| Requisito | Cómo se cubre |
|---|---|
| Conectar con fuentes diversas | CSV y ZIP (INE), CSV de Wikidata (y REST client opcional contra SPARQL), shapefile (CNIG), MySQL (lookups y validación) |
| Fusión de varias fuentes | *Stream lookup* y *Merge join*: códigos, Wikidata y población (T02); ocupación y control de totales (T10 a T13) |
| Seleccionar, filtrar, ordenar | *Select values*, *Filter rows*, *Sort rows* |
| Corregir errores | Eliminación del BOM, conciliación de nombres de CCAA con su código, `..` convertido en NULL, tipos y formatos numéricos |
| Valores que faltan | Componente ausente recuperado por diferencia; hueco aislado imputado con la media de los vecinos; huecos largos en NULL; siempre marcado |
| Reducir redundancia | Se descartan `Total Nacional`, las provincias y el total de residencia (se usa solo como control); *Unique rows* y claves únicas |
| Ingeniería de características | **Splitting** (periodo a año y mes), variable derivada `estancia_media`, `temporada` y **Binning** (`nivel_estancia`, `nivel_poblacion`, `nivel_patrimonio`) |
| Enriquecer | Wikidata (QID, coordenadas, BIC), población INE y shapefile del CNIG |
| Outliers | z-score por CCAA, tipo y origen; se marca el registro y se conserva |
| Validar | T40 y la rama de control de T10 a T13 |
| Flujo de trabajo completo | `J00_carga.kjb` |

### 5.10 Reglas de PDI que condicionan el diseño

- Los pasos de una transformación **se ejecutan en paralelo** y sin orden garantizado; el orden lo impone el job.
- Todas las filas que llegan a un mismo paso deben tener la misma estructura (nombres, tipos y orden de campos).
- Una cadena vacía se trata como NULL por defecto.
- *Row denormaliser*, *Unique rows* y *Merge join* necesitan datos **ordenados** por las claves.
- *Text file input* lee los campos **por posición**, por eso la EOH (8 columnas) y el resto (7) tienen transformaciones distintas.
- Un único *Table output* por tabla de destino.

---

## 6. Estructura del repositorio

```
.
├── README.md
├── LICENSE
├── data/
│   ├── raw/             # descargas originales + ccaa_codigos.csv + registro de descargas
│   └── clean/           # CSV limpios generados por el ETL
├── docs/
│   ├── diseno_conceptual.drawio · .drawio.svg · .drawio.png
│   ├── diseno_logico.drawio · .drawio.svg · .drawio.png
│   ├── almacen_turismo.mwb                       # modelo de MySQL Workbench
│   ├── almacen_turismo_fisico.png · .svg · .pdf  # diagrama EER exportado
│   └── memoria.pdf
├── scripts/
│   ├── descargar_fuentes.py   # descarga INE y Wikidata
│   └── preparar_geometrias.py # shapefiles CNIG → data/clean/ccaa.geojson
├── sql/
│   └── 01_crear_almacen_turismo.sql
├── kettle/
│   ├── T01_dim_tiempo.ktr
│   ├── T02_dim_ccaa.ktr
│   ├── T10_eoh.ktr · T11_eoap.ktr · T12_eoac.ktr · T13_eotr.ktr
│   ├── T40_validacion.ktr
│   └── J00_carga.kjb
├── rdf/                 # tripletas schema.org (apartado 5)
└── visualizaciones/     # mapas y gráficas (apartado 6)
```

---

## 7. Cómo reproducir el trabajo

**Requisitos:**
- [Pentaho Data Integration (Community Edition)](https://pentaho-public.atlassian.net/wiki/spaces/COM/overview?mode=global) y la versión de Java que exija.
- MySQL 8 y MySQL Workbench.
- Python 3.8 o superior. El script de descarga no tiene dependencias; el de geometrías necesita `pip install pyshp shapely`.
- Conector JDBC de MySQL (`mysql-connector-j-*.jar`) copiado en `data-integration/lib` (reiniciar Spoon).

**Pasos:**

1. **Crear el almacén.** Ejecutar `sql/01_crear_almacen_turismo.sql` en MySQL Workbench.
2. **Configurar la conexión en Pentaho.** *View → Database connections → New*: tipo MySQL, acceso Native (JDBC), host `localhost`, puerto `3306`, base de datos `turismo_dw`, usuario y contraseña. Pulsar **Test**.
3. **Obtener los datos**: ejecutar `python scripts/descargar_fuentes.py`, descargar a mano el shapefile del CNIG (copiando las dos capas autonómicas a `data/raw/cnig/`) y ejecutar `python scripts/preparar_geometrias.py`, según la sección [Cómo obtener los datos](#cómo-obtener-los-datos).
4. **Ejecutar el job completo**, desde Spoon o por línea de comandos:

```bash
./kitchen.sh -file=kettle/J00_carga.kjb -level:Basic
```

5. **Comprobar la carga** con los resultados de `T40_validacion.ktr` o con consultas sobre el almacén, por ejemplo:

```sql
SELECT t.anio, c.nombre, SUM(f.pernoctaciones) AS pernoctaciones
FROM v_ocupacion_total f
JOIN dim_tiempo t ON t.tiempo_key = f.tiempo_key
JOIN dim_ccaa   c ON c.ccaa_key   = f.ccaa_key
GROUP BY t.anio, c.nombre
ORDER BY t.anio, pernoctaciones DESC;
```

---

## 8. Estado del proyecto

- [x] **Apartado 1:** temática, problema, 4W, objetivos, casos de uso y métricas
- [x] **Apartado 2:** necesidades de datos, selección y descarga de todos los datasets
- [x] **Apartado 3:** diseño conceptual, lógico (draw.io) y físico (MySQL Workbench), script SQL ejecutado en MySQL 8 y justificación
- [ ] **Apartado 4:** transformaciones y job de Pentaho _(diseño definido, implementación en curso)_
- [ ] **Apartado 5:** transformación a tripletas schema.org y enlace con Wikidata
- [ ] **Apartado 6:** dos visualizaciones (mapa coroplético y evolución temporal)
- [ ] **Apartado 7:** memoria (máximo 10 páginas)
- [ ] **Apartado 8:** repositorio final, licencia y referencias
- [ ] **Exposición y defensa:** 18 de diciembre de 2026 (fecha prevista, pendiente de confirmar)

---

## 9. Fuentes y referencias

**Estadística oficial**
- INE, [Hostelería y turismo (INEbase)](https://www.ine.es/dyngs/INEbase/es/categoria.htm?c=Estadistica_P&cid=1254735576863)
- INE, [Encuesta de Ocupación Hotelera](https://www.ine.es/jaxiT3/Tabla.htm?t=67190) · [Apartamentos](https://www.ine.es/jaxiT3/Tabla.htm?t=67191) · [Campings](https://www.ine.es/jaxiT3/Tabla.htm?t=67192) · [Turismo rural](https://www.ine.es/jaxiT3/Tabla.htm?t=67193)
- INE, [Estadística Continua de Población](https://ine.es/dynt3/metadatos/es/RespuestaDatos.html?oe=30282)
- [datos.gob.es](https://datos.gob.es/): catálogo nacional de datos abiertos

**Cartografía**
- CNIG/IGN, [Centro de Descargas](https://centrodedescargas.cnig.es/CentroDescargas/index.jsp)
- IGN, [WFS INSPIRE de unidades administrativas](https://www.ign.es/wfs-inspire/unidades-administrativas?request=GetCapabilities&service=WFS)

**Datos enlazados y enriquecimiento**
- [Wikidata Query Service](https://query.wikidata.org/)
- [OpenStreetMap, etiqueta `ref:bic`](https://wiki.openstreetmap.org/wiki/Key:ref:bic) y [Overpass Turbo](https://overpass-turbo.eu/)
- [schema.org](https://schema.org/) (vocabulario del apartado 5)

**Herramientas**
- [Pentaho Community Wiki](https://pentaho-public.atlassian.net/wiki/spaces/COM/overview?mode=global)
- [draw.io](https://www.drawio.com/) y [MySQL Workbench](https://www.mysql.com/products/workbench/)

**Material de la asignatura:** enunciado de la práctica y presentaciones de Pentaho (introducción y extracción de datos), Adquisición y preparación de datos, Universidad de Alicante.

---

## 10. Licencia

El código y la documentación del proyecto se distribuyen bajo licencia **MIT** (véase el fichero [`LICENSE`](LICENSE)).

Los datos proceden de las fuentes citadas en la sección anterior y mantienen las condiciones de uso de cada organismo (INE, CNIG/IGN, Wikidata). Se cita siempre la fuente original.