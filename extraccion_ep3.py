"""EP3 · Extracción y transformación de ContentFlow para Power BI.

Lee de Azure Cosmos DB for MongoDB (PyMongo) las colecciones campañas,
publicaciones, reacciones, comentarios y usuarios, aplica las decisiones de la
Tabla RICE y deja tablas limpias (esquema en estrella) en exportes_ep3/*.csv.

Decisiones RICE que se implementan aquí:
  * Se extraen SOLO los atributos conservados (proyección en la consulta):
    no se piden correo, género, país, hashtags, contenido ni el texto del comentario.
  * metricas_objetivo se aplana en tres columnas (meta_likes/comentarios/compartidos).
  * fecha_inicio se convierte en mes (AAAA-MM); fecha_publicacion en hora, día y franja.
  * publicaciones_asociadas (arreglo) se desanida en una tabla puente.
  * Cumplimiento % = interacciones reales ÷ meta, con
        interacciones = reacciones + comentarios de las publicaciones asociadas
        meta          = meta_likes + meta_comentarios
    La meta de "compartidos" NO se usa: no existe una colección con compartidos
    reales (hallazgo documentado en la Tabla RICE).
  * El "mes" del cumplimiento es el mes de inicio de la campaña (mes_inicio).

Uso:
    python extraccion_ep3.py            # lee de Azure (necesita .env)
    python extraccion_ep3.py --local    # lee data/*.json, sin Azure (para probar)
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from pymongo.errors import PyMongoError

from config import (BASE_DIR, DATA_DIR, RESULTADOS_DIR, ConexionError,
                    conectar_db, get_logger)

log = get_logger("contentflow.ep3")

SALIDA_DEFECTO = os.path.join(BASE_DIR, "exportes_ep3")

# Atributos que se piden a la base (Tabla RICE: conservar). Lo demás no se extrae.
PROYECCION = {
    "campañas": ["nombre", "objetivo", "fecha_inicio", "fecha_fin",
                 "publicaciones_asociadas", "metricas_objetivo"],
    "publicaciones": ["usuario_id", "categoria", "tipo", "fecha_publicacion"],
    "reacciones": ["usuario_id", "publicacion_id", "tipo_reaccion", "fecha"],
    "comentarios": ["usuario_id", "publicacion_id", "fecha", "likes"],
    "usuarios": ["nombre", "dispositivo"],
}
EXCLUIDOS = {"usuarios": ["correo", "genero", "pais", "fecha_registro"],
             "publicaciones": ["contenido", "hashtags"],
             "comentarios": ["comentario (texto libre)"]}

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


# ----------------------------------------------------------------- extracción
def extraer_db(db):
    """Consulta cada colección con proyección (solo los atributos conservados)."""
    datos = {}
    for col, campos in PROYECCION.items():
        proy = {c: 1 for c in campos}
        datos[col] = list(db[col].find({}, proy))
        log.info("extraídos %d documentos de %s", len(datos[col]), col)
    return datos


def extraer_local():
    """Misma extracción pero desde data/*.json (modo sin Azure, para pruebas)."""
    archivos = {"campañas": "campañas.json", "publicaciones": "publicaciones.json",
                "reacciones": "reacciones.json", "comentarios": "comentarios.json",
                "usuarios": "usuarios.json"}
    datos = {}
    for col, archivo in archivos.items():
        with open(os.path.join(DATA_DIR, archivo), encoding="utf-8") as f:
            docs = json.load(f)
        datos[col] = [{k: d[k] for k in ["_id"] + PROYECCION[col] if k in d} for d in docs]
    return datos


# -------------------------------------------------------------- transformación
def _franja(hora):
    if hora < 6:
        return "Madrugada (00-05)"
    if hora < 12:
        return "Mañana (06-11)"
    if hora < 18:
        return "Tarde (12-17)"
    return "Noche (18-23)"


def _pct(parte, total):
    return round(100 * parte / total, 2) if total else 0.0


def transformar(datos):
    """Devuelve (tablas, resumen). tablas = {nombre: [filas dict]}."""
    pubs = {p["_id"]: p for p in datos["publicaciones"]}

    # --- dim_publicaciones: fecha ISO -> hora, día de la semana y franja
    dim_pub = []
    for p in datos["publicaciones"]:
        dt = datetime.fromisoformat(p["fecha_publicacion"])
        dim_pub.append({
            "publicacion_id": p["_id"], "usuario_id": p["usuario_id"],
            "categoria": p["categoria"], "tipo": p["tipo"],
            "fecha_publicacion": p["fecha_publicacion"],
            "hora": dt.hour, "dia_semana": DIAS[dt.weekday()], "franja": _franja(dt.hour)})

    # --- hechos de reacciones y comentarios (marcando fechas incoherentes)
    reac_pub, com_pub = Counter(), Counter()
    fact_reac, fact_com = [], []
    reac_antes = com_antes = 0
    for r in datos["reacciones"]:
        pf = pubs.get(r["publicacion_id"], {}).get("fecha_publicacion")
        antes = bool(pf and r["fecha"] < pf)
        reac_antes += antes
        reac_pub[r["publicacion_id"]] += 1
        fact_reac.append({"reaccion_id": r["_id"], "publicacion_id": r["publicacion_id"],
                          "usuario_id": r["usuario_id"], "tipo_reaccion": r["tipo_reaccion"],
                          "fecha": r["fecha"], "mes": r["fecha"][:7], "antes_de_publicar": antes})
    for c in datos["comentarios"]:
        pf = pubs.get(c["publicacion_id"], {}).get("fecha_publicacion")
        antes = bool(pf and c["fecha"] < pf)
        com_antes += antes
        com_pub[c["publicacion_id"]] += 1
        fact_com.append({"comentario_id": c["_id"], "publicacion_id": c["publicacion_id"],
                         "usuario_id": c["usuario_id"], "fecha": c["fecha"],
                         "mes": c["fecha"][:7], "likes": c.get("likes", 0),
                         "antes_de_publicar": antes})

    # --- campañas: aplanar metas, derivar mes, desanidar publicaciones
    dim_camp, puente, kpi_camp = [], [], []
    pubs_inexistentes = 0
    for c in datos["campañas"]:
        m = c.get("metricas_objetivo", {})
        mes = c["fecha_inicio"][:7]
        asociadas = c.get("publicaciones_asociadas", [])
        dim_camp.append({
            "campana_id": c["_id"], "nombre": c["nombre"], "objetivo": c["objetivo"],
            "fecha_inicio": c["fecha_inicio"], "fecha_fin": c["fecha_fin"], "mes_inicio": mes,
            "meta_likes": m.get("likes", 0), "meta_comentarios": m.get("comentarios", 0),
            "meta_compartidos": m.get("compartidos", 0), "n_publicaciones": len(asociadas)})
        for pid in asociadas:
            puente.append({"campana_id": c["_id"], "publicacion_id": pid})
            pubs_inexistentes += pid not in pubs
        reac = sum(reac_pub[pid] for pid in asociadas)
        com = sum(com_pub[pid] for pid in asociadas)
        meta = m.get("likes", 0) + m.get("comentarios", 0)
        kpi_camp.append({
            "campana_id": c["_id"], "nombre": c["nombre"], "objetivo": c["objetivo"],
            "mes_inicio": mes, "reacciones": reac, "comentarios": com,
            "interacciones": reac + com, "meta_likes": m.get("likes", 0),
            "meta_comentarios": m.get("comentarios", 0), "meta_total": meta,
            "cumplimiento_pct": _pct(reac + com, meta)})

    # --- KPI mensual por objetivo (suma de interacciones ÷ suma de metas)
    grupos = defaultdict(lambda: Counter())
    for k in kpi_camp:
        g = grupos[(k["mes_inicio"], k["objetivo"])]
        g["campañas"] += 1
        for campo in ("reacciones", "comentarios", "interacciones",
                      "meta_likes", "meta_comentarios", "meta_total"):
            g[campo] += k[campo]
    kpi_mensual = []
    for (mes, objetivo), g in sorted(grupos.items()):
        kpi_mensual.append({
            "mes_inicio": mes, "objetivo": objetivo, "campañas": g["campañas"],
            "reacciones": g["reacciones"], "comentarios": g["comentarios"],
            "interacciones": g["interacciones"], "meta_total": g["meta_total"],
            "pct_likes": _pct(g["reacciones"], g["meta_likes"]),
            "pct_comentarios": _pct(g["comentarios"], g["meta_comentarios"]),
            "cumplimiento_pct": _pct(g["interacciones"], g["meta_total"])})

    dim_usr = [{"usuario_id": u["_id"], "nombre": u.get("nombre"),
                "dispositivo": u.get("dispositivo")} for u in datos["usuarios"]]

    tablas = {
        "dim_campanas": dim_camp, "puente_campana_publicacion": puente,
        "dim_publicaciones": dim_pub, "dim_usuarios": dim_usr,
        "fact_reacciones": fact_reac, "fact_comentarios": fact_com,
        "kpi_cumplimiento_campana": kpi_camp, "kpi_cumplimiento_mensual": kpi_mensual,
    }
    resumen = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "filas_leidas": {c: len(d) for c, d in datos.items()},
        "filas_escritas": {t: len(f) for t, f in tablas.items()},
        "atributos_excluidos": EXCLUIDOS,
        "calidad": {"publicaciones_asociadas_inexistentes": pubs_inexistentes,
                    "reacciones_anteriores_a_la_publicacion": reac_antes,
                    "comentarios_anteriores_a_la_publicacion": com_antes},
    }
    return tablas, resumen


# ------------------------------------------------------------------ exportación
def exportar(tablas, resumen, salida=SALIDA_DEFECTO):
    import pandas as pd  # solo para escribir CSV (utf-8-sig: Power BI lee bien las tildes)
    os.makedirs(salida, exist_ok=True)
    rutas = []
    for nombre, filas in tablas.items():
        ruta = os.path.join(salida, f"{nombre}.csv")
        pd.DataFrame(filas).to_csv(ruta, index=False, encoding="utf-8-sig")
        rutas.append(ruta)
    os.makedirs(RESULTADOS_DIR, exist_ok=True)
    with open(os.path.join(RESULTADOS_DIR, "extraccion_ep3.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    return rutas


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="EP3: extracción y transformación para Power BI")
    ap.add_argument("--local", action="store_true", help="leer data/*.json en vez de Azure")
    ap.add_argument("--salida", default=SALIDA_DEFECTO, help="carpeta de salida de los CSV")
    args = ap.parse_args(argv)
    try:
        datos = extraer_local() if args.local else extraer_db(conectar_db())
        tablas, resumen = transformar(datos)
        exportar(tablas, resumen, args.salida)
    except ConexionError as e:
        print(f"[ERROR CRÍTICO] {e}")
        return 1
    except PyMongoError as e:
        log.exception("fallo en la extracción EP3")
        print(f"[ERROR BASE DE DATOS] {e}")
        return 1

    origen = "data/*.json (modo local)" if args.local else "Azure Cosmos DB"
    print(f"Origen: {origen}")
    print("Filas leídas:   ", resumen["filas_leidas"])
    print("Filas escritas: ", resumen["filas_escritas"])
    print("Calidad:        ", resumen["calidad"])
    print(f"CSV en: {args.salida}")
    log.info("extracción EP3 terminada: %s", resumen["filas_escritas"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
