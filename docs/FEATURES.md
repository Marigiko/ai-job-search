# Fase 7 — Funcionalidades nuevas

Estado de las funcionalidades propuestas. ✅ implementada · 🧩 receta lista para construir.

## 1. Radar de visa / sponsorship ✅
- Detección `visa: sponsor|relocation` en **todos** los portales (flags `--visa`), dimensión de scoring **#8**
  (`04-job-evaluation.md`) y referencia de esquemas por país en [`visa-sponsorship.md`](visa-sponsorship.md).
- La relocación pasó de veto a **señal positiva** (Fase 1d).

## 2. Seguimiento / recordatorios de follow-up ✅
- El dashboard marca ⏰ y cuenta las postulaciones en `applied`/`interview` sin mover hace ≥ `FOLLOWUP_DAYS`
  (10 por defecto, `tools/dashboard.py`). Tarjeta "Needs follow-up".
- **Receta de acción:** para redactar el follow-up, reusar el *Email application path* de `/apply` (crea un
  borrador Gmail de seguimiento al `application_url`/contacto de esa fila).

## 3. Analítica de conversión ✅
- El dashboard calcula conversión **por canal** y **por tipo de rol** (apps → interview+ → offers, con % que
  llega a entrevista). Sirve para doblar la apuesta en los canales/roles que convierten.
- Se conecta con la calibración de `/setup` (qué `role_type` produce entrevistas).

## 4. Inteligencia salarial + costo de vida 🧩
- Ya operativo: normalización a **USD mensual** e indicadores vs banda (2000/3000) en dashboard; `--min-salary`
  en RemoteOK/GetOnBoard/Jobicy/Landing.jobs; benchmark de empresa en `salary_lookup.py`.
- **Pendiente (receta):** una tabla de costo de vida neto (Buenos Aires vs ciudad destino) para comparar ofertas
  de relocación. Implementar como `tools/col_compare.py` con datos que aporte el usuario (mismo patrón BYO-data
  que `salary_lookup.py`).

## 5. Monitor + digest diario 🧩
- **Receta:** correr el pipeline en un intervalo con el skill `/loop` o `/schedule`:
  `"/loop 24h /scrape && /rank"` → deja el shortlist rankeado del día en `seen_jobs.json`; abrir el dashboard para verlo.
  No requiere código nuevo (usa `/scrape`+`/rank` ya existentes). Documentado aquí para activarlo cuando quieras.

## 6. Variantes de CV por rol 🧩
- Ya hay *profile statements* y lenguaje por rol (Backend/AI/Frontend/VibeCoder) en `05-cv-templates.md` y
  `03-writing-style.md` (Fase 1b). **Receta:** guardar un `cv/base_<rol>.tex` por rol y que `/apply` arranque del
  más cercano al posting (hoy arranca de `main_example.tex`).

## 7. Localización idiomática del CV/carta 🧩
- **Receta:** para postulaciones internacionales, generar variante en inglés (y formato local: Europass UE /
  resume 1-pág USA) además de la española. El workflow de `/apply` ya detecta el idioma del posting; extender
  para emitir la versión en el idioma destino y registrar cuál se envió.

---
Las ✅ están implementadas y probadas; las 🧩 quedan documentadas como siguiente incremento (sin bloquear el flujo actual).
