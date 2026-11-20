# Guía EP3 · ContentFlow en Azure (paso a paso)

Flujo completo, todo en Azure:

```
Cosmos DB for NoSQL  ->  Azure Data Factory  ->  Blob Storage (CSV)  ->  Power BI
 (ContentFlowDB)         (pipeline, 5 copias)     (salida-etl)           (dashboard + KPIs)
                                ^
                       desencadenador programado (automatización)
```

> **Para quien reproduzca esto:** los nombres de Cosmos, Storage y Data Factory son únicos en todo
> Azure. Cambie el sufijo `alarcon` por el suyo. Nunca suba claves de conexión al repositorio.
> Los nombres de botones están en español; si su portal está en inglés, el equivalente va entre paréntesis.

## Nombres que usaremos

| Recurso | Nombre |
|---|---|
| Grupo de recursos | `rg-contentflow-ep3` |
| Región (todo) | **North Central US** (en Azure for Students otras regiones pueden dar `RequestDisallowedByAzure`) |
| Cuenta Cosmos DB for NoSQL (Sin servidor) | `cosmos-contentflow-ep3-alarcon` |
| Base de datos | `ContentFlowDB` |
| Contenedores (clave de partición `/id`) | `campanas`, `publicaciones`, `reacciones`, `comentarios`, `usuarios` |
| Cuenta de almacenamiento | `stcontentflowep3alarcon` |
| Contenedor Blob | `salida-etl` |
| Data Factory | `adf-contentflow-ep3-alarcon` |
| Servicios vinculados | `LS_CosmosDB_ContentFlow`, `LS_Storage_Analitica` |
| Pipeline | `PL_ETL_ContentFlow_CosmosToBlob` |

Archivos de datos listos para subir (ya generados): carpeta `data_cosmos_nosql/` (son los JSON del caso con `_id` renombrado a `id`).
Si hay que regenerarlos: `python preparar_carga_nosql.py`.

---

## Fase 1 · Grupo de recursos
1. portal.azure.com → barra de búsqueda → `Grupos de recursos` → **+ Crear**.
2. Suscripción: *Azure for Students*. Grupo de recursos: `rg-contentflow-ep3`. Región: **North Central US**.
3. **Revisar y crear** → **Crear**.
- Resultado esperado: el grupo aparece en la lista.

## Fase 2 · Cuenta de Cosmos DB for NoSQL
1. Buscar `Azure Cosmos DB` → **+ Crear** → API **Azure Cosmos DB for NoSQL** → **Crear**.
2. Aspectos básicos: grupo `rg-contentflow-ep3`; nombre `cosmos-contentflow-ep3-alarcon`; ubicación **North Central US**;
   modo de capacidad **Sin servidor** (*Serverless*); zonas de disponibilidad **habilitadas**.
3. **Revisar y crear** → **Crear** (tarda varios minutos) → **Ir al recurso**.
- Resultado esperado: "Se completó la implementación".

## Fase 3 · Base de datos, contenedores y carga de datos
Dentro de la cuenta Cosmos → menú izquierdo → **Explorador de datos**.
1. **Nuevo contenedor** → Id de base de datos: *Crear nuevo* → `ContentFlowDB`.
2. Id de contenedor: `campanas`; clave de partición: `/id` → **Aceptar**.
3. Repetir el paso 1–2 con *Usar existente* `ContentFlowDB` para: `publicaciones`, `reacciones`, `comentarios`, `usuarios` (todos con `/id`).
4. Por cada contenedor: desplegar → **Elementos** (*Items*) → **Cargar elemento** (*Upload Item*) → elegir el archivo del mismo nombre
   en `data_cosmos_nosql/` → subir.
5. Verificar en **Nueva consulta SQL**: `SELECT VALUE COUNT(1) FROM c` → **500** en cada contenedor.
- Evidencia: captura del Explorador con los 5 contenedores y el COUNT.

## Fase 4 · Cuenta de almacenamiento (Blob)
1. Buscar `Cuentas de almacenamiento` → **+ Crear**.
2. Grupo `rg-contentflow-ep3`; nombre `stcontentflowep3alarcon` (solo minúsculas y números); región **North Central US**;
   rendimiento *Estándar*; redundancia **LRS**.
