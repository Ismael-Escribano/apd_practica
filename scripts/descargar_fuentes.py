#!/usr/bin/env python3
"""
Descarga las fuentes de datos del proyecto en data/raw/.

  INE        -> tablas CSV (separador ';') mediante la API de INEbase
  Wikidata   -> CCAA (QID, ISO, coordenadas) y nº de BIC por CCAA (SPARQL)

Uso:
  python scripts/descargar_fuentes.py                 # todo lo imprescindible
  python scripts/descargar_fuentes.py --solo ine      # tablas INE de ocupación
  python scripts/descargar_fuentes.py --solo poblacion
  python scripts/descargar_fuentes.py --solo ccaa     # Wikidata: CCAA
  python scripts/descargar_fuentes.py --solo bic      # Wikidata: nº de BIC
  python scripts/descargar_fuentes.py --opcionales    # añade tablas INE complementarias
  python scripts/descargar_fuentes.py --forzar        # vuelve a descargar lo ya existente
  python scripts/descargar_fuentes.py --dry-run       # solo muestra las URL

- Los ficheros que ya existen en data/raw/ NO se vuelven a descargar (usa --forzar).
- La población (82 MB) se guarda comprimida en .zip (así cabe en GitHub). Si ya tienes el
  .csv descargado, el script solo lo comprime, sin volver a descargarlo.
- Wikidata limita las peticiones (1 por minuto cuando hay incidencias): el script
  espera entre consultas y guarda cada lote por separado, de modo que si se corta
  basta con volver a ejecutarlo y continúa donde lo dejó.
- Solo usa la biblioteca estándar de Python (3.8+).
- Registro de descargas: data/raw/_descargas.log.csv
- NO descarga el shapefile del CNIG (se obtiene a mano, ver README).
"""
import argparse
import csv
import datetime
import hashlib
import io
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
UA = "ADP-UA-turismo/1.0 (proyecto academico, Universidad de Alicante)"

# ----------------------------------------------------------------- INE
INE_OCUPACION = {
    "67190": "eoh_viajeros_pernoctaciones_ccaa_provincias",
    "67191": "eoap_viajeros_pernoctaciones_ccaa",
    "67192": "eoac_viajeros_pernoctaciones_ccaa",
    "67193": "eotr_viajeros_pernoctaciones_ccaa",
}
# Complementarias (desglose por país). Pertenecen al sistema antiguo de INEbase y
# la API puede no servirlas; no son imprescindibles para el proyecto.
INE_OPCIONALES = {
    "67179": "eoh_pernoctaciones_ccaa_pais_residencia",
    "59162": "eoap_pernoctaciones_ccaa_pais_residencia",
    "67180": "eotr_pernoctaciones_ccaa_procedencia",
}
# Población residente por CCAA (Estadística Continua de Población, trimestral)
INE_POBLACION = {
    "56944": "ecp_poblacion_ccaa_sexo_nacionalidad_nacimiento",
}
INE_URLS = [  # se prueba en orden
    "https://ine.es/wstempus/csv_sc/es/DATOS_TABLA/{id}",
    "https://www.ine.es/jaxiT3/files/t/csv_bdsc/{id}.csv",
]

# ------------------------------------------------------------ Wikidata
WDQS = "https://query.wikidata.org/sparql"
ISO = ["ES-AN", "ES-AR", "ES-AS", "ES-IB", "ES-CN", "ES-CB", "ES-CL", "ES-CM",
       "ES-CT", "ES-VC", "ES-EX", "ES-GA", "ES-MD", "ES-MC", "ES-NC", "ES-PV",
       "ES-RI", "ES-CE", "ES-ML"]
LOTE = 4
PAUSA_WIKIDATA = 62  # segundos entre consultas


def values(iso):
    return " ".join(f'"{c}"' for c in iso)


def q_ccaa():
    return f"""SELECT ?ccaa ?ccaaLabel ?iso ?coord WHERE {{
  VALUES ?iso {{ {values(ISO)} }}
  ?ccaa wdt:P300 ?iso ;
        wdt:P17 wd:Q29 .
  OPTIONAL {{ ?ccaa wdt:P625 ?coord . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
ORDER BY ?iso"""


