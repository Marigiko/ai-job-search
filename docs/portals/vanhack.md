# VanHack (vanhack.com)

- **Estado:** rechazado (auth-walled)
- **Fecha:** 2026-07-14
- **Mercado / región:** Global (relocación/visa, curado)
- **Alineación con la meta:** visa/relocación (alta) — pero inaccesible sin cuenta

## Acceso
- **robots.txt / página:** `https://vanhack.com/jobs` responde 200 pero es una **SPA**; el listado de empleos
  se carga tras autenticación. VanHack es una plataforma curada que **requiere crear cuenta** y pasar screening
  para ver y postular a los empleos.
- **Auth:** **sí, requerida** para ver listados.
- **ToS:** acceso automatizado no contemplado; contenido tras login.

## Decisión
**Rechazado por la regla del repo** (`/add-portal` Step 2.4: fuentes con login se declinan — "este patrón solo
funciona en páginas públicas"). No se genera skill.

**Alternativa recomendada:** usar VanHack manualmente (crear cuenta y postular en su plataforma). El objetivo de
visa/relocación ya está cubierto de forma automatizable por **Arbeitnow** (`--visa`), **RemoteOK** (`--visa`) y las
queries `"visa sponsorship"`/`relocation` de `search-queries.md`. Si en el futuro VanHack expone una API pública,
se reevalúa.
