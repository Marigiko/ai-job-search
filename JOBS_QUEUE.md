# Jobs Queue — ESTADO ACTUALIZADO 2026-07-15

> Generado 2026-07-15 tras `/apply` masivo a las 21 jobs pendientes.
> **Estado: TODAS REDACTADAS (drafted)** — falta compilación + envío.

## Resumen

- Total en tracker: **19 aplicaciones** (`job_search_tracker.csv`, status `drafted`)
- CVs compilados: **0** (necesitan MiKTeX/lualatex)
- Covers compilados: **4** (Speer, Zaelot, Toloka, Orange Uni — de sesión anterior)
- Listos para compilar + enviar: **TODAS**

## Próximo paso para compilación

En Windows (MiKTeX):

```bash
cd cv
lualatex -interaction=nonstopmode main_speer.tex
lualatex -interaction=nonstopmode main_zaelot.tex
lualatex -interaction=nonstopmode main_toloka.tex
lualatex -interaction=nonstopmode main_orangeuni.tex
lualatex -interaction=nonstopmode main_bctecnologia.tex
lualatex -interaction=nonstopmode main_eversheds.tex
lualatex -interaction=nonstopmode main_kaizen.tex
lualatex -interaction=nonstopmode main_cysinformatica.tex
lualatex -interaction=nonstopmode main_tfutureperfect.tex
lualatex -interaction=nonstopmode main_factorit.tex
lualatex -interaction=nonstopmode main_restream.tex
lualatex -interaction=nonstopmode main_bcfastapi.tex
lualatex -interaction=nonstopmode main_10alabs.tex
lualatex -interaction=nonstopmode main_africanqueen.tex
lualatex -interaction=nonstopmode main_gvh.tex
lualatex -interaction=nonstopmode main_maipu.tex
lualatex -interaction=nonstopmode main_bjak.tex
lualatex -interaction=nonstopmode main_sugarshan.tex
lualatex -interaction=nonstopmode main_rapidseedbox.tex
```

Los covers se compilan con xelatex (nuevo en el directorio cover_letters):

```bash
cd cover_letters
xelatex -interaction=nonstopmode cover_<empresa>_<rol>.tex
```

Después de cada cover, copiar el `cover.cls` y `OpenFonts/` al mismo directorio antes de compilar.

## Desglose por score

| # | Score | Empresa | Rol | Cover | CV |
|---|-------|---------|-----|-------|-----|
| 5 | 83 | BC Tecnologia | Sr Backend Node/TS/AWS | cover_bctecnologia_backend | main_bctecnologia |
| 6 | 82 | Eversheds Sutherland | AI Application Developer | cover_eversheds_ai | main_eversheds |
| 7 | 80 | Kaizen RRHH | Sr Backend Python | cover_kaizen_backend | main_kaizen |
| 8 | 79 | C&S informática | Fullstack Node/Python/TS | cover_cysinformatica_fullstack | main_cysinformatica |
| 9 | 79 | The Future Perfect | Freelance AI Automation | cover_tfutureperfect_ai_automation | main_tfutureperfect |
| 10 | 76 | Factor IT | Generative AI Engineer | cover_factorit_genai | main_factorit |
| 11 | 76 | Restream | Backend Engineer (AI Clips) | cover_restream_backend | main_restream |
| 12 | 73 | BC Tecnologia | Backend Python/FastAPI | cover_bcfastapi_python | main_bcfastapi |
| 13 | 73 | 10a Labs | Data Engineer Web Scraping | cover_10alabs_scraping | main_10alabs |
| 14 | 72 | African Queen Mktg | Backend SaaS/API | cover_africanqueen_backend | main_africanqueen |
| 15 | 72 | Great Value Hiring | ML Eval AI Coding | cover_gvh_ml_eval | main_gvh |
| 17 | 68 | Maipú Mendoza | Full Stack Node/React/n8n | cover_maipu_fullstack | main_maipu |
| 20 | 66 | BJAK | Backend Developer (Tokyo) | cover_bjak_backend | main_bjak |
| 24 | 60 | SugarShan | Real Time Voice AI | cover_sugarshan_voice_ai | main_sugarshan |
| 25 | 60 | Rapidseedbox | Head of Engineering CTO | cover_rapidseedbox_head | main_rapidseedbox |

## Sesión anterior (4 redactas antes de hoy)

| Score | Empresa | Rol | Cover (compilado?!) | CV |
|-------|---------|-----|---------------------|-----|
| 87 | Speer Technologies | Backend Engineer | cover_speer_backend_engineer ✅ | main_speer |
| 86 | Zaelot | Sr/Lead Full-Stack | cover_zaelot_fullstack_engineer ✅ | main_zaelot |
| 85 | Toloka AI | SWE Testing AI Agents | cover_toloka_ai_swe ✅ | main_toloka |
| 82 | Orange Uni | Sr Python Backend | cover_orangeuni_python_backend ✅ | main_orangeuni |

## VETOS (no postular)
- Devups (pago $1800-2000/mo — bajo mínimo)
- ADN RRHH Ref 20595/21175 (sueldo ARS)
- Happl (Go excluyente)
- Solutix (Go excluyente)
- Aardvark (Go + EU sin visa)
- Atlas Search (10+ años)
- YouTrip (Go)
- Quora (new-grad)

## Proceso de envío sugerido
1. Compilar todos los CVs (lualatex) — verificar 2 páginas
2. Compilar todos los covers (xelatex) — verificar 1 página  
3. Aplicar por el canal del aviso (URL en el tracker)
4. `/outcome <empresa>` para mover a `applied`
