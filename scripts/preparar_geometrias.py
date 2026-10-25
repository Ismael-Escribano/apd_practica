#!/usr/bin/env python3
"""
Genera data/clean/ccaa.geojson a partir de los shapefiles de comunidades
autónomas del CNIG/IGN (Base de Datos de Divisiones Administrativas de España).

Entrada (se buscan de forma recursiva dentro de data/raw/cnig/):
  recintos_autonomicas_inspire_peninbal_etrs89.shp   (Península, Baleares, Ceuta, Melilla)
  recintos_autonomicas_inspire_canarias_wgs84.shp    (Canarias)
Ambos vienen en coordenadas geográficas (lon/lat), compatibles con WGS84:
no hace falta reproyectar.

Salida: GeoJSON con 19 entidades y las propiedades codigo_ine, codigo_iso, nombre.
Cada CCAA se identifica por su nombre (atributo NAMEUNIT) y se concilia con
data/raw/ccaa_codigos.csv. Las geometrías se simplifican (--tolerancia, en grados)
para que el mapa sea ligero.

Requisitos:  pip install pyshp shapely
Uso:         python scripts/preparar_geometrias.py [--tolerancia 0.003]
"""
import argparse
import csv
import json
import sys
import unicodedata
from pathlib import Path

import shapefile                      # pyshp
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "raw" / "cnig"
CODIGOS = RAIZ / "data" / "raw" / "ccaa_codigos.csv"
SALIDA = RAIZ / "data" / "clean" / "ccaa.geojson"

# Palabras clave (sin tildes, en minúscula) para reconocer cada CCAA por su nombre
CLAVES = {
    "01": ["andaluc"], "02": ["aragon"], "03": ["asturias"], "04": ["balears", "baleares"],
    "05": ["canarias"], "06": ["cantabria"], "07": ["castilla y leon", "castilla-leon"],
    "08": ["mancha"], "09": ["catalu"], "10": ["valenc"], "11": ["extremadura"],
    "12": ["galicia"], "13": ["madrid"], "14": ["murcia"], "15": ["navarra"],
    "16": ["pais vasco", "euskadi"], "17": ["rioja"], "18": ["ceuta"], "19": ["melilla"],
}


def normalizar(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()


def codigo_de(nombre):
    n = normalizar(nombre)
    hallados = [c for c, claves in CLAVES.items() if any(k in n for k in claves)]
    return hallados[0] if len(hallados) == 1 else None


def leer(shp):
    r = shapefile.Reader(str(shp), encoding="utf-8")
    campos = [f[0] for f in r.fields[1:]]
    for sr in r.shapeRecords():
        yield dict(zip(campos, sr.record)), sr.shape


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tolerancia", type=float, default=0.003,
                    help="simplificación en grados (0.003 ≈ 300 m); 0 = sin simplificar")
    a = ap.parse_args()

    ficheros = sorted(ENTRADA.rglob("recintos_autonomicas*.shp"))
    if not ficheros:
        sys.exit(f"No encuentro 'recintos_autonomicas*.shp' dentro de {ENTRADA}.\n"
                 "Copia allí las carpetas SHP_ETRS89 y SHP_WGS84 del zip del CNIG.")
    print("Shapefiles:", *[str(f.relative_to(RAIZ)) for f in ficheros], sep="\n  ")

    info = {r["codigo_ine"]: r for r in csv.DictReader(CODIGOS.open(encoding="utf-8"), delimiter=";")}
    partes, sin_codigo = {}, []
    for f in ficheros:
        for rec, shp in leer(f):
            nombre = rec.get("NAMEUNIT") or rec.get("NAME") or ""
            cod = codigo_de(nombre)
            if cod is None:
                sin_codigo.append(rec)
                continue
            geom = shape(shp.__geo_interface__)
            partes.setdefault(cod, []).append(geom if geom.is_valid else geom.buffer(0))

    # El CNIG incluye un recinto "Territorios no asociados a ninguna autonomía":
    # no es ninguna de las 19 CCAA y se descarta expresamente.
    ignorados = [r for r in sin_codigo if "no asociad" in normalizar(r.get("NAMEUNIT", ""))]
    sin_codigo = [r for r in sin_codigo if r not in ignorados]
    for r in ignorados:
        print(f"Descartado (no es una CCAA): {r.get('NAMEUNIT')}")

    if sin_codigo or len(partes) != 19:
        print(f"\nCCAA identificadas: {len(partes)} de 19. Registros sin identificar: {len(sin_codigo)}")
        for rec in sin_codigo[:25]:
            print("  ", {k: rec[k] for k in rec if k in ("NAMEUNIT", "NATCODE", "CODNUT2", "NATLEVNAME")})
        faltan = sorted(set(info) - set(partes))
        print("  Faltan los códigos INE:", faltan)
        sys.exit("Revisa los nombres anteriores y ajusta CLAVES en el script.")

    features = []
    for cod in sorted(partes):
        g = unary_union(partes[cod])
        if a.tolerancia > 0:
            g = g.simplify(a.tolerancia, preserve_topology=True)
        features.append({
            "type": "Feature",
            "properties": {"codigo_ine": cod, "codigo_iso": info[cod]["codigo_iso"],
                           "nombre": info[cod]["nombre"]},
            "geometry": mapping(g),
        })
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps({"type": "FeatureCollection", "features": features},
                       ensure_ascii=False, separators=(",", ":"))
    SALIDA.write_text(texto, encoding="utf-8")
    print(f"OK: {SALIDA.relative_to(RAIZ)} · {len(features)} CCAA · {len(texto) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()