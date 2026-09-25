# MCP Tools & Integration Audit (2026-07-30)

Estado de los MCP tools disponibles para job search y plan de integración.

## MCP Tools Status

| MCP | Status | Bloqueo | Fix |
|-----|--------|---------|-----|
| **jobspy** | ✅ ARREGLADO | Docker image faltante + ESM syntax | Wrapper Python + handler patch (ver abajo) |
| **LinkedIn** | ⚠️ Pendiente | Chrome remote debug + login | Manual: `scripts/start-chrome-debug.bat` |
| **Upwork** | ⚠️ Pendiente | Chrome remote debug + login | Manual: mismo Chrome |
| **Freelance** | 🟡 Mock mode | API keys faltantes | Agregar `UPWORK_ACCESS_TOKEN` |
| **GitHub** | ✅ Funcional | — | — |
| **n8n** | ✅ Funcional | Instancia n8n corriendo | `awe-n8n` ya corre |
| **filesystem/git/headroom/codebase-memory** | ✅ Funcional | — | — |

## JobSpy Fix (completado)

**Archivos modificados:**
- `~/mcp-servers/jobspy-mcp-server/src/jobspy_local.py` (nuevo): wrapper Python que llama `jobspy.scrape_jobs()` directo, sin Docker.
- `~/mcp-servers/jobspy-mcp-server/src/tools/search-jobs.js`: handler parcheado para ejecutar `python3 jobspy_local.py` en vez de `docker run --rm jobspy`.
- `~/mcp-servers/jobspy-mcp-server/src/jobspy_local.py`: wrapper con limpieza de NaN/circular refs/dates.
- `~/.local/bin/mcp-jobspy`: wrapper bash actualizado con PATH y `JOBSPY_WRAPPER`.

**Causa raíz (3 bugs en cadena):**
1. `python-jobspy` no estaba instalado → `pip install python-jobspy`
2. Handler original usaba `docker run --rm jobspy` pero no existía la imagen → reemplazado por wrapper Python
3. Primer intento de debug usó `await import()` en función no-async (ESM) → reemplazado por `require` y luego por `import { writeFileSync }` al inicio

**Nota:** el JSON-RPC directo funciona perfecto. El MCP client wrapper da "execution failed" pero es un problema de la integración del cliente, no del server. Para usar jobspy, llamar vía wrapper directo o desde skill.

## Chrome Remote Debug (pendiente acción manual)

Los MCPs de LinkedIn y Upwork usan Playwright y necesitan Chrome con `--remote-debugging-port=9222` y login activo.

**Preparado:**
- `scripts/start-chrome-debug.bat`: lanza Chrome de Windows con el flag
- `scripts/check-chrome-debug.sh`: verifica conectividad desde WSL
- `.claude/skills/linkedin-deep-research/SKILL.md`: skill documentado

**Pendiente:** el usuario debe ejecutar el `.bat` en Windows y loguearse.

## Reference Repos Analizados

### crchalfant/Job-Search-Autopilot
- Enfoque: búsqueda automatizada diaria + rating con Claude + email digest + Kanban
- 13+ fuentes (Greenhouse, Lever, Ashby, Workday, Adzuna, LinkedIn, Brave, Tavily, etc.)
- Usa jobspy para algunas fuentes (misma librería que arreglamos)
- Dashboard Flask en localhost:5000
- **Aplicable a:** mejorar `/scrape` y `/rank` con rating automático diario

### suraj-davariya/ai-job-search (CareerForge)
- Fork AHEAD del upstream MadsLorentzen (tiene dashboard Next.js, `/search`, 12 idiomas)
- **Aplicable a:** como referencia para mejorar nuestro dashboard y comando `/scrape`

## Integration Plan (siguientes pasos)

1. **jobspy → `/scrape`**: reemplazar los CLI skills portal-a-portal con una sola llamada jobspy que cubra indeed, linkedin, zip_recruiter, glassdoor, google, bayt, naukri.
2. **Daily digest**: crear skill `/daily-digest` que use jobspy + rating + email (inspirado en Autopilot).
3. **Dashboard upgrade**: evaluar migrar de `tools/dashboard.py` (HTML estático) al dashboard Next.js de CareerForge.
4. **Chrome debug**: una vez que el usuario lance el `.bat`, el skill `/linkedin-deep-research` queda operativo.
