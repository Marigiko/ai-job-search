# Remotive (remotive.com)

- **Estado:** adoptado · **Fecha:** 2026-07-14 · **Región:** Global remoto · **Alineación:** remoto USD
- **Acceso:** API JSON pública `/api/remote-jobs`, sin auth. Búsqueda server-side (`search`).
- **Técnico:** `{jobs:[...]}` (más claves meta/legal). Campos: id, url, title, company_name, category, tags, job_type, publication_date, candidate_required_location, salary(freetext), description(HTML). `location`=candidate_required_location (región/timezone).
- **Decisión:** adoptado. Skill `.agents/skills/remotive-search/`. `salaryText` (freetext, no numérico). Test en vivo OK; `typecheck`+`bun test` 4/4.
