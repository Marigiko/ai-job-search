# Landing.jobs (landing.jobs)

- **Estado:** adoptado
- **Fecha:** 2026-07-14
- **Mercado / región:** Europa (tech)
- **Alineación con la meta:** visa/relocación (alta — flag `relocation_paid`) + remoto

## Acceso
- **robots.txt:** API pública `/api/v1/`.
- **Auth:** ninguna.
- **ToS:** API pública. Uso razonable.
- **Anti-bot:** no observado.

## Técnico
- **Endpoint de búsqueda:** `GET https://landing.jobs/api/v1/jobs?page=<n>` — array de ~50 últimos. Sin búsqueda server-side → filtro client-side.
- **Endpoint de detalle:** no hay per-job; `detail` busca el id en el feed y compone la descripción de `role_description`+`main_requirements`+`nice_to_have`+`perks`.
- **Campos:** `id,title,url,remote,relocation_paid,currency_code,gross_salary_low/high,published_at,tags,locations[{city,country_code}]`.
- **Sin campo company:** se deriva del slug del `url` (`/at/<empresa>/...`), title-cased (best-effort).
- **Salario:** anual bruto en `currency_code` (mayormente EUR).

## Decisión
Adoptado. Skill: `.agents/skills/landingjobs-search/`. `relocation_paid` → `visa:"relocation"`; flags `--visa`,
`--remote`, `--min-salary` (anual, moneda del posting). Test en vivo OK (2026-07-14): `search` mostró empleos con
empresa/ubicación/salario y detección de relocación; `detail <id>` compuso la descripción. `typecheck` OK, `bun test` 5/5.
