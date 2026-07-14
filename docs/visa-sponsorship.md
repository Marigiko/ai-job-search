# Radar de visa / relocación (referencia)

Apoyo a la dimensión de scoring **#8 Relocation & Visa Fit** (`04-job-evaluation.md`) y a los flags
`--visa` de los portales. Objetivo: reconocer rápido señales de patrocinio de visa / relocación y priorizarlas.

## Señales en el texto de la oferta (ya detectadas por los skills)
Los portales marcan `visa: "sponsor" | "relocation" | null` buscando (case-insensitive):
`visa`, `sponsor(ship)`, `work permit`, `relocation`, `relocate`, `relocación`, `mudanza`, y el flag
`relocation_paid` de Landing.jobs. Al evaluar una oferta, buscá además frases como:
- EN: "visa sponsorship available", "we sponsor", "relocation package/assistance", "willing to relocate"
- ES: "patrocinio de visa", "cubrimos la relocación", "reubicación"

## Esquemas por país destino (para verificar el patrocinio)
| País | Esquema / palabra clave a buscar | Notas |
|------|----------------------------------|-------|
| 🇩🇪 Alemania / UE | **EU Blue Card**, "Fachkräfte", "Blaue Karte" | salario mínimo anual; Arbeitnow/Landing.jobs suelen marcarlo |
| 🇳🇱 Países Bajos | **Highly Skilled Migrant**, "kennismigrant", "30% ruling" | empleador debe ser *recognized sponsor* (lista IND) |
| 🇳🇿 Nueva Zelanda | **Accredited Employer Work Visa (AEWV)** | el empleador debe estar *accredited*; buscarlo en la oferta |
| 🇺🇸 EE. UU. | **H-1B**, "visa sponsorship", "cap-exempt", O-1 | H-1B por lotería; muchas ofertas dicen "no sponsorship" → filtrar |
| 🇨🇦 Canadá | **LMIA**, "Express Entry", "Global Talent Stream" | GTS es rápido para tech |
| 🇮🇪 Irlanda | **Critical Skills Employment Permit** | lista de ocupaciones críticas incluye software |
| 🇬🇧 Reino Unido | **Skilled Worker visa**, "sponsor licence" | empleador con *sponsor licence* (lista gov.uk) |
| 🇦🇺 Australia | **TSS 482 / Skills in Demand** | ocupaciones en la lista |

## Cómo usarlo en el flujo
- En `/rank` y `/apply`, un posting con patrocinio/relocación **sube** en la dimensión 8 (85–100).
- Verificá siempre el patrocinio en la fuente antes de asumirlo (el `visa` de los skills es una **pista**, no autoridad).
- Empleadores "recognized/accredited sponsor" son señal fuerte: si la oferta nombra el esquema, es real.
- Mantené aquí una lista propia de empresas-sponsor confirmadas a medida que apliques (feedback loop con `/outcome`).

## Empleadores-sponsor confirmados (se completa con la experiencia)
_(agregá aquí empresas que confirmaste que patrocinan, con país y fecha)_
