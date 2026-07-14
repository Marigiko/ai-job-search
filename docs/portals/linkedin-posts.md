# LinkedIn Posts (linkedin.com/posts) — Fase 3

- **Estado:** adoptado (híbrido) · **Fecha:** 2026-07-14 · **Tipo:** posts de recruiters (no la sección de empleos) · **Alineación:** cubre el caso "postular por email" desde publicaciones

## Acceso
- Los permalinks públicos `https://www.linkedin.com/posts/<slug>` devuelven **HTTP 200 logged-out** con OG meta (autor/empresa + texto) y el body. Verificado en vivo (Luftborn, Deepika Rajagopal).
- El **feed** y la búsqueda por keyword están tras la API Voyager autenticada → **no se usan** (regla public-only + ToS).
- ⚠️ **Uso personal**: banner en la SKILL.md.

## Técnico
- `extract <url>`: OG `og:title` (autor/empresa), `og:description` (texto), fecha **decodificada del activity id** (`Number(BigInt(id) >> 22n)`), y **email** por regex con de-ofuscación (`[at]`/`(at)`/` at `→@, `[dot]`/`(dot)`→., `&#64;`→@), filtrando assets/infra (licdn/linkedin).
- `parse --text`/stdin: mismo extractor sobre texto pegado (offline, fiable si el post está gated).
- `search`: **no crawlea el feed**; imprime el flujo compliant (WebSearch→extract). Modo autenticado `LINKEDIN_COOKIE` documentado y **declinado por defecto**.
- Contrato: `{meta,results:[{id,title,company,location:null,date,url, applyEmail, emails[], author, text, source:"linkedin-post"}]}`.

## Decisión
Adoptado (compliant). Skill `.agents/skills/linkedin-posts-search/`. Descubrimiento vía WebSearch (queries en
`search-queries.md`). Alimenta la **Fase 4** (postular por email). Test en vivo OK (2 posts reales → email+fecha+autor);
`typecheck`+`bun test` 7/7.
