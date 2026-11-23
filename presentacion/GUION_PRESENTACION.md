# Guion de la presentación · ContentFlow EP3

Archivo: `ContentFlow_EP3_Presentacion.pptx` (15 diapositivas, cada una con notas del orador: quién habla, cuánto, qué mostrar y qué decir).
Duración estimada: **unos 18 minutos**. Si les dan 15, pasen rápido por las diapositivas 7 y 11.

## Reparto sugerido

| Orador | Diapositivas | Tema | Tiempo |
|:--|:--|:--|:--:|
| **Vicente** | 1 a 4 y 14 a 15 | Portada, necesidad, KPIs, arquitectura, hallazgos y cierre | 6:30 |
| **Ignacio** | 5 a 8 y 13 | Cosmos DB, pipeline, transformaciones, resultado y automatización | 6:30 |
| **Francisco** | 9 a 12 | Por qué Power BI, modelo, diseño y demostración en vivo | 5:30 |

Los tres deben saber responder las preguntas de la última sección.

## Antes de empezar (checklist)

1. Abrir **en este orden** estas pestañas o ventanas, ya con la sesión iniciada:
   1. Portal de Azure en el grupo de recursos `rg-contentflow-ep3`.
   2. Data Factory Studio con el pipeline `PL_ETL_ContentFlow_CosmosToBlob`.
   3. Power BI Desktop con `powerbi/ContentFlow.pbix` (en la página del dashboard).
   4. Power BI en el navegador, con el modelo semántico `ContentFlow` (Actualización → Historial).
2. Probar internet y el proyector. Cerrar notificaciones y otras aplicaciones.
3. Plan B: las diapositivas ya traen capturas de las partes que se muestran en vivo. Si algo falla, sigan con la captura y no se detengan.
4. Quien muestra en vivo comparte pantalla; los otros dos avisan «cambio de pantalla» y esperan.

## Qué mostrar en vivo, diapositiva por diapositiva

| N° | Diapositiva | Orador | Tiempo | Mostrar en vivo (y respaldo) |
|:--:|:--|:--|:--:|:--|
| 1 | Portada | Vicente | 0:30 | Nada. |
| 2 | La gerencia necesita decidir con datos | Vicente | 1:00 | Nada. |
| 3 | Cuatro KPIs | Vicente | 1:00 | Nada. |
| 4 | Arquitectura | Vicente | 1:30 | **Portal de Azure** → grupo `rg-contentflow-ep3` (3 recursos). Respaldo: el diagrama. |
| 5 | Cosmos DB for NoSQL | Ignacio | 1:00 | **Cosmos DB → Explorador de datos**: abrir un documento de `campanas` y ejecutar `SELECT VALUE COUNT(1) FROM c` (500). Respaldo: la captura. |
| 6 | Extracción con Data Factory | Ignacio | 1:30 | **Data Factory → Autor** → pipeline; clic en `Copiar_Campanas_Metas` → pestaña Origen (se ve la consulta). Respaldo: la captura. |
| 7 | Transformaciones | Ignacio | 1:30 | Nada obligatorio (la tabla basta). |
| 8 | Resultado en Blob | Ignacio | 1:00 | **Data Factory → Supervisar** (5 copias en Correcto) y **Blob → salida-etl** (5 CSV). Respaldo: las capturas. |
| 9 | Por qué Power BI | Francisco | 1:00 | Nada (opcional: Transformar datos para ver Power Query). |
| 10 | Modelo en estrella | Francisco | 1:00 | **Power BI Desktop → Vista de modelo**. Respaldo: el diagrama. |
| 11 | Diseño del dashboard | Francisco | 1:30 | Nada (boceto). |
| 12 | **Demostración en vivo** | Francisco | 2:00 | **Power BI Desktop, pantalla completa**: leer tarjetas, elegir un mes, clic en un objetivo, señalar la hora con más interacciones. |
| 13 | Automatización | Ignacio | 1:30 | **Data Factory → Supervisar → Ejecuciones de desencadenador** (ejecución automática de las 23:21) y **Power BI web → Historial de actualizaciones**. Respaldo: las capturas. |
| 14 | Hallazgos y límites | Vicente | 1:30 | Nada (opcional: volver al dashboard). |
| 15 | Conclusiones y preguntas | Vicente | 1:00 | Nada. |

## Qué decir

El texto de cada diapositiva está escrito en sus **notas del orador** (en PowerPoint: Vista → Notas, o la vista del presentador). Son 3 o 4 frases por diapositiva: léanlas como guía, no de memoria palabra por palabra.

Ideas que no pueden faltar:

- **Todo está en Azure** y se puede reproducir con la guía del repositorio.
- **Solo extraemos lo que la Tabla RICE conservó**; el correo y el texto libre no salen de la base.
- **Los resultados son pequeños y casi iguales entre objetivos** (0,69 %, 0,71 % y 0,72 %) porque los datos son sintéticos. Digan esto con calma, no como un problema.
- **Usuarios más activos** quedó como trabajo futuro.

## Preguntas probables

| Pregunta | Respuesta corta |
|:--|:--|
| ¿Por qué pasar por CSV en Blob y no conectar Power BI directo a Cosmos DB? | Blob separa la lectura de la base, evita gastar RU en cada actualización y permite actualización programada sin puerta de enlace. |
| ¿Cuánto cuesta? | Poco: Cosmos en modo Sin servidor, Data Factory con ejecuciones de menos de un minuto y Blob LRS. Detenemos el desencadenador al terminar. |
| ¿Cómo protegen los datos personales? | El correo, el género, el país, los hashtags y el texto no se extraen. Las claves no están en el repositorio. |
| ¿Por qué el cumplimiento es tan bajo? | Las metas (416.134) son muy altas frente a las interacciones registradas (2.944); los datos son sintéticos. |
| ¿Por qué 2.944 interacciones si hay 1.000 en total? | Una publicación puede estar en varias campañas y se cuenta en cada una (1.487 relaciones campaña-publicación). Los KPIs 3 y 4 cuentan cada interacción una sola vez. |
| ¿Qué es la Tabla RICE? | Un puntaje (alcance × impacto × confianza ÷ esfuerzo) para decidir qué atributos extraer: 1 o más se conserva, bajo 0,5 se descarta. |
| ¿Qué harían después? | Analizar usuarios más activos, limitar el cumplimiento a la ventana de cada campaña y alinear las frecuencias de actualización. |

## Pendientes antes de presentar

1. **Captura de la ejecución automática** del desencadenador (Data Factory → Supervisar → Ejecuciones de desencadenador, ejecución de las 23:21 «Disparada por programa»): guardarla como `Evidencias/EP3/ADF_Ejecucion_Desencadenador_Automatica.png`, agregarla a la diapositiva 13 y volver a generar el informe.
2. **Captura del dashboard final** (Power BI Desktop, pantalla completa): guardarla como `Evidencias/EP3/PowerBI_Dashboard_Final.png`. Sirve para el informe y como diapositiva de respaldo.
3. Revisar que los números del dashboard coincidan con los de la diapositiva 14 (0,71 %, 2.944 y 416.134).
4. Al terminar la evaluación, **detener el desencadenador `trigger1`** en Data Factory.
