# The Muse (themuse.com)

- **Estado:** adoptado · **Fecha:** 2026-07-14 · **Región:** USA (fuerte) + global vía `location` (NZ, UK/Europa) · **Alineación:** cobertura USA + NZ + Europa (roles on-site/híbridos de empresas reales)
- **Acceso:** API pública `/api/public/jobs` (sin key) + per-job `/api/public/jobs/<id>`. Filtros server-side `location`, `category`, `level`, `page`. Sin parámetro de keyword → filtro client-side.
- **Técnico:** `{results:[...],page_count,total}`. Campos: id, name, company.name, locations[{name}], categories[{name}], levels[{name}], publication_date, contents(HTML), refs.landing_page. `remote` si location incluye "Flexible / Remote". Sin salario.
- **Decisión:** adoptado. Skill `.agents/skills/themuse-search/`. **Portal primario de USA** y fuerte para NZ/Europa vía `-l "Auckland, New Zealand"` / `-l "London, United Kingdom"`. Test en vivo OK (NY + Auckland, detail per-id); `typecheck`+`bun test` 3/3.
