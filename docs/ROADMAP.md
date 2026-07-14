# Roadmap — Extensión para segundo empleo (+ relocación/visa)

> Documento vivo. Se actualiza en cada avance. Fuente de verdad del plan de acción.
> Contexto: Mario busca un **segundo empleo** (complementa uno de medio tiempo, 1500 USD/mes).
> Meta: **mín. 2000 / ideal 3000 USD/mes**, con prioridad en **relocación o sponsor de visa** (objetivo: migrar).

Leyenda de estado: ⬜ pendiente · 🟨 en progreso · ✅ hecho

---

## Fase 0 — Documentación 🟨
- ✅ `docs/ROADMAP.md` (este archivo)
- ✅ `docs/DECISIONS.md` (log de decisiones)
- ✅ `docs/portals/README.md` (plantilla + índice de fichas de portal)
- ✅ `.gitignore` actualizado (`dashboard.html`)

## Fase 1 — Perfil y preferencias (bloquea scoring/búsqueda) 🟨
- ⬜ **1a** Poblar perfil real (acción del usuario, vía `/setup`) — pendiente del usuario
- ✅ **1b** Roles múltiples como lista canónica (`### Target Roles` en CLAUDE.md + 01; tiers en search-queries.md; framing en 03/05)
- ✅ **1c** Banda salarial como dimensión de fit (`### 7. Compensation Fit`) + fix del bug de `/setup`
- ✅ **1d** Relocación/visa como señal positiva (`### 8. Relocation & Visa Fit`) + veto quitado en 04/rank.md/job-scraper

## Fase 2 — Expansión de portales ✅ (viables agotados)
Cada portal se ficha en `docs/portals/`. **9 portales adoptados y probados en vivo:**
1. Visa/relocación: **Arbeitnow ✅** (EU, `--visa`), **Landing.jobs ✅** (EU, `relocation_paid`)
2. Remotos: **RemoteOK ✅** (`--min-salary`), **We Work Remotely ✅** (`--category`), **Remotive ✅**
3. Remoto por región: **Jobicy ✅** (`--geo usa|new-zealand|europe`)
4. USA + global: **The Muse ✅** (`--location`, per-job detail)
5. LatAm/Argentina: **GetOnBoard ✅** (salario mensual USD), **Computrabajo ✅** (`--country ar`, HTML)

**Cobertura del objetivo de regiones (≥3 por región donde aplica):**
- **USA:** The Muse, Jobicy (`--geo usa`), Remotive/RemoteOK/WWR → ✅
- **Europa:** Arbeitnow, Landing.jobs, Jobicy (`--geo europe`), The Muse → ✅
- **Nueva Zelanda:** The Muse (`-l "Auckland, New Zealand"`), Jobicy (`--geo new-zealand`) → ✅

**Rechazados/diferidos:** VanHack ❌ / Wellfound ❌ / Bumeran ❌ (auth/Cloudflare) · Relocate.me / Seek NZ ⏸ (diferidos; NZ ya cubierto). Ver matriz en `docs/portals/README.md`.

## Fase 3 — Posts de recruiters en LinkedIn (híbrido) ⬜
- ⬜ Skill `linkedin-posts-search`, comando `extract <post-url>` (modo compliant)
- ⬜ Extracción de `applyEmail` por regex
- ⬜ Queries de descubrimiento en `search-queries.md`
- ⬜ Modo autenticado documentado y **OFF por defecto**

## Fase 4 — Postular por email (redactar + enviar con confirmación) ⬜
- ⬜ Detección de postulación por email en `/apply`
- ⬜ Preview + confirmación explícita → envío vía Gmail MCP con PDF adjunto
- ⬜ Registro en tracker (`channel=email`)

## Fase 5 — Tracking completo (prerequisito del dashboard) ✅
- ✅ `/apply` escribe fila `drafted`
- ✅ Columnas nuevas en el CSV (`salary_expected`, `salary_offered`, `relocation_visa`, `application_url`)
- ✅ Actualizar lectores/escritores (`outcome.md`, `job-scraper`, `upskill`)
- ✅ Normalizar vocabulario de estados (`docs/TRACKING.md`)

## Fase 6 — Dashboard HTML estático ✅
- ✅ `tools/dashboard.py` → `dashboard.html` autocontenido (embudo, filtros, semáforos salario/visa) — probado con fixtures y vacío
- ✅ Comando `/dashboard`

## Fase 7 — Funcionalidades nuevas propuestas ⬜
1. ⬜ Radar de visa/sponsorship
2. ⬜ Inteligencia salarial + costo de vida (Lima vs destino)
3. ⬜ Seguimiento y recordatorios de follow-up
4. ⬜ Monitor de posts/empleos + digest diario
5. ⬜ Analítica de conversión + calibración automática
6. ⬜ (Extra) Variantes de CV por rol
7. ⬜ (Extra) Localización idiomática (inglés/Europass/resume USA)

---

## Secuencia
`0 → 1 → {2, 3} → {4, 5} → 6 → 7`

**MVP recomendado:** Fase 0 + Fase 1 + Arbeitnow/RemoteOK + Fase 5 + Fase 6.
