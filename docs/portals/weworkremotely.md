# We Work Remotely (weworkremotely.com)

- **Estado:** adoptado
- **Fecha:** 2026-07-14
- **Mercado / región:** Global remoto
- **Alineación con la meta:** remoto USD (fallback +3000 sin mudarse)

## Acceso
- **robots.txt:** feeds RSS públicos, pensados para sindicación.
- **Auth:** ninguna.
- **ToS:** RSS público; sin restricción de uso personal.
- **Anti-bot:** no observado.

## Técnico
- **Endpoint de búsqueda:** `GET https://weworkremotely.com/categories/<slug>.rss` (RSS/XML). Sin búsqueda server-side → filtro client-side.
- **Endpoint de detalle:** la descripción completa viene en el RSS; `detail` busca el slug en los feeds.
- **Campos por item:** `title` ("Empresa: Puesto"), `link`, `guid`, `pubDate`, `region`, `category`, `description` (HTML).
- **Notas de parsing:** empresa/título se separan del `title` por `": "`; `region`→location; `pubDate` RFC-822→`YYYY-MM-DD`; todos remotos.

## Decisión
Adoptado. Skill: `.agents/skills/weworkremotely-search/`. Categorías vía `--category` (programming/front-end/back-end/devops/design/...).
Test en vivo OK (2026-07-14): `search` devolvió empleos con contrato completo, empresa parseada y detección de visa;
`detail <slug>` trajo la descripción. `typecheck` OK, `bun test` 5/5.
