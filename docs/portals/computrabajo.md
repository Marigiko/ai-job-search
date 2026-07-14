# Computrabajo (computrabajo.com)

- **Estado:** adoptado · **Fecha:** 2026-07-14 · **Región:** LatAm, **default Argentina** (`--country ar`) · **Alineación:** LatAm red-de-seguridad (local, Argentina)
- **Acceso:** páginas HTML públicas `https://<pais>.computrabajo.com/trabajo-de-<slug>?p=<n>`. Sin auth. **Sin Cloudflare en `.ar`** (a diferencia de Bumeran). ⚠️ **Uso personal** (posible restricción ToS) → banner en la SKILL.md.
- **Técnico:** scraping de tarjetas `article.box_offer` (title `a.js-o-link`, company `[offer-grid-article-company-url]`, location `p.fs16 span.mr10`, modalidad `i_home_office`, fecha relativa `p.fc_aux`). `detail` extrae el bloque bajo `<h3>Descripción de la oferta</h3>` + título vía `<h1>`/og:title. `date` aproximada desde "Hace N días".
- **Decisión:** adoptado. Skill `.agents/skills/computrabajo-search/`. Multi-país vía `--country` (ar/mx/cl/pe/co/uy). Test en vivo OK (búsqueda AR + detail); `typecheck`+`bun test` 3/3. Más frágil que las APIs (HTML).
