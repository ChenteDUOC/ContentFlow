"""EP3 · Genera INFORME_TECNICO_EP3_CONTENTFLOW.pdf a partir de informe/ep3/INFORME_EP3.md.

    pip install markdown
    python informe/ep3/generar_informe_ep3.py

* Convierte el Markdown a HTML autocontenido (imágenes incrustadas) y lo imprime a PDF con
  Microsoft Edge en modo headless (viene con Windows; no hace falta instalar nada más).
* Si una imagen del informe todavía no existe (por ejemplo, la captura del dashboard final),
  el PDF muestra un recuadro amarillo "PENDIENTE" y el script lista lo que falta.
  Guarda la captura con ese nombre y vuelve a ejecutar el script.
"""
import base64
import html
import mimetypes
import os
import re
import shutil
import subprocess
import sys

import markdown

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
MD = os.path.join(AQUI, "INFORME_EP3.md")
HTML = os.path.join(AQUI, "informe_ep3.html")
PDF = os.path.join(RAIZ, "INFORME_TECNICO_EP3_CONTENTFLOW.pdf")

CSS = """
@page { size: Letter; margin: 2cm 1.9cm 2.1cm 1.9cm;
        @bottom-left { content: "ContentFlow · EP3 · BDY0101"; font: 8pt Calibri, Arial, sans-serif; color: #6B7390; }
        @bottom-right { content: "Página " counter(page); font: 8pt Calibri, Arial, sans-serif; color: #6B7390; } }
* { box-sizing: border-box; }
body { font-family: Calibri, Arial, sans-serif; font-size: 10.3pt; line-height: 1.38; color: #161B33; }
h1 { font-family: Cambria, Georgia, serif; font-size: 17pt; color: #5B4BDB; margin: 22pt 0 7pt;
     padding-bottom: 3pt; border-bottom: 1.6pt solid #5B4BDB; break-after: avoid; }
h1:first-of-type { font-size: 19pt; color: #161B33; border: none; margin-top: 0; }
h2 { font-family: Cambria, Georgia, serif; font-size: 12.5pt; color: #161B33; margin: 14pt 0 4pt; break-after: avoid; }
body > h2:first-of-type { font-size: 13pt; color: #5B4BDB; margin-top: 0; }
p { margin: 5pt 0; text-align: left; }
ul, ol { margin: 4pt 0 6pt 0; padding-left: 18pt; }
li { margin: 2pt 0; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.8pt; background: #F3F4FA; padding: 0 2pt; border-radius: 2pt; }
pre { background: #F3F4FA; border: 0.6pt solid #D8DBEE; border-radius: 4pt; padding: 6pt 8pt; font-size: 8.4pt;
      line-height: 1.32; white-space: pre-wrap; break-inside: avoid; margin: 5pt 0 8pt; }
pre code { background: none; padding: 0; font-size: 8.4pt; }
table { border-collapse: collapse; width: 100%; margin: 7pt 0 10pt; font-size: 9.3pt; break-inside: auto; }
th { background: #161B33; color: #fff; text-align: left; padding: 4pt 6pt; font-weight: 600; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #D8DBEE; vertical-align: top; }
tr { break-inside: avoid; }
tr:nth-child(even) td { background: #F8F8FC; }
body > table:first-of-type th { display: none; }
body > table:first-of-type td { border-bottom: 0.6pt solid #E3E5F2; padding: 3pt 6pt; }
body > table:first-of-type td:first-child { width: 22%; color: #5B4BDB; }
.toc { background: #F3F4FA; border-radius: 5pt; padding: 7pt 12pt; margin: 10pt 0 6pt; font-size: 9.6pt; }
.toc ul { list-style: none; padding-left: 0; margin: 0; columns: 2; column-gap: 20pt; }
.toc li { margin: 1.5pt 0; break-inside: avoid; }
.toc a { color: #161B33; text-decoration: none; }
figure { margin: 8pt 0 10pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; max-height: 8.6cm; border: 0.6pt solid #D8DBEE; border-radius: 3pt; }
figure.diagrama img { border: none; }
figcaption { font-size: 8.8pt; color: #6B7390; margin-top: 3pt; text-align: center; }
.pendiente { border: 1.2pt dashed #F2A541; background: #FFF8EB; border-radius: 4pt; padding: 12pt 10pt;
             text-align: center; color: #7A5200; font-size: 9.6pt; }
.pendiente code { background: #FFEFCF; }
strong { color: #161B33; }
"""


