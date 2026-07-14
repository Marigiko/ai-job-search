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
| Arbeitnow | adoptado | visa/relocación + remoto (EU) | [arbeitnow.md](arbeitnow.md) |
| RemoteOK | adoptado | remoto USD | [remoteok.md](remoteok.md) |
| We Work Remotely | adoptado | remoto USD | [weworkremotely.md](weworkremotely.md) |
| GetOnBoard | adoptado | LatAm + remoto | [getonbrd.md](getonbrd.md) |
| Landing.jobs | adoptado | visa/relocación (EU) | [landingjobs.md](landingjobs.md) |
| Remotive | adoptado | remoto (por región) | [remotive.md](remotive.md) |
| Jobicy | adoptado | remoto **USA / NZ / Europa** (`--geo`) | [jobicy.md](jobicy.md) |
| The Muse | adoptado | **USA** + NZ + Europa (`--location`) | [themuse.md](themuse.md) |
| Computrabajo | adoptado | LatAm / **Argentina** (`--country`) | [computrabajo.md](computrabajo.md) |
| VanHack | rechazado (auth) | visa/relocación | [vanhack.md](vanhack.md) |
| Bumeran | rechazado (Cloudflare) | Argentina/LatAm | [bumeran.md](bumeran.md) |

## Cobertura por región objetivo (USA / Europa / Nueva Zelanda)

| Región | Portales |
|--------|----------|
| **USA** | The Muse (`-l "New York, NY"`), Jobicy (`--geo usa`), Remotive/RemoteOK/WWR (remoto US) |
| **Europa** | Arbeitnow (EU), Landing.jobs (EU), Jobicy (`--geo europe`), The Muse (`-l "London, United Kingdom"`) |
| **Nueva Zelanda** | The Muse (`-l "Auckland, New Zealand"`), Jobicy (`--geo new-zealand`) |
| **LatAm / Argentina** | Computrabajo (`--country ar`), GetOnBoard |

## Sondeados no adoptados — 2026-07-14

| Portal | Resultado | Estado |
|--------|-----------|--------|
| **Wellfound** | SPA + Cloudflare/GraphQL con token | rechazado (auth-walled) |
| **Bumeran** | API interna tras Cloudflare (403) | rechazado — ver [bumeran.md](bumeran.md) |
| **Relocate.me** | sin API pública (`/api/jobs` 404) | diferido (requiere scraping HTML) |
| **Seek NZ** | API `chalice-search` protegida (308) | diferido (requiere headers/host); NZ ya cubierto por The Muse + Jobicy |