3. **Revisar y crear** → **Crear** → **Ir al recurso**.
4. Menú izquierdo → **Contenedores** → **+ Contenedor** → nombre `salida-etl`, acceso *Privado* → **Crear**.

## Fase 5 · Azure Data Factory
1. Buscar `Data factories` (*Factorías de datos*) → **+ Crear**.
2. Grupo `rg-contentflow-ep3`; nombre `adf-contentflow-ep3-alarcon`; región **North Central US**; versión **V2**;
   Git: **Configurar Git más tarde**.
3. **Revisar y crear** → **Crear** → **Ir al recurso** → **Iniciar Studio** (*Launch Studio*).

## Fase 6 · Servicios vinculados (conexiones)
En ADF Studio: **Administrar** (ícono de maletín) → **Servicios vinculados** → **+ Nuevo**.
1. **Azure Cosmos DB for NoSQL** → nombre `LS_CosmosDB_ContentFlow` → *Desde la suscripción de Azure* → elegir la cuenta
   `cosmos-contentflow-ep3-alarcon` → base de datos `ContentFlowDB` → **Probar conexión** → "Conexión correcta" → **Crear**.
2. **Azure Blob Storage** → nombre `LS_Storage_Analitica` → *Desde la suscripción de Azure* → cuenta `stcontentflowep3alarcon`
   → **Probar conexión** → **Crear**.
- Truco (LAB): si no ves el botón *Probar conexión*, baja el zoom del navegador con **Ctrl y -**.

## Fase 7 · Conjuntos de datos (datasets)
**Autor** (lápiz) → **Conjuntos de datos** → **… → Nuevo conjunto de datos**.

Origen (tipo *Azure Cosmos DB for NoSQL*, servicio `LS_CosmosDB_ContentFlow`, importar esquema: **Ninguno**):

| Nombre | Contenedor |
|---|---|
| `DS_Cosmos_Campanas` | `campanas` |
| `DS_Cosmos_Publicaciones` | `publicaciones` |
| `DS_Cosmos_Reacciones` | `reacciones` |
| `DS_Cosmos_Comentarios` | `comentarios` |

Destino (tipo *Azure Blob Storage → DelimitedText*, servicio `LS_Storage_Analitica`, **primera fila como encabezado** marcada,
importar esquema: **Ninguno**; ruta: contenedor `salida-etl`, archivo):

| Nombre | Archivo |
|---|---|
| `DS_Blob_CampanasMetas` | `campanas_metas.csv` |
| `DS_Blob_CampanaPublicacion` | `campana_publicacion.csv` |
| `DS_Blob_Publicaciones` | `publicaciones.csv` |
| `DS_Blob_Reacciones` | `reacciones.csv` |
| `DS_Blob_Comentarios` | `comentarios.csv` |

- Por qué CSV: Power BI lo lee directo y la consulta de origen ya deja los datos planos.
- Importante (error 404 del LAB): el archivo de destino aún no existe, por eso no se importa esquema.

## Fase 8 · Pipeline `PL_ETL_ContentFlow_CosmosToBlob`
**Autor → Canalizaciones → Nueva canalización**. Arrastrar **5 actividades *Copiar datos*** (sin conectarlas entre sí: corren en paralelo).
En cada una: pestaña **Origen** → *Usar consulta* = **Consulta** → pegar la consulta; pestaña **Receptor** → dataset de destino;
pestaña **Asignación** (*Mapping*): **déjala vacía** (botón *Borrar* si ADF propone algo). Lección del LAB: con consultas planas y alias
no hace falta asignación manual.

Decisiones de la Tabla RICE que se aplican: solo atributos conservados, metas aplanadas, mes derivado, arreglo desanidado con JOIN;
no se extraen `correo`, `genero`, `pais`, `hashtags`, `contenido` ni el texto del comentario.

| Actividad | Origen → Receptor | Filas esperadas |
|---|---|---|
| `Copiar_Campanas_Metas` | `DS_Cosmos_Campanas` → `DS_Blob_CampanasMetas` | 500 |
| `Copiar_Campana_Publicacion` | `DS_Cosmos_Campanas` → `DS_Blob_CampanaPublicacion` | 1487 |
| `Copiar_Publicaciones` | `DS_Cosmos_Publicaciones` → `DS_Blob_Publicaciones` | 500 |
| `Copiar_Reacciones` | `DS_Cosmos_Reacciones` → `DS_Blob_Reacciones` | 500 |
| `Copiar_Comentarios` | `DS_Cosmos_Comentarios` → `DS_Blob_Comentarios` | 500 |

