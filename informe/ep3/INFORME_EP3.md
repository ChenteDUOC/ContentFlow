# INFORME TÉCNICO PARCIAL · EXPLOTACIÓN DE DATOS NoSQL PARA EL ANÁLISIS ORGANIZACIONAL
## Caso ContentFlow (Forma A) · Evaluación Parcial N°3 (20 %)

| | |
|:--|:--|
| **Institución** | Duoc UC · Sede Puerto Montt · Escuela de Informática y Telecomunicaciones |
| **Asignatura** | BDY0101 · Base de Datos No Relacionales |
| **Integrantes** | Carlos Ignacio Bittner Navea · Vicente Benjamin Alarcón Gallardo · Francisco Jesús Aranguiz Inostroza |
| **Tecnología** | Azure Cosmos DB for NoSQL · Azure Data Factory · Azure Blob Storage · Power BI (Desktop y servicio) |
| **Datos** | 5 contenedores · 2.500 documentos (500 por contenedor) |
| **Repositorio** | https://github.com/ChenteDev1/ContentFlow (carpetas `adf/`, `powerbi/`, `informe/ep3/` y `GUIA_EP3_AZURE.md`) |
| **Fecha** | 20 de noviembre de 2026 · Versión 1.0 |

[TOC]

# 1. Resumen ejecutivo

Construimos, íntegramente en Azure, un flujo que parte de los datos de ContentFlow en **Azure Cosmos DB for NoSQL**, los extrae y transforma con **Azure Data Factory** (5 consultas en paralelo, con solo los atributos que priorizamos en la Tabla RICE), los deja como 5 archivos CSV en **Blob Storage** y los explota en un **dashboard de Power BI** con 4 KPIs. El flujo se ejecuta y se actualiza de forma programada: un desencadenador de Data Factory regenera los CSV y el modelo semántico publicado en Power BI se actualiza todos los días.

Con los datos disponibles, el cumplimiento de las metas de las campañas es muy bajo en los tres tipos de objetivo (**0,69 %, 0,71 % y 0,72 %**) y casi no hay diferencias entre ellos. El conjunto de datos es sintético, así que el dashboard lo declara de forma explícita en lugar de forzar una conclusión.

# 2. Objetivos y motivación

ContentFlow es una plataforma de contenidos donde las personas publican, reaccionan, comentan y participan en campañas. La gerencia quiere identificar **a los usuarios más activos, los contenidos más populares y el impacto de las campañas**. En la EP2 dejamos los datos en la nube y los consultamos; la motivación de esta etapa es pasar de «consultar» a **explotar los datos para decidir**: llevarlos a una herramienta de análisis donde la gerencia vea indicadores y pueda filtrarlos sin escribir consultas.

**Objetivo general.** Diseñar e implementar un flujo de extracción, transformación y visualización de datos NoSQL en Azure y Power BI que responda las preguntas de negocio priorizadas con la Tabla RICE y se mantenga actualizado automáticamente.

**Objetivos específicos** (entre paréntesis, el indicador de la rúbrica que respalda cada uno):

1. Extraer datos de al menos tres contenedores de Cosmos DB con consultas que filtren, aplanen y desanidan documentos (IE1).
2. Transformar y limpiar los datos documentando y justificando cada decisión con la Tabla RICE (IE2).
3. Justificar el uso de Power BI y conectarlo de forma funcional a los datos transformados (IE3, IE4).
4. Modelar 4 KPIs claros, con su fórmula, su origen y su automatización (IE5).
5. Construir un dashboard claro e interactivo que destaque los KPIs y justificar cada visualización (IE6, IE7).
6. Automatizar la actualización de los datos y del informe (IE8).

# 3. Necesidad cubierta

La gerencia de ContentFlow necesita responder tres preguntas. La Tabla RICE concretó el análisis en «la efectividad de las campañas digitales y el cumplimiento mensual de las interacciones meta por tipo de objetivo» y planteó tres preguntas guía:

| Pregunta RICE | Dónde se responde |
|:--|:--|
| **De negocio:** ¿qué tipo de objetivo de campaña logra mayor % de cumplimiento mensual? | Dashboard, KPI 1 y KPI 2 |
| **Operativa:** ¿qué formato, categoría y horario concentran más reacciones? | Dashboard, KPI 3 y KPI 4 |
| **Técnica:** ¿qué atributos conviene extraer de Cosmos DB con Data Factory considerando estructura y costo en RU/s? | Pipeline de Data Factory y sección 5 de este informe |

