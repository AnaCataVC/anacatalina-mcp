<p align="center">
  <img src="icon.png" alt="Ana Catalina MCP Server" width="160" />
</p>

<h1 align="center">Ana Catalina &mdash; Interactive Curriculum MCP Server</h1>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.12" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-Official%20SDK-purple?style=flat" alt="Model Context Protocol" /></a>
  <a href="https://cloud.google.com/run"><img src="https://img.shields.io/badge/Google%20Cloud-Cloud%20Run-4285F4?style=flat&logo=googlecloud&logoColor=white" alt="Google Cloud Run" /></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Container%20Ready-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker" /></a>
  <a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen?style=flat&logo=pytest&logoColor=white" alt="Pytest" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat" alt="License MIT" /></a>
</p>

> **Official Model Context Protocol (MCP) Server** with Server-Sent Events (SSE) transport over FastAPI, exposing an interactive CV and portfolio for AI assistants and LLM clients. Includes a local `stdio` bridge for Claude Desktop and a production-ready container for Google Cloud Run.

<div align="center">
  <h3>🟢 Live Server URL / Servidor en Vivo:</h3>
  <p><strong><a href="https://mcp.ana-catalina.com/">https://mcp.ana-catalina.com/</a></strong></p>
  <small>(Cloud Run Mirror: <code>https://anacatalina-mcp-165536131179.us-central1.run.app/</code>)</small>
</div>

---

## Descripción del Proyecto (Spanish)

Este proyecto implementa un servidor oficial de **Model Context Protocol (MCP)** en Python que permite a evaluadores técnicos, reclutadores y modelos LLM (como Claude o GPT) explorar de forma interactiva y estructurada la trayectoria profesional, habilidades técnicas, proyectos insignia y compatibilidad con vacantes de **Ana Catalina** (Data Scientist & Learning Engineer en SimpliRoute, ex-Fracttal).

### Características Principales
- **Web Showcase & Playground Interactivo:** Servido en la raíz (`/`) y `/demo` bajo el *Pastel-Tech Design System*. Permite a reclutadores y visitantes humanos evaluar compatibilidad con vacantes y buscar en el currículum en tiempo real sin costo de APIs ni tokens.
- **Negociación Transparente de Contenido:** Devuelve una aplicación web responsiva si la petición proviene de un navegador (`Accept: text/html`) y el JSON de descubrimiento original si proviene de agentes o APIs.
- **Transporte SSE Remoto:** Integrado con FastAPI y `SseServerTransport` para despliegue Serverless en Google Cloud Run. ¡El servidor ya se encuentra en producción!
- **9 Herramientas MCP Especializadas:** Consulta granular de experiencia laboral, stack tecnológico con niveles de dominio, proyectos insignia, evaluación automática de vacantes, búsqueda global por palabras clave, educación, contacto y perfil general.
- **Script Puente Local (`conecta_cata.py`):** Permite conectar clientes locales basados en `stdio` (como Claude Desktop) con el servidor remoto alojado en Cloud Run a través de HTTP/SSE.
- **Desacoplamiento y Rendimiento:** Datos estructurados en `data/cv_data.json` validados en memoria con **Pydantic v2** al iniciar el contenedor (<2ms por consulta).

---

## Project Overview (English)

This project provides an official **Model Context Protocol (MCP)** server built in Python that enables AI assistants, hiring managers, and evaluators to interactively query the professional experience, technical skill matrix, featured projects, and job compatibility of **Ana Catalina** (Data Scientist & Learning Engineer at SimpliRoute, former Fracttal).

### Key Features
- **Interactive Web Showcase & Playground:** Served at `/` and `/demo` using the *Pastel-Tech Design System*. Allows human visitors and evaluators to test job fit and query the curriculum directly in the browser with zero API billing and zero hallucinations.
- **Transparent HTTP Content Negotiation:** Serves the interactive web interface to browsers (`Accept: text/html`) while preserving the structured JSON discovery payload for programmatic agents and curl.
- **Remote SSE Transport:** Implemented via FastAPI and `SseServerTransport`, optimized for Serverless hosting on Google Cloud Run. Live and deployed!
- **9 Dedicated MCP Tools:** Granular exploration of work history, skill taxonomy by category/level, highlighted projects, automated job fit scoring, full-text curriculum search, education, contact details, and general profile.
- **Local Stdio Bridge (`conecta_cata.py`):** Bi-directional async adapter connecting `stdio`-based clients (such as Claude Desktop) to remote SSE endpoints.
- **Zero-Latency In-Memory Architecture:** Clean data validation using **Pydantic v2** loaded into memory on container startup (<2ms response time).

---

## 📐 Arquitectura del Sistema / System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Cliente MCP / Client Layer"]
        A["Claude Desktop / IDE Client<br/>(stdio: stdin / stdout)"]
    end

    subgraph BridgeLayer["Puente Local / Local Bridge"]
        B["conecta_cata.py<br/>(stdio_server ⇄ sse_client)"]
    end

    subgraph CloudLayer["Google Cloud Run / Serverless Host"]
        C["FastAPI App (:8080)<br/>/sse & /messages/"]
        D["FastMCP Server Core<br/>(9 MCP Tools)"]
        E["CV Service & Pydantic Engine<br/>(models/cv.py)"]
        F[("data/cv_data.json<br/>(In-Memory Dataset)")]
    end

    A <-->|"JSON-RPC (stdio)"| B
    B <-->|"SSE Stream & HTTP POST"| C
    C <--> D
    D <--> E
    E <--> F
```

---

## 🧰 Catálogo de Herramientas MCP / MCP Tools Catalog

El servidor expone **9 herramientas oficiales** registradas a través del protocolo MCP:

| Herramienta / Tool | Parámetros / Parameters | Tipo Retorno / Return Type | Descripción / Description |
| :--- | :--- | :--- | :--- |
| `obtener_experiencia` | `empresa` *(str, opcional)* | `List[ExperienceItem]` | Historial laboral detallado, roles, responsabilidades y tecnologías empleadas. Permite filtrar por empresa. |
| `obtener_stack_tecnologico` | `categoria` *(str, opcional)*<br/>`nivel` *(str, opcional)* | `List[SkillCategory]` | Tecnologías, lenguajes (Python, SQL), Cloud/GCP (BigQuery, Vertex AI) y Docker organizados por categoría y nivel (Avanzado, Intermedio). |
| `obtener_proyectos_destacados` | `tipo` *(str, opcional)*<br/>`tecnologia` *(str, opcional)* | `List[ProjectItem]` | Proyectos insignia (laborales y personales), arquitectura, stack tecnológico y enlaces a repositorios/demos. |
| `evaluar_fit_puesto` | `descripcion_vacante` *(str, requerido)* | `FitEvaluationResult` | Analiza los requerimientos de una vacante laboral y calcula el porcentaje de compatibilidad, fortalezas coincidentes y propuesta de valor. |
| `buscar_en_curriculum` | `consulta` *(str, requerido)* | `Dict[str, Any]` | Búsqueda transversal por palabra clave en todo el currículum (experiencia, habilidades, proyectos y educación). |
| `obtener_educacion` | *Ninguno* | `List[EducationItem]` | Formación académica formal, grado obtenido, institución y especialización. |
| `obtener_contacto` | *Ninguno* | `ContactDetails` | Canales directos de contacto profesional (Email y perfil de LinkedIn). |
| `obtener_perfil` | *Ninguno* | `PersonalInfo` | Perfil general: nombre, cargo actual, ubicación y enlaces de portafolio (incluyendo GitHub). |
| `obtener_resumen_ejecutivo` | `idioma` *(str, default="es")* | `str` | Síntesis ejecutiva del perfil profesional enfocada en Data Science, ML, GCP y arquitecturas MCP en español (`es`) o inglés (`en`). |

---

## 💡 Aprendizajes Clave & Decisiones de Diseño

1. **Dualidad de Transporte en MCP (`stdio` vs `SSE`):**
   - Los clientes locales de escritorio como Claude Desktop operan mediante subprocesos y canales `stdin`/`stdout`.
   - Los entornos de producción serverless (Google Cloud Run) requieren streaming HTTP mediante Server-Sent Events (`/sse` y `/messages/`).
   - El script `conecta_cata.py` actúa como un puente asíncrono bidireccional construido sobre `anyio`, traduciendo eventos entre ambos mundos con latencia nula.
   - Esta necesidad no es pareja entre clientes MCP: `claude_desktop_config.json` (Claude Desktop) solo acepta servidores locales vía `command`/`args` (`stdio`) — un campo `url` ahí se ignora silenciosamente o rompe la config, por eso el puente es obligatorio para conectarlo. Otros clientes, como `mcp.json` de Cursor, sí aceptan un `url` remoto de forma nativa (HTTP/SSE) y no necesitan ningún puente.

2. **Higiene Estricta de Streams en `stdio`:**
   - Cualquier mensaje o log emitido a `stdout` corrompe el flujo JSON-RPC del protocolo MCP.
   - Toda la telemetría, logs informativos y errores en `conecta_cata.py` se canalizan explícitamente hacia `stderr`.

3. **Desacoplamiento y Validación de Datos:**
   - La separación entre la capa de datos (`data/cv_data.json`), los contratos de interfaz (`models/cv.py`) y la lógica de negocio (`services/cv_service.py`) permite actualizar el contenido del currículum sin modificar el servidor MCP ni arriesgar la compatibilidad de tipos.

4. **Compatibilidad y Cambios de API en `mcp 2.x`:**
   - Recientemente, la versión `2.0.0` del SDK oficial de MCP introdujo cambios que renombraron `FastMCP`. Para mantener la estabilidad del despliegue en Cloud Run y garantizar que nuestro código `FastMCP` v1 continúe funcionando correctamente sin refactorización inmediata, fijamos la dependencia en `requirements.txt` a `mcp>=1.3.0,<2`.

---

## 🚀 Instalación y Uso Local / Local Setup

### 1. Clonar el Repositorio y Configurar Entorno

```bash
# Clonar repositorio
git clone https://github.com/AnaCataVC/anacatalina-mcp.git
cd anacatalina-mcp

# Crear y activar entorno virtual
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# Instalar dependencias (producción)
pip install -r requirements.txt

# Instalar dependencias de desarrollo (incluye pytest, para correr la suite de pruebas)
pip install -r requirements-dev.txt
```

### 2. Ejecutar la Suite de Pruebas

```bash
pytest tests/ -v
```

### 3. Iniciar el Servidor MCP Local

```bash
uvicorn server:app --host 0.0.0.0 --port 8080 --reload
```

Endpoints disponibles:
- **Web Showcase & Playground:** `http://localhost:8080/` (en navegadores) o `http://localhost:8080/demo`
- **Discovery JSON:** `http://localhost:8080/` (con cabecera `Accept: application/json` o agentes MCP)
- **Health Check:** `http://localhost:8080/health`
- **SSE Stream:** `http://localhost:8080/sse`
- **Mensajes POST:** `http://localhost:8080/messages/`
- **REST Helper APIs:**
  - `POST /api/evaluate-fit` &mdash; Evaluación determinista de vacantes
  - `GET /api/search?q={query}` &mdash; Búsqueda transversal por palabras clave
  - `GET /api/skills` &mdash; Taxonomía de stack y niveles
  - `GET /api/projects` &mdash; Proyectos destacados (laborales y personales)

---

## 🔌 Configuración en Claude Desktop

Para conectar Claude Desktop con el servidor remoto desplegado en Cloud Run usando el puente local, puedes basarte en el archivo [`claude_desktop_config.example.json`](claude_desktop_config.example.json) incluido en este repositorio. Añade o reemplaza la configuración en tu archivo `claude_desktop_config.json`:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Asegúrate de ajustar el argumento `command` o las rutas según tu sistema operativo. Usa rutas relativas de entorno o tu ruta local al script puente `conecta_cata.py`, pero **nunca compartas rutas absolutas locales en repositorios públicos**.

```json
{
  "mcpServers": {
    "anacatalina-cv": {
      "command": "python",
      "args": [
        "conecta_cata.py" 
      ],
      "env": {
        "MCP_SERVER_SSE_URL": "https://mcp.ana-catalina.com/sse"
      }
    }
  }
}
```

> [!TIP]
> **Pruebas en desarrollo local:** Para conectar Claude Desktop con tu servidor local, cambia el valor de `"MCP_SERVER_SSE_URL"` a `"http://localhost:8080/sse"`.

---

## ☁️ Despliegue en Google Cloud Run / Cloud Run Deployment

### 1. Construir y Probar Contenedor Localmente

```bash
docker build -t anacatalina-mcp .
docker run -p 8080:8080 -e PORT=8080 anacatalina-mcp
```

### 2. Desplegar a Google Cloud Run con Google Cloud SDK (`gcloud`)

```bash
# Autenticarse en Google Cloud
gcloud auth login
gcloud config set project TU_PROJECT_ID

# Desplegar directamente desde el código fuente
gcloud run deploy anacatalina-mcp \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 3600 \
  --session-affinity
```

> [!NOTE]
> Las opciones `--timeout 3600` y `--session-affinity` son fundamentales para mantener conexiones SSE persistentes y estables en Cloud Run.

---

## 📄 Licencia / License

Este proyecto se distribuye bajo la licencia **MIT**. Desarrollado por **Ana Catalina**.