Consultas de origen, en el orden de la tabla anterior (1 aplana metas y deriva el mes; 2 desanida el arreglo con JOIN;
3 omite contenido y hashtags y saca la hora; 4 y 5 omiten el texto del comentario y derivan el mes). **Pégalas sin líneas de comentario `--`**:

```sql
SELECT c.id AS campana_id, c.nombre, c.objetivo, c.fecha_inicio, c.fecha_fin,
       SUBSTRING(c.fecha_inicio, 0, 7)         AS mes_inicio,
       c.metricas_objetivo.likes               AS meta_likes,
       c.metricas_objetivo.comentarios         AS meta_comentarios,
       c.metricas_objetivo.compartidos         AS meta_compartidos,
       ARRAY_LENGTH(c.publicaciones_asociadas) AS n_publicaciones
FROM c
```

```sql
SELECT c.id AS campana_id, p AS publicacion_id
FROM c
JOIN p IN c.publicaciones_asociadas
```

```sql
SELECT c.id AS publicacion_id, c.usuario_id, c.categoria, c.tipo, c.fecha_publicacion,
       SUBSTRING(c.fecha_publicacion, 11, 2) AS hora
FROM c
```

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

## Fase 9 · Validar, publicar, ejecutar y monitorear
1. **Validar** → "Se validó la canalización. No se encontraron errores."
2. **Publicar todo** → **Publicar**.
3. **Agregar desencadenador → Desencadenar ahora** → **Aceptar**.
4. **Supervisar** → **Ejecuciones de canalización** → estado **Correcto**; abrir los *detalles* (gafas) de cada copia y anotar
   **Filas leídas = Filas escritas** (tabla de la Fase 8).
- Evidencias: captura de cada pestaña Origen/Receptor, Validar sin errores, Supervisar con "Correcto" y filas.
- Exportar el JSON del pipeline (ícono `{}`) y guardarlo en el repositorio (`adf/PL_ETL_ContentFlow_CosmosToBlob.json`), sin claves.

## Fase 10 · Comprobar los CSV
Cuenta de almacenamiento → **Contenedores** → `salida-etl`: deben estar los 5 CSV. Abrir uno (**Editar** o **Descargar**) y confirmar
que trae encabezados y que no aparecen `correo`, `contenido` ni `hashtags`.

## Fase 11 · Power BI (se detalla al llegar aquí)
Power BI Desktop → **Obtener datos → Azure → Azure Blob Storage** → nombre de la cuenta → clave de cuenta (Storage → **Claves de acceso**;
no se comparte ni se sube al repositorio) → seleccionar `salida-etl` → **Transformar datos**.
Modelo en estrella (campañas ↔ puente ↔ publicaciones ↔ reacciones/comentarios), medidas de cumplimiento y 2 o más visualizaciones
interactivas. Valores de control (calculados por `extraccion_ep3.py --local`): cumplimiento global ≈ **0,69 %** (Aumentar engagement),
**0,71 %** (Captar nuevos usuarios) y **0,72 %** (Promover contenido).

## Fase 12 · Automatización (se detalla al llegar aquí)
1. Data Factory: **Agregar desencadenador → Nuevo/Editar → Programar** (por ejemplo, una vez al día) y **Publicar todo**.
2. Power BI: publicar el informe y, en el servicio web, configurar las credenciales del origen y la **actualización programada**
   (después de la hora del desencadenador).
3. Al terminar la evaluación: **detener el desencadenador** para no gastar crédito.

## Evidencias a guardar (carpeta `Evidencias/`)
Cosmos con los 5 contenedores y COUNT = 500; recursos del grupo `rg-contentflow-ep3`; ambos servicios vinculados con conexión correcta;
datasets; las 5 actividades (Origen/Receptor); Validar y Publicar; Supervisar "Correcto" con filas leídas = escritas; los 5 CSV en Blob;
modelo y dashboard de Power BI; desencadenador y actualización programada.