La necesidad de la gerencia no se limita a las preguntas RICE: también pidió identificar a los usuarios más activos. Ese análisis queda fuera del dashboard actual (ver sección 12, «Limitaciones y trabajo futuro»), aunque el campo `usuario_id` ya viaja en las tablas extraídas.

# 4. Arquitectura de la solución

![Arquitectura: fuente → extracción y transformación → almacenamiento → visualización](informe/ep3/diagramas/arquitectura.png)

El flujo sigue el esquema pedido (**fuente → transformación → visualización**) con un almacenamiento intermedio:

1. **Fuente.** Azure Cosmos DB for NoSQL (base `ContentFlowDB`, 5 contenedores).
2. **Extracción y transformación.** Azure Data Factory lee con consultas SQL que ya proyectan, aplanan y desanidan los documentos.
3. **Almacenamiento.** Blob Storage guarda el resultado como CSV en el contenedor `salida-etl`.
4. **Visualización.** Power BI se conecta al Blob, termina la limpieza con Power Query, modela los datos y publica el dashboard.
5. **Automatización.** Un desencadenador programado de Data Factory regenera los CSV y una actualización programada de Power BI recarga el modelo.

Todo el flujo está en la misma región (North Central US) y en un grupo de recursos dedicado a esta entrega, `rg-contentflow-ep3`, separado del de la EP2.

# 5. Extracción de datos

## 5.1 Fuente de datos y carga

Los cinco archivos JSON del caso (`usuarios`, `publicaciones`, `reacciones`, `comentarios` y `campañas`, 500 documentos cada uno) se cargaron en `ContentFlowDB`. Cosmos DB for NoSQL exige que cada documento tenga un campo `id`, mientras que los JSON de origen traen `_id` (nombre de MongoDB). El script `preparar_carga_nosql.py` solo renombra `_id` → `id`; no filtra ni modifica nada más. Los archivos resultantes están en `data_cosmos_nosql/` y se subieron desde el Explorador de datos del portal.

![Cosmos DB: contenedores de ContentFlowDB y conteo de documentos (500)](Evidencias/EP3/EP3_Cosmos_ExplorerDatos_Conteo.png)

## 5.2 Recursos de Azure

| Recurso | Nombre | Configuración |
|:--|:--|:--|
| Grupo de recursos | `rg-contentflow-ep3` | North Central US |
| Cosmos DB for NoSQL | `cosmos-contentflow-ep3-alarcon` | Modo Sin servidor (se paga por RU consumidas); base `ContentFlowDB`; clave de partición `/id` |
| Contenedores | `campanas`, `publicaciones`, `reacciones`, `comentarios`, `usuarios` | 500 documentos cada uno |
| Cuenta de almacenamiento | `stcontentflowep3alarcon` | Blob, redundancia LRS; contenedor privado `salida-etl` |
| Data Factory | `adf-contentflow-ep3-alarcon` | Versión V2; servicios vinculados `LS_CosmosDB_ContentFlow` y `LS_Storage_Analitica` |

![Grupo de recursos rg-contentflow-ep3 con sus tres recursos](Evidencias/EP3/EP3_Azure_GrupoRecursos.png)

## 5.3 Pipeline y consultas

El pipeline `PL_ETL_ContentFlow_CosmosToBlob` tiene **5 actividades «Copiar datos» en paralelo**. Cada una lee un contenedor con una consulta SQL y escribe un CSV. Con esto se consultan cuatro contenedores (`campanas`, `publicaciones`, `reacciones` y `comentarios`), más de los tres que exige la evaluación. El JSON completo del pipeline está en `adf/PL_ETL_ContentFlow_CosmosToBlob.json`.

![Pipeline de Data Factory con las 5 copias en paralelo](Evidencias/EP3/EP3_ADF_Pipeline_5Copias.png)

**Copiar_Campanas_Metas** · aplana las metas anidadas y deriva el mes:

