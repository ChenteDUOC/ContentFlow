"""Pruebas de la extracción/transformación EP3 (sin Azure: base simulada con los JSON reales)."""
import extraccion_ep3 as ep3
from analitica_negocio import impacto_campanas


def _tablas(db):
    return ep3.transformar(ep3.extraer_db(db))


def test_proyeccion_no_extrae_datos_descartados(db):
    datos = ep3.extraer_db(db)
    for col, excluidos in {"usuarios": ["correo", "genero", "pais"],
                           "publicaciones": ["contenido", "hashtags"],
                           "comentarios": ["comentario"]}.items():
        for doc in datos[col]:
            assert not set(excluidos) & set(doc)


def test_tablas_sin_columnas_sensibles(db):
    tablas, _ = _tablas(db)
    prohibidas = {"correo", "genero", "pais", "contenido", "hashtags", "comentario"}
    for nombre, filas in tablas.items():
        assert not prohibidas & set(filas[0]), nombre


def test_conteos_y_desanidado(db):
    tablas, resumen = _tablas(db)
    assert len(tablas["dim_campanas"]) == 500
    asociadas = sum(c["n_publicaciones"] for c in tablas["dim_campanas"])
    assert len(tablas["puente_campana_publicacion"]) == asociadas
    assert resumen["filas_leidas"]["reacciones"] == len(tablas["fact_reacciones"]) == 500


def test_metas_aplanadas_y_mes(db):
    camp = _tablas(db)[0]["dim_campanas"][0]
    assert {"meta_likes", "meta_comentarios", "meta_compartidos", "mes_inicio"} <= set(camp)
    assert len(camp["mes_inicio"]) == 7 and camp["mes_inicio"][4] == "-"


def test_cumplimiento_coincide_con_analitica_existente(db):
    """El KPI por campaña debe dar lo mismo que analitica_negocio.impacto_campanas."""
    tablas, _ = _tablas(db)
    esperado = {d["campaña"]: d for d in impacto_campanas(db, top=500)[2]}
    for k in tablas["kpi_cumplimiento_campana"]:
        e = esperado[k["campana_id"]]
        assert k["interacciones"] == e["interacciones_observadas"]
        assert k["cumplimiento_pct"] == e["cumplimiento_pct"]


def test_kpi_mensual_suma_igual_que_kpi_por_campana(db):
    tablas, _ = _tablas(db)
    assert (sum(m["interacciones"] for m in tablas["kpi_cumplimiento_mensual"])
            == sum(k["interacciones"] for k in tablas["kpi_cumplimiento_campana"]))
    assert (sum(m["campañas"] for m in tablas["kpi_cumplimiento_mensual"]) == 500)


def test_modo_local_equivale_a_la_base(db):
    assert ep3.transformar(ep3.extraer_local())[0]["kpi_cumplimiento_mensual"] == \
        _tablas(db)[0]["kpi_cumplimiento_mensual"]
