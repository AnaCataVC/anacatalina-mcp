---
name: sync-mcp-data
description: Audita y sincroniza los datos del servidor MCP (data/cv_data.json) con los repositorios hermanos anacatalina-cv y projects-hub garantizando consistencia, validación Pydantic v2 y cumplimiento de invariantes de identidad.
allowed-tools: Bash, Read, Grep, run_command, view_file, replace_file_content, write_to_file
---

# Skill: Sincronización de Datos MCP (Cross-Repository Data Sync)

Esta skill guía el proceso de auditoría y sincronización entre el servidor MCP (`anacatalina-mcp`) y sus repositorios hermanos de referencia:
- **`anacatalina-cv`** (`../anacatalina-cv`): Fuente de verdad primaria para información personal, experiencia laboral (SimpliRoute, Fracttal), matriz de habilidades técnicas y educación.
- **`projects-hub`** (`../projects-hub`): Fuente de verdad primaria para proyectos de código abierto y herramientas destacadas en el portafolio.

---

## Directrices Críticas e Invariantes

1. **Zero Hardcoded Paths (Portabilidad Absoluta):**
   - NUNCA usar rutas absolutas de la máquina (`C:\Users\...`).
   - Resolver siempre los repositorios hermanos de forma dinámica respecto al workspace actual (`..` o `$env:USERPROFILE\Repos\...`).
2. **Identidad del Candidato e Invariantes Estrictos:**
   - Nombre oficial: `Ana-Catalina Villalobos Contardo` (primer nombre siempre con guion `Ana-Catalina`).
   - GitHub: `AnaCataVC`.
   - Sin emojis de banderas nacionales en documentación, interfaces o datos (Zero Flags Rule).
3. **Validación Estricta de Esquemas Pydantic v2:**
   - Toda modificación a `data/cv_data.json` debe validar exitosamente contra el modelo `models.cv.CVData`.
4. **Calidad y Suite de Tests (Quality Gate):**
   - Tras cualquier sincronización o edición de datos, ejecutar `pytest tests/ -v` para certificar que las 9 tools MCP y todos los endpoints REST y Streamable HTTP operan sin regresiones.

---

## Flujo de Ejecución

### 1. Ejecutar el Script de Auditoría de Datos
Ejecutar la herramienta nativa de auditoría en Python desde la raíz del proyecto:

```powershell
.venv\Scripts\python.exe scripts/sync_mcp_data.py --audit
```

O en formato JSON estructurado para consumo automatizado por subagentes:

```powershell
.venv\Scripts\python.exe scripts/sync_mcp_data.py --json
```

Para comprobaciones rápidas en pipelines o hooks:

```powershell
.venv\Scripts\python.exe scripts/sync_mcp_data.py --check-only
```

### 2. Inspección y Detección de Cambios
El script realiza automáticamente:
- Lectura de `anacatalina-cv/src/i18n.js` y `anacatalina-cv/src/pages/index.astro` para extraer:
  - Titular profesional (`hero.subtitle`).
  - Fechas y viñetas de responsabilidades laborales de SimpliRoute y Fracttal (limpieza de etiquetas HTML).
  - Resúmenes ejecutivos en español e inglés.
  - Matriz completa y badges de habilidades técnicas (`parse_skills_from_cv_astro`).
  - Formación académica y prácticas profesionales.
- Escaneo de `projects-hub/src/content/projects/es/*.md` para obtener:
  - Títulos, descripciones, stacks tecnológicos, URLs de repositorios en GitHub y demos en producción de proyectos flagship.
- Comparación profunda y dinámica contra el estado actual de `data/cv_data.json`.

### 3. Aplicar Sincronización
Para volcar las actualizaciones validadas a `data/cv_data.json`:

```powershell
.venv\Scripts\python.exe scripts/sync_mcp_data.py --sync
```

### 4. Quality Gate & Verificación
Validar que la suite de 27+ pruebas automatizadas pase con 100% de éxito:

```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```