```sql
SELECT c.id AS campana_id, c.nombre, c.objetivo, c.fecha_inicio, c.fecha_fin,
       SUBSTRING(c.fecha_inicio, 0, 7)         AS mes_inicio,
       c.metricas_objetivo.likes               AS meta_likes,
       c.metricas_objetivo.comentarios         AS meta_comentarios,
       c.metricas_objetivo.compartidos         AS meta_compartidos,
       ARRAY_LENGTH(c.publicaciones_asociadas) AS n_publicaciones
FROM c
```

**Copiar_Campana_Publicacion** · desanida el arreglo: una fila por publicación asociada:

```sql
SELECT c.id AS campana_id, p AS publicacion_id
FROM c
JOIN p IN c.publicaciones_asociadas
```

**Copiar_Publicaciones** · omite `contenido` y `hashtags`; saca la hora del texto ISO:

```sql
SELECT c.id AS publicacion_id, c.usuario_id, c.categoria, c.tipo, c.fecha_publicacion,
       SUBSTRING(c.fecha_publicacion, 11, 2) AS hora
FROM c
```

**Copiar_Reacciones** y **Copiar_Comentarios** · derivan el mes; los comentarios no traen el texto:

```sql
SELECT c.id AS reaccion_id, c.usuario_id, c.publicacion_id, c.tipo_reaccion, c.fecha,
       SUBSTRING(c.fecha, 0, 7) AS mes
FROM c
```

```sql
SELECT c.id AS comentario_id, c.usuario_id, c.publicacion_id, c.fecha,
       SUBSTRING(c.fecha, 0, 7) AS mes, c.likes
FROM c
```

## 5.4 Ejecución y verificación

El pipeline se ejecutó correctamente: las cinco copias terminaron en estado **Correcto**. El detalle de `Copiar_Reacciones` muestra que se **leyeron 500 filas (100,16 KB) y se escribieron 500 filas (42,143 KB)**: sin pérdidas ni duplicados, y con menos de la mitad del volumen original porque la consulta solo trae los atributos necesarios.

![Supervisión de Data Factory: las 5 copias en estado Correcto](Evidencias/EP3/EP3_ADF_Supervisar_5Copias_Correcto.png)

![Detalle de la copia de reacciones: 500 filas leídas y 500 escritas](Evidencias/EP3/EP3_ADF_Detalle_Copia_Reacciones.png)

Los cinco CSV quedaron en el contenedor `salida-etl`:

![Contenedor salida-etl con los 5 CSV generados por el pipeline](Evidencias/EP3/EP3_Blob_5CSV_Primera_Carga.png)

# 6. Transformación y su justificación

## 6.1 Qué datos se eligieron y por qué (Tabla RICE)

La Tabla RICE puntúa cada atributo con **R × I × C ÷ E** (alcance, impacto, confianza y esfuerzo). Con un puntaje de 1 o más se conserva, entre 0,5 y 1 se evalúa y bajo 0,5 se descarta. Estos son los atributos clave y su destino en el flujo:

| Atributo | Colección | Puntaje | Decisión | Uso en el flujo |
|:--|:--|:--:|:--:|:--|
| `objetivo` | campañas | 3,00 | Conservar | Eje del KPI 1 |
| `publicacion_id` | reacciones | 2,85 | Conservar | Une cada reacción con su publicación y su campaña |
| `categoria` | publicaciones | 1,90 | Conservar | KPI 3 |
| `tipo_reaccion` | reacciones | 1,80 | Conservar | Se extrae; permite separar «Me gusta» del resto |
| `tipo` | publicaciones | 1,80 | Conservar | KPI 3 |
| `metricas_objetivo` | campañas | 1,35 | Conservar | Metas, denominador del cumplimiento (se aplana) |
| `fecha_inicio` | campañas | 1,35 | Conservar | Mes de la campaña (`mes_inicio`) |
| `fecha_publicacion` | publicaciones | 1,35 | Conservar | Hora de publicación, KPI 4 |
| `publicaciones_asociadas` | campañas | 1,27 | Conservar | Tabla puente (se desanida con `JOIN`) |
| `fecha_fin`, `likes` (comentarios), `fecha` (reacciones) | varias | 0,80 a 0,90 | Evaluar | Se extraen como apoyo; ver 6.4 |
| `hashtags` | publicaciones | 0,25 | Descartar | Multiplica filas y RU/s; la temática ya está en `categoria` |
| `correo` | usuarios | 0,23 | Descartar | Dato personal: no sale de la base operacional |
| `contenido` | publicaciones | 0,09 | Descartar | Texto libre largo y pesado |
| `genero`, `pais` | usuarios | 0,12 a 0,40 | Descartar | No cambian ninguna decisión del análisis |

