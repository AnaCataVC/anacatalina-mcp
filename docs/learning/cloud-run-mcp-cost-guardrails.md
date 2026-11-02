# Cloud Run Request Timeout & MCP Free-Tier Cost Guardrails

## Context & Motivation

In October 2026, the monthly Google Cloud billing for the `cata-mcp` project experienced an unexpected increase from 14 CLP (minimal rounding/storage baseline in September) to 4,491 CLP (~$5.50 USD). 

Because `anacatalina-mcp` is designed as a lightweight, zero-cost, high-performance in-memory Model Context Protocol (MCP) server, this billing anomaly prompted an immediate forensic analysis of Cloud Monitoring and Cloud Logging data to establish preventative architectural guardrails.

---

## Forensic Investigation & Root Cause

### 1. Metrics Analysis (September vs. October)

| Metric | September 2026 | October 2026 | Variation |
| :--- | :--- | :--- | :--- |
| **Total HTTP Requests** | 3,193 req | 4,792 req | +50% *(Well below 2,000,000 free tier)* |
| **Total Billable Instance Seconds** | **12,395 s** (3.44 hrs) | **409,081 s** (113.63 hrs) | **+3,200% (33x increase)** |
| **Monthly Free Tier Allowance (vCPU)** | 180,000 s (~50 hrs) | 180,000 s (~50 hrs) | Fully exhausted |
| **Excess Billable Time** | 0 s | **~229,081 s** (~63.6 hrs) | Billed at `us-central1` standard rate |
| **Invoice Total** | **14 CLP** | **4,491 CLP** | Exact correlation |

### 2. The Persistent Stream Loop

Cloud Run request logs revealed that MCP client integrations (such as Cursor, Claude Desktop, and Antigravity, identifying as `Go-http-client/2.0` and `Google`) initiated long-lived streaming connections to `GET /mcp`.

Under the default Cloud Run configuration:
1. **1-Hour Timeout Ceiling:** `spec.template.spec.timeoutSeconds` was set to `3600` (1 hour).
2. **Active Request Billing Invariant:** In Google Cloud Run, CPU is allocated and billed whenever at least one request is being processed. Because the SSE/Streamable HTTP transport kept the HTTP connection open, Cloud Run considered the instance active for the entire 3,600-second window.
3. **Automated Client Reconnect:** Upon reaching the 3,600-second timeout, MCP clients immediately reconnected within 4 to 5 seconds, resulting in consecutive 1-hour active billing blocks:
   - `21:06:21 UTC` -> 3,601s connection
   - `22:06:26 UTC` -> 3,600s connection
   - `23:06:30 UTC` -> 3,601s connection
4. This loop held container instances active for up to 13 hours per day during October, consuming 409,081 billable instance seconds and blowing past the 180,000-second free tier.

---

## Architectural Guardrails & Remediation

### 1. Request Timeout Bounding (`timeoutSeconds: 300`)

The service was reconfigured to enforce an upper bound of 300 seconds (5 minutes):

```bash
gcloud run services update anacatalina-mcp \
  --timeout=300s \
  --region=us-central1 \
  --project=cata-mcp
```

### 2. Why 300 Seconds Does Not Degrade User Experience

1. **In-Memory Sub-5ms Execution:** All 10 FastMCP tools (`obtener_experiencia`, `evaluar_fit_puesto`, `buscar_en_curriculum`, etc.) query in-memory Python data structures. Real execution time is between 2ms and 10ms.
2. **Interactive Chat Compatibility:** 5 minutes provides more than enough headroom for any individual tool call, multi-turn reasoning phase, or interactive web showcase session.
3. **Automatic Scale-to-Zero:** If an agent or human evaluator stops interacting, the idle connection closes at 300s instead of remaining pinned for 3,600s. The container immediately terminates to zero instances, preventing billing leakage.
4. **Fast Cold Starts (<1.5s):** The service has `startup-cpu-boost: true` enabled, ensuring that when a new request arrives after scaling down, the instance initializes almost instantaneously.

### 3. Client-Side Best Practice

When working locally or configuring AI editors (Cursor, Windsurf, Antigravity, Claude Desktop):
- Toggle or disable the MCP connector in `mcp_config.json` (`"disabled": true` or omit) when not actively testing or developing MCP workflows to prevent unnecessary background polling from local development sessions.
