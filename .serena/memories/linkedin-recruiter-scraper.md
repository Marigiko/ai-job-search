Scraper de posts de recruiters LinkedIn creado (2026-07-15).

Archivo: .agents/skills/linkedin-recruiter-scraper/scraper.py

Qué hace: busca en Google/Bing con operador "site:linkedin.com/posts" para encontrar
posts públicos de recruiters que incluyen email de aplicación. Luego usa el CLI
existente linkedin-posts-search (bun/TS) para extraer applyEmail de cada URL.

Uso:
  python3 .agents/skills/linkedin-recruiter-scraper/scraper.py \
    --queries queries.txt --out results.json --max-results 5 --engine google

Queries viven en: .agents/skills/linkedin-recruiter-scraper/queries.txt

Requisitos: python3 con playwright (chromium instalado), bun (para el CLI externo).
Google da mejores resultados que Bing; Bing a veces devuelve 0 links. Google puede
interceptar con consent/CAPTCHA (el scraper lo detecta y saltea la query).

El scraper se integra con linkedin_email_workflow.py para postulación automática.