Los atributos **descartados no se piden a Cosmos DB**: las consultas del pipeline los dejan fuera, lo que reduce los datos movidos y las RU consumidas. Además, no extraer `correo` protege datos personales.

## 6.2 Transformaciones aplicadas

| Transformación | Dónde | Por qué |
|:--|:--|:--|
| `_id` → `id` | `preparar_carga_nosql.py` | Cosmos DB for NoSQL exige el campo `id` |
| Proyección de atributos | Consultas de Data Factory | Solo se extrae lo conservado en el RICE (menos RU/s y menos datos) |
| Aplanado de `metricas_objetivo` | Consulta `Copiar_Campanas_Metas` | Un objeto anidado no es una columna; se convierte en `meta_likes`, `meta_comentarios` y `meta_compartidos` |
| Mes a partir de la fecha ISO | `SUBSTRING(fecha, 0, 7)` | Permite agrupar por mes (`AAAA-MM`) sin convertir fechas en el origen |
| Hora a partir de la fecha ISO | `SUBSTRING(fecha_publicacion, 11, 2)` | Permite medir el mejor horario |
| Desanidado de `publicaciones_asociadas` | `JOIN p IN c.publicaciones_asociadas` | Un arreglo se convierte en filas: una por cada pareja campaña-publicación |
| Renombrado de columnas | Alias `AS` en las consultas | Nombres claros y consistentes (`campana_id`, `publicacion_id`) |

## 6.3 Transformaciones en Power BI

En Power Query, cada CSV se abre como tabla con `Csv.Document`, se promueve la primera fila a encabezado y se asignan los tipos: enteros para las metas, `n_publicaciones`, `hora` y `likes`; fecha y hora para `fecha_inicio`, `fecha_fin`, `fecha_publicacion` y `fecha`; texto para el resto. La consulta `salida-etl` (la lista de archivos) queda sin carga: solo sirve de origen.

## 6.4 Calidad de datos y límites de las transformaciones

- **Fechas incoherentes.** La auditoría de la EP2 detectó 245 reacciones y 251 comentarios con fecha anterior a la publicación que reaccionan o comentan. Los marcamos pero no los eliminamos, así que siguen contando en los KPIs.
- **Atributos «Evaluar».** `fecha_fin` se extrae pero el cumplimiento **no** se limita a la ventana de la campaña (cuenta todas las interacciones de sus publicaciones). `likes` de los comentarios y `usuario_id` viajan en las tablas pero el dashboard actual no los usa.
- **Meta de «compartidos».** Existe en las campañas, pero ninguna colección registra compartidos reales; por eso no se mide.
- **Atribución por campaña.** Una publicación puede pertenecer a varias campañas. Para el cumplimiento, sus interacciones se cuentan en **cada** campaña que la incluye. Por eso el total del KPI 2 (2.944) es mayor que las 1.000 interacciones únicas del conjunto de datos (500 reacciones y 500 comentarios). Los KPIs 3 y 4 cuentan cada interacción una sola vez.

# 7. Por qué Power BI y cómo se conecta

## 7.1 Justificación

| Característica técnica de Power BI | Cómo la usamos |
|:--|:--|
| Conector nativo a Azure Blob Storage | Lee los CSV directamente, sin código ni intermediarios |
| Power Query (ETL integrado) | Convierte cada CSV en tabla, asigna tipos y deja la lista de archivos como origen |
| Modelo semántico con relaciones | Une 5 tablas en un modelo en estrella con filtro en ambas direcciones donde hace falta |
| Lenguaje DAX | Calcula las medidas de interacciones, meta y cumplimiento |
| Visuales interactivos y filtro cruzado | Segmentadores por mes y objetivo; al hacer clic en un gráfico se filtran los demás |
| Publicación en el servicio de Power BI | El informe y el modelo semántico quedan disponibles en línea |
| Actualización programada | Recarga el modelo desde Blob sin intervención (sin puerta de enlace, porque el origen está en la nube) |
| Integración con la identidad de Duoc | Se entra con la cuenta institucional |

