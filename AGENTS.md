# AGENTS.md

Notes for AI coding agents working on this repository.

## Pendientes

Items identified during review but deliberately not implemented — they need a
human decision or a dedicated verification cycle before touching them.

- **Migración de `mcp` a la serie 2.x.** `requirements.txt` fija `mcp>=1.3.0,<2`
  porque `mcp==2.0.0` cambió la API de `FastMCP` de forma incompatible (ver
  historial de commits: se pinneó en caliente tras romper el despliegue).
  Migrar requiere su propio ciclo de prueba local + staging contra la API 2.x
  antes de tocar producción — no intentar como parte de un cambio más grande.

- **`cloudbuild.yaml` no versionado.** El despliegue a Cloud Run se dispara
  desde un trigger de Cloud Build configurado en la consola de GCP, fuera del
  repo. No hay visibilidad desde el código de qué build steps usa ese trigger
  hoy. Antes de comitear un `cloudbuild.yaml`, confirmar la config real con
  `gcloud builds triggers describe <trigger>` para no divergir de lo que ya
  está andando en producción.

- **Límite de largo en inputs libres** (`descripcion_vacante` en
  `evaluar_fit_puesto`, `consulta` en `buscar_en_curriculum`). Evaluado y
  descartado por ahora: son scans de substring sobre ~10 items en memoria (sin
  operación costosa detrás) y Cloud Run ya limita el tamaño de request. Un cap
  de longitud acá sería validación decorativa sin problema real que resuelva.
  Reconsiderar si estos parámetros alguna vez envuelven una llamada externa.
