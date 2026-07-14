# RemoteOK (remoteok.com)

- **Estado:** adoptado
- **Fecha:** 2026-07-14
- **Mercado / región:** Global remoto
- **Alineación con la meta:** remoto USD (fallback de +3000 USD sin mudarse)

## Acceso
- **robots.txt:** `/api` es una API JSON pública documentada.
- **Auth:** ninguna. Requiere `User-Agent` de navegador (si no, 403) — el CLI lo envía.
- **ToS:** piden **atribución** (link back al `url` del empleo y mencionar Remote OK como fuente). Sin restricción de uso personal.
- **Anti-bot:** 403 si falta UA; sin captcha observado.

## Técnico
- **Endpoint de búsqueda:** `GET https://remoteok.com/api` — array; **el índice 0 es un header legal/metadata** (se salta). Sin búsqueda server-side.
- **Endpoint de detalle:** no hay per-job; `detail` busca por `id`/`slug` en el feed (el `description` ya viene).
- **Campos por resultado:** `id,slug,epoch,date,company,position,tags,description,location,apply_url,salary_min,salary_max,url`.
- **Notas de parsing:** todos remotos (`remote:true`); `salary_min/max` son USD anuales (`0`→null); `visa` derivado del texto.

## Decisión
Adoptado. Skill: `.agents/skills/remoteok-search/`. Aporta el flag `--min-salary` (piso anual USD, sin ocultar
empleos con salario desconocido). Test en vivo OK (2026-07-14): `search` devolvió empleos con contrato completo
y detección de visa; `detail <id>` trajo la descripción. `typecheck` OK, `bun test` 7/7.