**Comparación con lo que teníamos.** En la EP2 generamos un panel HTML estático con un script de Python: había que ejecutarlo a mano cada vez que cambiaban los datos y no tenía filtros. Power BI aporta interactividad y actualización programada, y el equipo de la gerencia puede explorar los datos sin programar.

## 7.2 Conexión

Power BI Desktop se conecta con **Obtener datos → Azure Blob Storage**, indicando la cuenta `stcontentflowep3alarcon` y su clave de acceso, y se selecciona el contenedor `salida-etl`. En el servicio de Power BI, el origen se configura con método de autenticación **Clave** y nivel de privacidad **Organizacional**. La clave la ingresa una persona del equipo; **no se guarda en el repositorio**.

# 8. Modelo de datos del dashboard

![Modelo de datos en estrella en Power BI](informe/ep3/diagramas/modelo_estrella.png)

| Relación | Cardinalidad | Filtro cruzado |
|:--|:--:|:--:|
| `campanas` → `campana_publicacion` por `campana_id` | 1 a varios | Sencillo |
| `publicaciones` → `campana_publicacion` por `publicacion_id` | 1 a varios | **Ambas direcciones** |
| `publicaciones` → `reacciones` por `publicacion_id` | 1 a varios | Sencillo |
| `publicaciones` → `comentarios` por `publicacion_id` | 1 a varios | Sencillo |

La tabla `campana_publicacion` resuelve la relación de muchos a muchos entre campañas y publicaciones. El filtro en ambas direcciones permite que una campaña (o un objetivo, o un mes) filtre sus publicaciones y, a través de ellas, sus reacciones y comentarios.

![Vista de modelo de Power BI con las 4 relaciones](Evidencias/EP3/EP3_PowerBI_Modelo_Relaciones.png)

**Medidas DAX** (tabla `campanas`):

```
Total reacciones   = SUMX(campana_publicacion, CALCULATE(COUNTROWS(reacciones)))
Total comentarios  = SUMX(campana_publicacion, CALCULATE(COUNTROWS(comentarios)))
Interacciones      = [Total reacciones] + [Total comentarios]
Meta total         = SUM(campanas[meta_likes]) + SUM(campanas[meta_comentarios])
Cumplimiento %     = DIVIDE([Interacciones], [Meta total])
```

Las medidas recorren la tabla puente para que cada interacción se atribuya a la campaña que corresponde. Si las relaciones están mal definidas, estas medidas dan resultados absurdos (ver el problema del 357 % en la sección 13).

# 9. KPIs

| KPI | Cómo se calcula | De dónde salen los datos | Cómo se automatiza |
|:--|:--|:--|:--|
| **KPI 1 · Cumplimiento de metas** (por objetivo y por mes) | `Cumplimiento %` = Interacciones ÷ Meta total, con interacciones = reacciones + comentarios de las publicaciones asociadas, y meta = meta de likes + meta de comentarios | `campanas_metas.csv`, `campana_publicacion.csv`, `reacciones.csv`, `comentarios.csv` | Pipeline de Data Factory programado + actualización programada de Power BI |
| **KPI 2 · Interacciones frente a la meta** | `Interacciones` y `Meta total` como tarjetas (2.944 frente a 416.134) | Los mismos archivos | Igual que el KPI 1 |
| **KPI 3 · Contenido más popular** (por formato y por categoría) | Reacciones + comentarios de cada publicación, agrupados por `tipo` y por `categoria` | `publicaciones.csv`, `reacciones.csv`, `comentarios.csv` | Igual que el KPI 1 |
| **KPI 4 · Mejor horario de publicación** | Reacciones + comentarios agrupados por la hora de publicación (0 a 23) | `publicaciones.csv`, `reacciones.csv`, `comentarios.csv` | Igual que el KPI 1 |

El **cumplimiento global es 0,71 %** (2.944 interacciones sobre 416.134 de meta). Se calcula con la misma lógica en el modelo de Power BI y en un script de control (`extraccion_ep3.py`) que replica el cálculo con Python sobre los JSON originales; ambos coinciden.