def q_bic(iso):
    return f"""SELECT ?iso ?ccaaLabel (COUNT(DISTINCT ?bien) AS ?n_bic) WHERE {{
  VALUES ?iso {{ {values(iso)} }}
  ?ccaa wdt:P300 ?iso ;
        wdt:P17 wd:Q29 .
  ?bien wdt:P808 ?codigo_bic ;
        wdt:P131/wdt:P131?/wdt:P131?/wdt:P131? ?ccaa .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
}}
GROUP BY ?iso ?ccaaLabel
ORDER BY ?iso"""


# --------------------------------------------------------------- util
def get(url, accept="*/*", reintentos=4, espera=5, timeout=120):
    ultimo = None
    for i in range(1, reintentos + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code == 429:  # límite de peticiones
                ra = e.headers.get("Retry-After") if e.headers else None
                pausa = int(ra) + 5 if ra and ra.isdigit() else 65
                print(f"   429 (límite de peticiones), intento {i}/{reintentos}: espero {pausa} s...")
                time.sleep(pausa)
            else:
                print(f"   intento {i}/{reintentos} fallido: {e}")
                time.sleep(espera * i)
        except (urllib.error.URLError, TimeoutError) as e:
            ultimo = e
            print(f"   intento {i}/{reintentos} fallido: {e}")
            time.sleep(espera * i)
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo}")


def guardar(nombre, datos, url, carpeta=None):
    destino = carpeta or RAW
    destino.mkdir(parents=True, exist_ok=True)
    (destino / nombre).write_bytes(datos)
    RAW.mkdir(parents=True, exist_ok=True)
    log = RAW / "_descargas.log.csv"
    nuevo = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(["fecha", "fichero", "bytes", "sha256", "url"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), nombre,
                    len(datos), hashlib.sha256(datos).hexdigest(), url])
    print(f"   OK  {nombre}  ({len(datos):,} bytes)")


def guardar_zip(nombre_csv, datos, url):
    """Guarda `datos` dentro de un .zip (mismo nombre que el CSV) y lo registra en el log."""
    RAW.mkdir(parents=True, exist_ok=True)
    nombre_zip = nombre_csv[:-4] + ".zip"
    with zipfile.ZipFile(RAW / nombre_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(nombre_csv, datos)
    tam = (RAW / nombre_zip).stat().st_size
    log = RAW / "_descargas.log.csv"
    nuevo = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(["fecha", "fichero", "bytes", "sha256", "url"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), nombre_zip,
                    tam, hashlib.sha256(datos).hexdigest(), url])
    print(f"   OK  {nombre_zip}  ({tam:,} bytes comprimido; {len(datos):,} sin comprimir)")


# ---------------------------------------------------------------- INE
def descargar_ine(tablas, dry, forzar, etiqueta, comprimir=False):
    print(f"== INE: {etiqueta} ==")
    for tid, alias in tablas.items():
        nombre = f"ine_{tid}_{alias}.csv"
        nombre_zip = nombre[:-4] + ".zip"
        urls = [u.format(id=tid) for u in INE_URLS]
        print(f"- tabla {tid}: {urls[0]}")
        if dry:
            continue
        if comprimir:
            if (RAW / nombre_zip).exists() and not forzar:
                print(f"   ya existe {nombre_zip}, se omite (usa --forzar para repetir)")
                continue
            if (RAW / nombre).exists() and not forzar:
                print(f"   {nombre} ya descargado: se comprime sin volver a descargar")
                guardar_zip(nombre, (RAW / nombre).read_bytes(), "(CSV local)")
                continue
        elif (RAW / nombre).exists() and not forzar:
            print(f"   ya existe {nombre}, se omite (usa --forzar para repetir)")
            continue
        for u in urls:
            try:
                datos = get(u)
                if len(datos) < 200:
                    muestra = datos[:150].decode("utf-8", errors="replace").strip()
                    raise RuntimeError(f"respuesta demasiado corta ({len(datos)} bytes): {muestra!r}")
                if comprimir:
                    guardar_zip(nombre, datos, u)
                else:
                    guardar(nombre, datos, u)
                break
            except Exception as e:  # noqa: BLE001
                print(f"   ! {e}")
        else:
            print(f"   NO DESCARGADA. Descarga manual: https://www.ine.es/jaxi/Tabla.htm?tpx={tid}"
                  f"  o  https://www.ine.es/jaxiT3/Tabla.htm?t={tid}")


