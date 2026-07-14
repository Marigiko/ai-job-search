# Arbeitnow (arbeitnow.com)

- **Estado:** adoptado
- **Fecha:** 2026-07-14
- **Mercado / región:** Alemania / UE + remoto
- **Alineación con la meta:** visa/relocación + remoto USD/EUR

## Acceso
- **robots.txt:** el endpoint `/api/job-board-api` es una API pública documentada, pensada para uso programático.
- **Auth:** ninguna (sin API key).
- **ToS:** API pública; sin restricción de "uso personal" tipo LinkedIn. Backoff en 429/5xx incorporado.
- **Anti-bot:** no observado.

## Técnico
- **Endpoint de búsqueda:** `GET https://www.arbeitnow.com/api/job-board-api?page=<n>` — últimos 100 empleos/página, sin búsqueda server-side (filtro client-side).
- **Endpoint de detalle:** no hay per-job endpoint; `detail` escanea páginas recientes por `slug` (el `description` ya viene en el listado).
- **Campos por resultado:** `slug,title,company_name,location,created_at,url,remote,tags,job_types,description`.
- **Notas de parsing:** `created_at` es timestamp Unix → `YYYY-MM-DD`; `visa` se deriva del texto (tags+title+description) como `sponsor`/`relocation`.

## Decisión
Adoptado. Skill generado: `.agents/skills/arbeitnow-search/`. Test en vivo OK (2026-07-14):
`search -q developer --remote` devolvió resultados con `id/title/url` no nulos y detección de relocación;
`detail <slug>` devolvió la descripción completa. `bun run typecheck` y `bun test` (6/6) en verde.
