# Bumeran (bumeran.com.ar)

- **Estado:** rechazado (Cloudflare / anti-bot) · **Fecha:** 2026-07-14 · **Región:** Argentina/LatAm

## Acceso
- La página `www.bumeran.com.ar` es una **SPA JS** (shell ~63KB, datos por API interna).
- Las APIs internas probadas (`www.bumeran.com.ar/api/...`, `api.bumeran.com.ar/...`) devuelven **403 "Just a moment"** → **Cloudflare challenge**. No accesibles con `fetch` sin resolver el challenge.

## Decisión
**Rechazado** — mismo criterio que Wellfound: fuente efectivamente bloqueada por anti-bot. Construir un
scraper aquí requeriría un navegador headless / bypass de Cloudflare, fuera del patrón zero-dep del repo y
en zona gris de ToS.

**Alternativa:** para Argentina/LatAm ya está **Computrabajo** (`--country ar`), que es HTML público sin
Cloudflare. Si Bumeran expone una API pública en el futuro, se reevalúa.
