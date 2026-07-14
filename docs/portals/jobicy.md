# Jobicy (jobicy.com)

- **Estado:** adoptado · **Fecha:** 2026-07-14 · **Región:** Global remoto con filtro `geo` (USA / NZ / Europa / …) · **Alineación:** remoto USD, cobertura regional USA+NZ+EU
- **Acceso:** API v2 pública `/api/v2/remote-jobs`, sin auth. Filtros server-side `tag` (keyword), `geo`, `industry`, `count`.
- **Técnico:** `{jobs:[...]}`. Campos: id, url, jobTitle, companyName, jobIndustry[], jobType[], jobGeo, jobLevel, jobDescription(HTML), pubDate, salaryMin/Max, salaryCurrency, salaryPeriod (anual).
- **Decisión:** adoptado. Skill `.agents/skills/jobicy-search/`. **Clave para el objetivo de regiones:** `--geo usa`, `--geo new-zealand`, `--geo europe`. Test en vivo OK (USA y NZ); `typecheck`+`bun test` 3/3.
