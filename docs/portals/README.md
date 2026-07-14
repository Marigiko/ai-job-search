# Fichas de portal

Una ficha por portal investigado para la Fase 2. Alimenta el gate de ToS/auth de `/add-portal`
y deja registro de por qué un portal se adoptó o rechazó. Nombre de archivo: `<portal-slug>.md`.

## Plantilla

```markdown
# <Nombre del portal> (<dominio>)

- **Estado:** investigando | adoptado | rechazado
- **Fecha:** YYYY-MM-DD
- **Mercado / región:** <país o global>
- **Alineación con la meta:** visa/relocación | remoto USD | LatAm red-de-seguridad | regional

## Acceso
- **robots.txt:** ¿permite las rutas de búsqueda/detalle? (cita las líneas relevantes)
- **Auth:** ¿requiere login para ver listados? (sí → RECHAZAR por regla del repo)
- **ToS:** ¿prohíbe acceso automatizado? (sí → banner "uso personal" en la SKILL.md)
- **Anti-bot:** Cloudflare / captcha / rate limit observado

## Técnico
- **Endpoint de búsqueda:** URL + parámetros (preferir API/JSON/RSS sobre scraping HTML)
- **Endpoint de detalle:** patrón de URL
- **Campos por resultado:** id, title, company, location, date, url (+ extras: salary, remote, visa)
- **Notas de parsing:** selectores/shape del JSON

## Decisión
<adoptar / rechazar y por qué. Si se adopta: nombre del skill generado y estado del test en vivo.>
```

## Índice

| Portal | Estado | Alineación | Ficha |
|--------|--------|-----------|-------|
| Arbeitnow | adoptado | visa/relocación + remoto | [arbeitnow.md](arbeitnow.md) |
| RemoteOK | adoptado | remoto USD | [remoteok.md](remoteok.md) |
| We Work Remotely | adoptado | remoto USD | [weworkremotely.md](weworkremotely.md) |
| GetOnBoard | adoptado | LatAm + remoto | [getonbrd.md](getonbrd.md) |
| Landing.jobs | adoptado | visa/relocación (EU) | [landingjobs.md](landingjobs.md) |
| VanHack | rechazado (auth) | visa/relocación | [vanhack.md](vanhack.md) |

## Sondeados (pendientes / feasibility) — 2026-07-14

| Portal | Resultado del sondeo | Camino para construir |
|--------|----------------------|-----------------------|
| **Computrabajo** (pe) | HTML 200 accesible (sin Cloudflare) | scraping HTML de las tarjetas de empleo (patrón `linkedin-search`) |
| **Bumeran** (pe) | SPA JS (shell 63KB) | hallar la API interna (api.bumeran / guuk) e ir por JSON |
| **Relocate.me** | sin API pública (`/api/jobs` 404) | scraping HTML |
| **Wellfound** | SPA + Cloudflare/GraphQL con token | **rechazado** (efectivamente auth-walled) |
| **Seek NZ** | API protegida (308, requiere headers/host) | investigar endpoint chalice-search + headers |
| **Remotive** | API JSON pública OK | bonus remoto, fácil (misma plantilla) |
| **Jobicy** | API JSON v2 pública OK | bonus remoto, fácil (misma plantilla) |
