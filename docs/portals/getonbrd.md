# GetOnBoard / getonbrd.com

- **Estado:** adoptado
- **Fecha:** 2026-07-14
- **Mercado / región:** LatAm + remoto (tech)
- **Alineación con la meta:** LatAm red-de-seguridad + remoto USD (salarios mensuales USD)

## Acceso
- **robots.txt:** API pública documentada `/api/v0/`.
- **Auth:** ninguna para `search`, `companies`, `seniorities`. El per-job `jobs/:id` requiere auth (401) → no se usa.
- **ToS:** API pública. Uso razonable.
- **Anti-bot:** no observado.

## Técnico
- **Endpoint de búsqueda:** `GET https://www.getonbrd.com/api/v0/search/jobs?query=<kw>&remote=<bool>&per_page=<n>&page=<n>` — **búsqueda server-side real** (query, remote, paginación con `meta.total_pages`).
- **Endpoint de detalle:** `jobs/:id` es auth-walled → `detail` re-busca por queries candidatas derivadas del slug (empresa+ciudad / token más largo / rol) y matchea el id; la descripción viene inline en search.
- **Campos:** `title, description, remote, countries, min_salary, max_salary (MENSUAL USD), published_at, seniority(ref), category_name, company(ref)`.
- **Relaciones (JSON:API):** `company` y `seniority` son referencias por id. Resueltas: empresa vía `GET /companies/:id` (campo `name`, **cacheada por corrida**); seniority vía catálogo `GET /seniorities` (5 items, fetch único). Si falla el lookup → `null`, no bloquea.

## Decisión
Adoptado. Skill: `.agents/skills/getonbrd-search/`. Aporta `--min-salary` (piso **mensual** USD, sin ocultar
salarios desconocidos), `--remote`, `--visa`. Test en vivo OK (2026-07-14): `search` devolvió empleos con
**nombres de empresa resueltos**, salarios mensuales USD y seniority (p. ej. un "Vibe Coder in Residence" a
$3600–5700/mo); `detail <slug>` trajo la descripción completa. `typecheck` OK, `bun test` 5/5.