# ----------------------------------------------------------- Wikidata
_ultima = [0.0]


def sparql_csv(consulta):
    falta = PAUSA_WIKIDATA - (time.time() - _ultima[0])
    if _ultima[0] and falta > 0:
        print(f"   espero {int(falta)} s (Wikidata limita las peticiones)...")
        time.sleep(falta)
    url = WDQS + "?" + urllib.parse.urlencode({"query": consulta})
    try:
        return get(url, accept="text/csv", timeout=90).decode("utf-8"), url
    finally:
        _ultima[0] = time.time()


def descargar_ccaa(dry, forzar):
    print("== Wikidata: CCAA ==")
    if dry:
        print(q_ccaa())
        return
    if (RAW / "wikidata_ccaa.csv").exists() and not forzar:
        print("   ya existe wikidata_ccaa.csv, se omite (usa --forzar para repetir)")
        return
    txt, url = sparql_csv(q_ccaa())
    filas = list(csv.reader(io.StringIO(txt)))
    print(f"   CCAA recibidas: {len(filas) - 1} (esperadas: 19)")
    guardar("wikidata_ccaa.csv", txt.encode("utf-8"), url)


def descargar_bic(dry, forzar):
    print("== Wikidata: BIC por CCAA (lotes de 4) ==")
    lotes = [ISO[i:i + LOTE] for i in range(0, len(ISO), LOTE)]
    if dry:
        print(q_bic(lotes[0]))
        return
    carpeta = RAW / "_lotes"
    for n, lote in enumerate(lotes, 1):
        f = carpeta / f"bic_lote{n}.csv"
        if f.exists() and not forzar:
            print(f"   lote {n}/{len(lotes)} ya descargado")
            continue
        print(f"   lote {n}/{len(lotes)}: {lote}")
        try:
            txt, url = sparql_csv(q_bic(lote))
        except RuntimeError as e:
            print(f"   ! {e}\n   Vuelve a ejecutar `--solo bic` en unos minutos: continúa por el lote {n}.")
            return
        guardar(f"bic_lote{n}.csv", txt.encode("utf-8"), url, carpeta=carpeta)
    # fusionar lotes
    cabecera, cuerpo = None, []
    for n in range(1, len(lotes) + 1):
        filas = list(csv.reader(io.StringIO((carpeta / f"bic_lote{n}.csv").read_text(encoding="utf-8"))))
        cabecera = filas[0]
        cuerpo += filas[1:]
    salida = io.StringIO()
    w = csv.writer(salida, lineterminator="\n")
    w.writerow(cabecera)
    w.writerows(cuerpo)
    print(f"   filas BIC: {len(cuerpo)} (esperadas: 19)")
    guardar("wikidata_bic_por_ccaa.csv", salida.getvalue().encode("utf-8"), WDQS)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--solo", choices=["ine", "poblacion", "ccaa", "bic"])
    p.add_argument("--opcionales", action="store_true", help="incluye tablas INE complementarias")
    p.add_argument("--forzar", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    todo = a.solo is None
    if todo or a.solo == "ine":
        descargar_ine(INE_OCUPACION, a.dry_run, a.forzar, "ocupación")
        if a.opcionales:
            descargar_ine(INE_OPCIONALES, a.dry_run, a.forzar, "complementarias")
    if todo or a.solo == "poblacion":
        descargar_ine(INE_POBLACION, a.dry_run, a.forzar, "población", comprimir=True)
    if todo or a.solo == "ccaa":
        descargar_ccaa(a.dry_run, a.forzar)
    if todo or a.solo == "bic":
        descargar_bic(a.dry_run, a.forzar)
    print("Terminado. Revisa data/raw/ y _descargas.log.csv")


if __name__ == "__main__":
    sys.exit(main())