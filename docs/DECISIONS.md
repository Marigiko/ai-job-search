# Log de Decisiones

Registro cronológico de decisiones de diseño para la extensión del repo. Formato: fecha · decisión · razón.

---

## 2026-07-14 — Decisiones iniciales del plan de acción

### D1 · Posts de LinkedIn: enfoque híbrido
**Decisión:** implementar primero el modo *compliant* (descarga de permalinks públicos `/posts/<slug>` + descubrimiento vía WebSearch), y dejar el modo *autenticado* (cookie de sesión → API Voyager) documentado pero **desactivado por defecto**.
**Razón:** la búsqueda de posts del feed por keyword requiere autenticación (API Voyager); el repo prohíbe fuentes auth-walled. El modo compliant no viola ToS ni requiere login. El autenticado queda como opción avanzada bajo responsabilidad del usuario.

### D2 · Dashboard: HTML estático generado
**Decisión:** un script Python (`tools/dashboard.py`) lee los datos existentes y genera un `dashboard.html` autocontenido (CSS/JS inline, sin deps, offline).
**Razón:** encaja con la filosofía "corre en tu máquina", cero servidor/mantenimiento, y todos los datos ya viven en archivos locales (CSV, JSON, markdown).

### D3 · Portales a agregar
**Decisión:** priorizar visa/relocación (Relocate.me, Landing.jobs, Arbeitnow, VanHack), luego remotos globales (RemoteOK, We Work Remotely, Wellfound), luego LatAm (GetOnBoard, Computrabajo, Bumeran) y por región (NZ, Europa, USA).
**Razón:** alineación directa con el objetivo de migrar (visa) y con el fallback de remoto en USD de +3000.

### D4 · Postular por email: redactar y enviar con confirmación
**Decisión:** generar email + CV + carta, mostrar preview y pedir confirmación explícita; solo entonces enviar vía Gmail MCP. Sin confirmación → crear draft, nunca enviar.
**Razón:** el email es una acción externa e irreversible; la confirmación evita envíos erróneos manteniendo la automatización.

### D5 · Relocación deja de ser deal-breaker automático
**Decisión:** la relocación pasa de `FAIL` hard-codeado (en `04` dim 4, `rank.md`, `job-scraper/SKILL.md`) a una **señal positiva** que sube el puntaje.
**Razón:** el objetivo del usuario es migrar; un puesto que ofrece relocación/visa es lo más deseable, no un descarte.

### D6 · Dónde viven las preferencias
**Decisión:** los **valores** de preferencia (banda salarial, relocación/visa, roles) van en `CLAUDE.md`/`01-candidate-profile.md`; la **estructura** del framework (nuevas dimensiones de scoring) va en `04-job-evaluation.md`.
**Razón:** `/reset profile` limpia `01`/`CLAUDE.md` pero preserva `03/04/06` como reglas del framework. Así los valores se resetean y la estructura sobrevive.