def incrustar(ruta_rel):
    ruta = os.path.join(RAIZ, ruta_rel.replace("/", os.sep))
    if not os.path.exists(ruta):
        return None
    tipo = mimetypes.guess_type(ruta)[0] or "image/png"
    with open(ruta, "rb") as f:
        return f"data:{tipo};base64,{base64.b64encode(f.read()).decode()}"


def construir_html():
    with open(MD, encoding="utf-8") as f:
        texto = f.read()
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists", "toc"],
                               extension_configs={"toc": {"toc_depth": "1", "title": ""}})
    # el índice generado por [TOC] se envuelve en un recuadro
    cuerpo = re.sub(r'(<div class="toc">)', r'\1<strong>Contenido</strong>', cuerpo, count=1)
    # el título del informe (primer h1) no debe aparecer en su propio índice
    cuerpo = re.sub(r'(<div class="toc">.*?<ul>)\s*<li><a href="[^"]*">INFORME T[^<]*</a></li>', r'\1', cuerpo,
                    count=1, flags=re.S)
    pendientes, n = [], [0]

    def figura(m):
        pie, ruta = html.unescape(m.group(1)), m.group(2)
        n[0] += 1
        etiqueta = f"Figura {n[0]}. {pie}"
        datos = incrustar(ruta)
        es_diagrama = "diagramas" in ruta
        if datos is None:
            pendientes.append(ruta)
            return (f'<figure><div class="pendiente"><strong>PENDIENTE</strong> · falta la imagen<br>'
                    f'<code>{html.escape(ruta)}</code></div><figcaption>{html.escape(etiqueta)}</figcaption></figure>')
        clase = ' class="diagrama"' if es_diagrama else ""
        return (f'<figure{clase}><img src="{datos}" alt="{html.escape(pie)}"/>'
                f'<figcaption>{html.escape(etiqueta)}</figcaption></figure>')

    cuerpo = re.sub(r'<p><img alt="(.*?)" src="(.*?)" ?/?></p>', figura, cuerpo)
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
           f'<title>Informe técnico EP3 · ContentFlow</title><style>{CSS}</style></head><body>{cuerpo}</body></html>')
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(doc)
    return pendientes


def buscar_navegador():
    candidatos = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                  r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return shutil.which("msedge") or shutil.which("chrome")


def main():
    pendientes = construir_html()
    nav = buscar_navegador()
    if not nav:
        print(f"No se encontró Edge/Chrome. Abre {HTML} en un navegador y guarda como PDF (Ctrl+P).")
        return 1
    if os.path.exists(PDF):
        os.remove(PDF)
    url = "file:///" + HTML.replace("\\", "/")
    perfil = os.path.join(AQUI, ".perfil_navegador")
    subprocess.run([nav, "--headless=new", "--disable-gpu", f"--user-data-dir={perfil}", "--no-pdf-header-footer",
                    "--print-to-pdf-no-header", f"--print-to-pdf={PDF}", url],
                   check=False, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(perfil, ignore_errors=True)
    if not os.path.exists(PDF):
        print("No se pudo generar el PDF.")
        return 1
    print("PDF listo:", PDF)
    if pendientes:
        print("\nImágenes que aún faltan (guárdalas con este nombre y vuelve a ejecutar):")
        for p in pendientes:
            print("  -", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
