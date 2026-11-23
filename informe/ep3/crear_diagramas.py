"""EP3 · Genera los diagramas del informe y de la presentación (matplotlib, sin datos sensibles).

    python informe/ep3/crear_diagramas.py

Salida: informe/ep3/diagramas/arquitectura.png, modelo_estrella.png, boceto_dashboard.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagramas")
os.makedirs(SALIDA, exist_ok=True)

TINTA, GRIS, CLARO = "#161B33", "#6B7390", "#F3F4FA"
VIOLETA, TURQUESA, AMBAR, BERMELLON = "#5B4BDB", "#00A896", "#F2A541", "#E4572E"


def caja(ax, x, y, w, h, color, fondo="#FFFFFF", radio=1.2, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radio}",
                                fc=fondo, ec=color, lw=lw))


def cabecera(ax, x, y, w, h, color, texto, tam=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.0",
                                fc=color, ec=color, lw=0))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", color="white",
            fontsize=tam, fontweight="bold")


def flecha(ax, x1, y1, x2, y2, color=TINTA, estilo="-|>", lw=2.0, **kw):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=estilo, mutation_scale=18,
                                 color=color, lw=lw, **kw))


# ------------------------------------------------------------------ arquitectura
def arquitectura():
    fig, ax = plt.subplots(figsize=(13, 5.6), dpi=200)
    ax.set_xlim(0, 100), ax.set_ylim(0, 44), ax.axis("off")
    cajas = [
        (2, VIOLETA, "FUENTE", "Azure Cosmos DB\nfor NoSQL",
         ["Base ContentFlowDB", "5 contenedores", "2.500 documentos", "Modo Sin servidor (RU)"]),
        (27, TURQUESA, "EXTRACCIÓN Y TRANSFORMACIÓN", "Azure Data Factory",
         ["Pipeline con 5 copias", "en paralelo", "Consultas SQL: proyección,", "aplanado, mes, JOIN"]),
        (52, AMBAR, "ALMACENAMIENTO", "Azure Blob Storage",
         ["Contenedor salida-etl", "5 archivos CSV limpios", "Sin datos personales", "Acceso privado (clave)"]),
        (77, BERMELLON, "VISUALIZACIÓN", "Power BI",
         ["Power Query + modelo", "en estrella + medidas DAX", "Dashboard interactivo", "con 4 KPIs"]),
    ]
    for x, color, rol, titulo, lineas in cajas:
        caja(ax, x, 15, 21, 25, color)
        cabecera(ax, x, 35.2, 21, 4.8, color, rol, tam=7.6 if len(rol) > 14 else 9)
        ax.text(x + 10.5, 31.0, titulo, ha="center", va="center", color=TINTA, fontsize=11.5,
                fontweight="bold", linespacing=1.15)
        for i, t in enumerate(lineas):
            ax.text(x + 10.5, 25.6 - i * 2.55, t, ha="center", va="center", color=GRIS, fontsize=8.6)
    for x, txt in ((23.2, "Lectura\n(proyección)"), (48.2, "Escritura\nCSV"), (73.2, "Conector\nAzure Blob")):
        flecha(ax, x, 27.5, x + 3.6, 27.5, lw=2.4)
        ax.text(x + 1.8, 31.1, txt, ha="center", va="center", color=TINTA, fontsize=7.4, linespacing=1.1)
    # banda de automatización
    caja(ax, 2, 1.5, 96, 9.6, TINTA, fondo=CLARO)
    ax.text(5, 8.6, "AUTOMATIZACIÓN", color=TINTA, fontsize=9, fontweight="bold", va="center")
    pasos = [("Desencadenador\nde Data Factory", TURQUESA), ("Pipeline copia\nlos datos a Blob", TURQUESA),
             ("CSV nuevos\nen salida-etl", AMBAR), ("Actualización programada\nde Power BI (1:00 a. m.)", BERMELLON)]
    xs = [6, 28, 50, 72]
    for (txt, color), x in zip(pasos, xs):
        caja(ax, x, 2.6, 20, 4.6, color, fondo="#FFFFFF", radio=0.9, lw=1.4)
        ax.text(x + 10, 4.9, txt, ha="center", va="center", color=TINTA, fontsize=7.6, linespacing=1.1)
    for x in (26.2, 48.2, 70.2):
        flecha(ax, x, 4.9, x + 1.7, 4.9, lw=1.8)
    fig.savefig(os.path.join(SALIDA, "arquitectura.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ------------------------------------------------------------------ modelo en estrella
def tabla(ax, x, y, w, nombre, campos, color, claves=()):
    alto_fila = 2.55
    h = 3.6 + alto_fila * len(campos) + 1.0
    caja(ax, x, y, w, h, color, radio=0.8)
    cabecera(ax, x, y + h - 3.6, w, 3.6, color, nombre, tam=9)
    for i, c in enumerate(campos):
        txt = c + ("  (clave)" if c in claves else "")
        ax.text(x + 1.4, y + h - 3.6 - 1.7 - i * alto_fila, txt, ha="left", va="center",
                color=TINTA if c in claves else GRIS, fontsize=7.8,
                fontweight="bold" if c in claves else "normal")
    return h


def modelo():
    fig, ax = plt.subplots(figsize=(13, 7.4), dpi=200)
    ax.set_xlim(0, 100), ax.set_ylim(0, 58), ax.axis("off")
    h_camp = tabla(ax, 1, 14, 24, "campanas", ["campana_id", "nombre", "objetivo", "fecha_inicio", "fecha_fin",
                   "mes_inicio", "meta_likes", "meta_comentarios", "meta_compartidos", "n_publicaciones"],
                   VIOLETA, ("campana_id",))
    tabla(ax, 38, 30, 21, "campana_publicacion", ["campana_id", "publicacion_id"], AMBAR)
    h_pub = tabla(ax, 72, 30, 26, "publicaciones", ["publicacion_id", "usuario_id", "categoria", "tipo",
                  "fecha_publicacion", "hora"], TURQUESA, ("publicacion_id",))
    tabla(ax, 47, 2, 24, "reacciones", ["reaccion_id", "publicacion_id", "usuario_id", "tipo_reaccion",
                                        "fecha", "mes"], BERMELLON)
    tabla(ax, 75, 2, 23, "comentarios", ["comentario_id", "publicacion_id", "usuario_id", "fecha", "mes",
                                         "likes"], BERMELLON)
    y_enlace = 36.0
    # campanas 1 --- * puente
    ax.plot([25, 38], [y_enlace, y_enlace], color=TINTA, lw=1.8)
    ax.text(26, y_enlace + 1.2, "1", fontsize=10, fontweight="bold")
    ax.text(36.2, y_enlace + 1.2, "*", fontsize=11, fontweight="bold")
    flecha(ax, 29.5, y_enlace, 32.5, y_enlace, lw=1.8)
    # publicaciones 1 --- * puente (ambas direcciones)
    ax.plot([59, 72], [y_enlace, y_enlace], color=TINTA, lw=1.8)
    ax.text(69.8, y_enlace + 1.2, "1", fontsize=10, fontweight="bold")
    ax.text(59.8, y_enlace + 1.2, "*", fontsize=11, fontweight="bold")
    flecha(ax, 62.4, y_enlace, 59.6, y_enlace, lw=1.8)
    flecha(ax, 65.0, y_enlace, 67.8, y_enlace, lw=1.8)
    ax.text(65.5, y_enlace - 2.6, "filtro en\nambas direcciones", ha="center", va="top", fontsize=7.2,
            color=GRIS, linespacing=1.1)
    # publicaciones 1 --- * reacciones / comentarios
    top_inferiores = 2 + 3.6 + 2.55 * 6 + 1.0          # borde superior de reacciones y comentarios
    ax.plot([76, 76, 59, 59], [30, 26.2, 26.2, top_inferiores + 2.2], color=TINTA, lw=1.8)
    ax.text(76.8, 27.8, "1", fontsize=10, fontweight="bold")
    ax.text(59.8, top_inferiores + 1.8, "*", fontsize=11, fontweight="bold")
    flecha(ax, 59, top_inferiores + 2.4, 59, top_inferiores + 0.1, lw=1.8)
    ax.plot([86.5, 86.5], [30, top_inferiores + 2.2], color=TINTA, lw=1.8)
    ax.text(87.3, 27.8, "1", fontsize=10, fontweight="bold")
    ax.text(87.3, top_inferiores + 1.8, "*", fontsize=11, fontweight="bold")
    flecha(ax, 86.5, top_inferiores + 2.4, 86.5, top_inferiores + 0.1, lw=1.8)
    ax.text(1, 56, "Modelo de datos en estrella (Power BI)", fontsize=13, fontweight="bold", color=TINTA)
    ax.text(1, 52.6, "Una tabla puente une campañas con publicaciones; reacciones y comentarios cuelgan de publicaciones.",
            fontsize=8.8, color=GRIS)
    fig.savefig(os.path.join(SALIDA, "modelo_estrella.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ------------------------------------------------------------------ boceto del dashboard
def boceto():
    fig, ax = plt.subplots(figsize=(13, 7.3), dpi=200)
    ax.set_xlim(0, 100), ax.set_ylim(0, 56), ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 100, 56, fc=CLARO, ec="#C9CCE0", lw=1.5))

    def panel(x, y, w, h, titulo, etiqueta=None):
        caja(ax, x, y, w, h, "#C9CCE0", fondo="#FFFFFF", radio=0.6, lw=1.2)
        ax.text(x + 1.2, y + h - 1.6, titulo, fontsize=8.2, fontweight="bold", color=TINTA, va="center")
        if etiqueta:
            cabecera(ax, x + w - 7.4, y + h - 3.0, 6.6, 2.4, VIOLETA, etiqueta, tam=6.8)

    ax.text(2, 53.2, "ContentFlow · Efectividad de campañas", fontsize=13, fontweight="bold", color=TINTA, va="center")
    ax.text(2, 50.3, "Cumplimiento = (reacciones + comentarios) ÷ (meta de likes + meta de comentarios)",
            fontsize=7.6, color=GRIS, va="center")
    for x, t in ((66, "Segmentador: mes de inicio"), (83, "Segmentador: objetivo")):
        caja(ax, x, 48.2, 15.5, 5.2, GRIS, fondo="#FFFFFF", radio=0.6, lw=1.2)
        ax.text(x + 7.75, 50.8, t, fontsize=7.4, color=TINTA, ha="center", va="center")
    # tarjetas
    for i, (t, v, e) in enumerate((("Cumplimiento de metas", "0,71 %", "KPI 1"), ("Interacciones", "2.944", "KPI 2"),
                                   ("Meta total", "416.134", "apoyo"))):
        x = 2 + i * 21.5
        caja(ax, x, 38.8, 20, 8.2, "#C9CCE0", fondo="#FFFFFF", radio=0.6, lw=1.2)
        ax.text(x + 1.2, 45.0, t, fontsize=7.8, color=GRIS, va="center")
        ax.text(x + 1.2, 41.2, v, fontsize=15, fontweight="bold", color=TINTA, va="center")
        cabecera(ax, x + 13.2, 39.5, 6, 2.3, VIOLETA if e.startswith("KPI") else GRIS, e, tam=6.8)
    caja(ax, 67, 38.8, 31, 8.2, AMBAR, fondo="#FFF8EB", radio=0.6, lw=1.2)
    ax.text(68.2, 42.9, "Nota: datos sintéticos; las diferencias entre\nobjetivos son pequeñas. La meta de\n“compartidos” no se mide (no hay datos).",
            fontsize=7.0, color=TINTA, va="center", linespacing=1.25)
    # gráficos fila 2
    panel(2, 18.4, 36, 18.4, "Cumplimiento % por objetivo", "KPI 1")
    for i, (h, c) in enumerate(((11.2, AMBAR), (10.9, TURQUESA), (10.6, VIOLETA))):
        ax.add_patch(Rectangle((6 + i * 10.4, 20.4), 6.4, h * 0.95, fc=c, ec="none"))
    panel(40, 18.4, 58, 18.4, "Cumplimiento % mensual por objetivo (mes de inicio)")
    xs = [44 + i * 5.1 for i in range(11)]
    for c, ys in ((VIOLETA, [8, 11, 9, 12, 10, 13, 9, 11, 12, 10, 13]), (TURQUESA, [10, 9, 12, 10, 11, 9, 12, 10, 9, 12, 10]),
                  (AMBAR, [12, 10, 11, 9, 13, 11, 10, 12, 11, 13, 11])):
        ax.plot(xs, [20.6 + y * 0.9 for y in ys], color=c, lw=2)
    # fila 3
    panel(2, 1.2, 30, 15.6, "Por formato de contenido", "KPI 3")
    for i, h in enumerate((8.6, 8.4, 8.0)):
        ax.add_patch(Rectangle((4.4, 12.0 - i * 3.6), h * 1.9, 2.4, fc=TURQUESA, ec="none"))
    panel(34, 1.2, 30, 15.6, "Por categoría", "KPI 3")
    for i, h in enumerate((8.6, 8.4, 8.1, 7.8, 7.4)):
        ax.add_patch(Rectangle((36.4, 13.0 - i * 2.35), h * 1.8, 1.6, fc=TURQUESA, ec="none"))
    panel(66, 1.2, 32, 15.6, "Por hora de publicación", "KPI 4")
    import random
    random.seed(3)
    for i in range(24):
        ax.add_patch(Rectangle((67.8 + i * 1.18, 2.8), 0.85, 2.0 + random.random() * 7.5, fc=AMBAR, ec="none"))
    fig.savefig(os.path.join(SALIDA, "boceto_dashboard.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    arquitectura()
    modelo()
    boceto()
    print("Diagramas en", SALIDA)