# 10. Diseño del dashboard

## 10.1 Boceto y principios de diseño

![Boceto del dashboard final con la ubicación de cada KPI](informe/ep3/diagramas/boceto_dashboard.png)

El dashboard es de **una sola página**, pensado para que la gerencia lo lea de arriba hacia abajo:

- **Lo más importante arriba y a la izquierda:** el título, los segmentadores y las tarjetas de KPI.
- **Un mensaje por gráfico**, con título descriptivo y etiquetas de datos.
- **Colores consistentes:** cada tipo de objetivo usa el mismo color en el gráfico de barras y en el de líneas.
- **Sin elementos decorativos ni gráficos de torta:** barras para comparar, líneas para el tiempo.
- **Honestidad de los datos:** una nota visible indica que los datos son sintéticos y que la meta de «compartidos» no se mide.

![Dashboard final de ContentFlow en Power BI](Evidencias/EP3/PowerBI_Dashboard_Final.png)

## 10.2 Justificación de cada visualización

| Visualización | Pregunta que responde | Por qué este tipo de gráfico |
|:--|:--|:--|
| **Tarjetas** (cumplimiento, interacciones, meta total) | ¿Cómo vamos en total? | Un número grande se lee de inmediato; es lo primero que busca una gerencia |
| **Barras: cumplimiento por objetivo** (KPI 1) | ¿Qué tipo de objetivo cumple mejor sus metas? | Las barras comparan categorías con claridad; muestra que las diferencias son mínimas |
| **Líneas: cumplimiento mensual por objetivo** (KPI 1) | ¿Cómo evoluciona mes a mes? | Las líneas muestran la tendencia en el tiempo; una línea por objetivo permite compararlos |
| **Barras: interacciones por formato** (KPI 3) | ¿Video, imagen o texto? | Pocas categorías, comparación directa |
| **Barras: interacciones por categoría** (KPI 3) | ¿Qué temáticas generan más respuesta? | Barras ordenadas permiten ver el ranking |
| **Columnas: interacciones por hora** (KPI 4) | ¿A qué hora conviene publicar? | Una columna por hora (0 a 23) muestra el patrón del día |
| **Segmentadores** (mes de inicio y objetivo) | ¿Y si miro solo un mes o un objetivo? | Filtran todo el dashboard a la vez |
| **Nota de datos** | ¿Puedo confiar en estas diferencias? | Evita sobreinterpretar un conjunto de datos sintético |

# 11. Automatización y actualización

La automatización tiene dos eslabones encadenados:

1. **Data Factory (desencadenador `trigger1`).** Es un desencadenador de tipo *Schedule* asociado al pipeline `PL_ETL_ContentFlow_CosmosToBlob`, configurado para ejecutarse cada 2 días a las 23:21 (zona horaria de Santiago) entre el 20 y el 23 de noviembre de 2026, periodo de la evaluación. Cada ejecución vuelve a leer Cosmos DB y sobrescribe los 5 CSV de `salida-etl`.
2. **Power BI (actualización programada).** El modelo semántico `ContentFlow`, publicado en «Mi área de trabajo», tiene la actualización programada activada con frecuencia **diaria a la 1:00 a. m.** (UTC-04:00, Santiago). Las credenciales del origen Azure Blob están configuradas con método Clave y privacidad Organizacional.

![Configuración del desencadenador programado de Data Factory](Evidencias/EP3/EP3_ADF_Desencadenador_Config.png)

**Pruebas realizadas.** Ejecutamos el pipeline a mano a las 22:29:56: terminó en estado Correcto en 31 s y los 5 CSV quedaron con fecha de modificación 20/11/2026 22:30. Luego actualizamos el modelo de Power BI a petición y el historial muestra dos actualizaciones completadas (22:22 y 22:32).

![Ejecución manual del pipeline en Data Factory (Correcto, 31 s)](Evidencias/EP3/ADF_Supervisar_Ejecucion_Manual.jpg)

![Los 5 CSV con la fecha de modificación de la ejecución manual](Evidencias/EP3/Blob_salida-etl_CSV_actualizados.jpg)

![Historial de actualizaciones de Power BI y programación diaria](Evidencias/EP3/PowerBI_Historial_Actualizaciones.jpg)

