# GetOnBoard / getonbrd.com

- **Estado:** investigando (viable — pendiente de construir)
- **Fecha:** 2026-07-14
- **Mercado / región:** LatAm + remoto (tech)
- **Alineación con la meta:** LatAm red-de-seguridad + remoto USD

## Acceso
- **robots.txt:** API pública documentada `/api/v0/`.
- **Auth:** ninguna para búsqueda. (Algunos endpoints/campos pueden requerir token, pero `search/jobs` es abierto.)
- **ToS:** API pública. Uso razonable.
- **Anti-bot:** no observado.

## Técnico
- **Endpoint de búsqueda:** `GET https://www.getonbrd.com/api/v0/search/jobs?query=<kw>&remote=true&per_page=<n>&page=<n>` — **búsqueda server-side real** (query, remote, paginación con `meta.total_pages`).
- **Endpoint de detalle:** el job trae `attributes.description` inline; `links.public_url` es la URL.
- **Campos (attributes):** `title, description, remote, remote_modality, remote_zone, countries, min_salary, max_salary, published_at, seniority, category_name, tags, company, modality, perks`. Salario en USD.
- **⚠️ Complicación (JSON:API):** `company`, `seniority` y `tags` son **relaciones por id** (`{data:{id,type}}`), sin el nombre inline. `expand`/`include` NO están soportados (devuelven error). El nombre de empresa se resuelve con `GET /api/v0/companies/:id` (probado: id 19970 → "SugarShan Inc").

## Decisión
**Viable, diferido.** La API es de las mejores (búsqueda server-side + salario + remoto + seniority, LatAm),
pero requiere un paso extra de diseño no presente en los otros portales: **resolver el nombre de empresa por id**.
Plan al construir: hacer un lookup a `/companies/:id` por cada empresa única del set de resultados, con una
**caché en memoria por ejecución** para no repetir requests (típicamente ≤ nº de resultados). Igual para `seniority`
(catálogo pequeño y estable → se puede cachear un mapa id→label). Hasta entonces, `company` quedaría `null`.
