# Modelo de tracking

Cómo fluye el estado de una postulación entre los tres almacenes de datos y cómo lo consume el dashboard.

## Almacenes
| Archivo | Rol | Escrito por |
|---------|-----|-------------|
| `job_scraper/seen_jobs.json` | Embudo temprano (descubierto → rankeado) | `/scrape`, `/rank` |
| `job_search_tracker.csv` | Espina dorsal (una fila por postulación) | `/apply`, `/outcome`, `/scrape` (opcional) |
| `documents/applications/<c>_<r>/outcome.md` | Registro por postulación (etapas, notas) | `/outcome`, `/interview` |

## Esquema del CSV (17 columnas)
```
date,company,sector,role,role_type,channel,status,contact_person,fit_rating,
salary_expected,salary_offered,relocation_visa,application_url,notes,cv_file,cover_letter_file,source
```
- **Columnas nuevas (Fase 5):** `salary_expected`, `salary_offered`, `relocation_visa` (`sponsor`/`relocation`/`remote`/`none`/`unknown`), `application_url` (apply link o `mailto:`, distinto de `source` = URL del posting).
- Trackers antiguos de 13 columnas siguen siendo válidos: leer por nombre de columna y tolerar ausencias.

## Embudo (para el dashboard)
```
scraped → ranked → interested → drafted → applied → interview → offer → hired
                                                          ↘ rejected / no response / offer declined / withdrawn
```

## Vocabularios de estado y mapeo
| Etapa embudo | `seen_jobs.json` status | CSV `status` | `outcome.md` Status |
|--------------|--------------------------|--------------|---------------------|
| Descubierto | `new` | — | — |
| Rankeado | `ranked` | — | — |
| Marcado de interés | — | `interested` | — |
| Borrador generado | — | `drafted` | — |
| Postulado | — | `applied` | `in_progress` |
| En entrevistas | — | `interview` | `in_progress` |
| Oferta | — | `offer` | `in_progress` |
| Contratado | — | `hired` | `hired` |
| Rechazado | — | `rejected` | `rejected` |
| Sin respuesta | — | `no response` | `no_response` |
| Oferta rechazada | — | `offer declined` | `offer_declined` |
| Retirado | — | `withdrawn` | (queda `in_progress`/`interview_only`) |
| Expirado | `expired` | — | — |

Nota: el CSV usa espacios (`no response`), `outcome.md` usa guiones bajos (`no_response`). El dashboard normaliza ambos a la etapa del embudo.