**Evidencia de ejecución automática.** Sin intervención nuestra, el desencadenador `trigger1` se ejecutó el 20/11/2026 a las 23:21 y terminó en estado *Succeeded*. Disparó una ejecución del pipeline `PL_ETL_ContentFlow_CosmosToBlob` (23:21:00 a 23:21:24, 25 s, «Triggered by: trigger1»), y los 5 CSV de `salida-etl` quedaron con fecha de modificación 20/11/2026 23:21.

![Ejecución del desencadenador trigger1 en Data Factory (Succeeded, 20/11/2026 23:21)](Evidencias/EP3/ADF_Supervisar_Ejecucion_Desencadenador.jpg)

![Ejecución del pipeline disparada por trigger1 (25 s, Succeeded)](Evidencias/EP3/ADF_Supervisar_Pipeline_por_trigger1.jpg)

![Los 5 CSV con la fecha de modificación de la ejecución de trigger1 (23:21)](Evidencias/EP3/Blob_salida-etl_CSV_tras_trigger1.jpg)

A continuación, Power BI actualizó el modelo por su cuenta según la programación diaria. El historial muestra dos actualizaciones de tipo **Programado** completadas: 21/11/2026 1:00 a. m. (terminó 1:02) y 22/11/2026 1:00 a. m. (terminó 1:05), además de las dos de prueba «A petición» del 20/11. Con esto queda demostrada la cadena completa sin intervención manual: Cosmos DB → Data Factory → Blob → Power BI.

![Historial de actualizaciones de Power BI con las ejecuciones programadas](Evidencias/EP3/PowerBI_Historial_Actualizacion_Programada.jpg)

**Consideraciones.** Las frecuencias se fijaron para la ventana de evaluación y controlan el costo. Como el pipeline corre cada 2 días y Power BI se actualiza todos los días, algunas actualizaciones de Power BI recargan datos que no cambiaron; es inofensivo, y en un entorno real convendría alinear ambas frecuencias. Al terminar la evaluación se detiene `trigger1`.

# 12. Resultados y hallazgos

- **Cumplimiento por objetivo:** Promover contenido 0,72 %, Captar nuevos usuarios 0,71 % y Aumentar engagement 0,69 %. La diferencia entre el mejor y el peor es de 0,03 puntos porcentuales: con estos datos **no se puede afirmar que un objetivo funcione mejor que otro**.
- **Cumplimiento global:** 0,71 %. Las metas (416.134) son muy altas frente a las interacciones registradas (2.944).
- **Formato:** hay más interacciones en Imagen (369) que en Video (338) y Texto (293), pero eso se debe a que hay más publicaciones de imagen: el promedio por publicación es casi igual (2,01; 2,02 y 1,97).
- **Categoría:** Tecnología (220) y Educación (214) suman más interacciones; por publicación, Entretenimiento (2,12) y Educación (2,10) son las más altas y Cultura (1,88) la más baja.
- **Horario:** la hora con más interacciones es las 17:00 (59), seguida de las 08:00 (56) y la 01:00 (55). Por franja, la **tarde (12 a 17 h)** tiene el mejor promedio (2,16 interacciones por publicación) frente a la noche (1,89).

Todas estas diferencias son pequeñas. El conjunto de datos es sintético y de tamaño reducido (500 publicaciones), así que sirven para demostrar el flujo y el dashboard, no para tomar decisiones reales de contenido.

**Limitaciones y trabajo futuro.** (1) Incorporar el análisis de **usuarios más activos**, extrayendo la colección `usuarios` con los atributos que el RICE considere (por ejemplo, `dispositivo`) y sin datos personales. (2) Limitar el cumplimiento a la ventana de cada campaña usando `fecha_fin`. (3) Medir «compartidos» si la plataforma llega a registrarlos. (4) Alinear la frecuencia del pipeline con la de la actualización de Power BI.

# 13. Problemas encontrados y soluciones

| Problema | Causa | Solución |
|:--|:--|:--|
| Error `RequestDisallowedByAzure` al crear Cosmos DB | La política de Azure for Students restringe regiones | Usar la región **North Central US** y habilitar zonas de disponibilidad |
| El arreglo de compras no llegaba al archivo (LAB 3.1.2) | La asignación (*mapping*) de Data Factory aplana los arreglos | Renombrar con alias en la consulta de origen y dejar la asignación vacía; en ContentFlow las consultas ya salen planas |
| Error 404 al importar el esquema del destino | El archivo de salida todavía no existe | Elegir «Importar esquema: Ninguno» |
| Power BI Desktop: error 700003 al iniciar sesión | Registro antiguo del equipo en la cuenta de la organización | Desconectar la cuenta en *Acceso a trabajo o escuela* de Windows, reiniciar y volver a iniciar sesión |
| El cumplimiento mostraba 357 % en lugar de menos de 1 % | Faltaban relaciones en el modelo, así que cada fila contaba todas las reacciones | Crear las relaciones con filtro en ambas direcciones entre `publicaciones` y `campana_publicacion` |
| La tabla `publicaciones` traía columnas de comentarios | Se había cargado el archivo equivocado | Eliminar la consulta y volver a crearla desde `publicaciones.csv` |

# 14. Costos y seguridad

- **Costos.** Cosmos DB en modo Sin servidor (se paga solo por lo consumido), Blob con redundancia local (LRS) y Data Factory con ejecuciones de menos de un minuto cuestan muy poco; aun así el crédito de Azure for Students es limitado, por lo que `trigger1` se detiene al terminar.
- **Seguridad.** Las claves de Cosmos DB y de Blob nunca se escriben en el repositorio; los JSON de Data Factory exportados no contienen secretos. El contenedor `salida-etl` es privado. Los datos personales (`correo`) no salen de la base operacional.

# 15. Conclusiones

1. El flujo **Cosmos DB → Data Factory → Blob → Power BI** funciona de punta a punta en Azure y se puede reproducir con la guía `GUIA_EP3_AZURE.md` y los JSON del repositorio.
2. La **Tabla RICE** fue útil como criterio técnico: permitió extraer solo lo necesario (menos RU/s y menos datos movidos) y dejar fuera los datos personales y el texto libre.
3. Power BI aporta lo que el panel HTML de la EP2 no tenía: **interactividad y actualización programada**.
4. Los resultados muestran un cumplimiento de metas muy bajo y casi idéntico entre objetivos; por tratarse de datos sintéticos, la lección principal es de método: declarar los límites en lugar de forzar conclusiones.
5. Quedan como mejora el análisis de usuarios activos y alinear las frecuencias de actualización.

# Anexo A · Cómo reproducir el flujo

1. Crear el grupo de recursos, la cuenta de Cosmos DB for NoSQL (Sin servidor), la cuenta de almacenamiento y Data Factory con los nombres de la sección 5.2 (cambiando el sufijo `alarcon`, que debe ser único en Azure).
2. Generar los JSON con `id` (`python preparar_carga_nosql.py`) y subirlos a los 5 contenedores.
3. Crear los servicios vinculados, los 9 conjuntos de datos y el pipeline; importar `adf/PL_ETL_ContentFlow_CosmosToBlob.json` o pegar las consultas de la sección 5.3.
4. Ejecutar el pipeline y comprobar los 5 CSV en `salida-etl`.
5. Abrir `powerbi/ContentFlow.pbix`, apuntar al nuevo Blob y actualizar.
6. Programar el desencadenador y la actualización del modelo semántico.

El paso a paso con los nombres de cada botón está en `GUIA_EP3_AZURE.md`.

# Anexo B · Archivos de la EP3 en el repositorio

| Ruta | Contenido |
|:--|:--|
| `GUIA_EP3_AZURE.md` | Guía paso a paso del flujo en Azure y Power BI |
| `adf/PL_ETL_ContentFlow_CosmosToBlob.json` | Pipeline exportado de Data Factory (sin secretos) |
| `preparar_carga_nosql.py`, `data_cosmos_nosql/` | Conversión `_id` → `id` y archivos listos para cargar |
| `extraccion_ep3.py`, `tests/test_extraccion_ep3.py` | Script de control que replica la transformación en Python y sus pruebas |
| `powerbi/ContentFlow.pbix` | Informe y modelo de Power BI |
| `informe/ep3/` | Este informe, sus diagramas y el generador del PDF |
| `Evidencias/EP3/` | Capturas de Azure y Power BI |
