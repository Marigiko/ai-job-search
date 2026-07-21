# Prompt para OpenCode — Tareas pendientes AI Job Search

Copia y pega esto en OpenCode para que termine las tareas pendientes:

---

Estoy trabajando en el repo `/mnt/d/Projects/ai-job-search` (rama `feat/second-job-relocation-extension`). Hay 4 tareas pendientes. Hazlas en orden:

## 1. Compilar 4 CVs con lualatex en MiKTeX

Los CVs están en `cv/`. Son: `main_speer.tex`, `main_zaelot.tex`, `main_toloka.tex`, `main_orangeuni.tex`. compilalos con:

```bash
cd cv
for f in main_speer main_zaelot main_toloka main_orangeuni; do
  lualatex -interaction=nonstopmode "$f.tex"
  lualatex -interaction=nonstopmode "$f.tex"  # segundo pass para referencias
done
```

Verifica que:
- El PDF tiene exactamente 2 páginas (usa `pypdf` o `pdfinfo` para contar)
- No hay títulos `\cventry` huérfanos (título al final de página 1 sin bullets)
- Los covers en `cover_letters/` compilan con `xelatex` y son 1 página

Si algún CV no cumple, ajusta el LaTeX (usa `\needspace{5\baselineskip}` antes de cada `\cventry` y `\enlargethispage{-3\baselineskip}` si se desborda).

## 2. 7 jobs de LinkedIn — por ahora solo documentarlos

Los 7 jobs en `job_search_tracker.csv` con estado `pending_user_action` no se pueden aplicar automáticamente (LinkedIn detecta automatización). Están esperando a que el usuario pase posts de recruiters. No hagas nada con estos por ahora, solo verifica que el workflow `linkedin_email_workflow.py` funcionaDry-run de prueba:

```bash
python3 .agents/skills/job-scraper/linkedin_email_workflow.py \
  --text "Hiring backend! Send CV to jobs [at] company [dot] com" \
  --company "TestCo" --role "Backend" --dry-run
```

Debería imprimir: `Apply to: jobs@company.com for Backend`.

## 3. Validar las mejoras de plataforma

Ejecuta todos los tests:

```bash
cd /mnt/d/Projects/ai-job-search
python3 -m pytest tests/ -v
```

Deben pasar 82 tests. Si alguno falla, corrígelo.

Valida `setup.sh` (solo verifica que existe y tiene contenido, no lo ejecutes si no tienes bun):

```bash
cat setup.sh | head -5
cat requirements.txt
```

## 4. Actualiza el dashboard

```bash
python3 tools/dashboard.py
```

---

Al final:
- Haz `git add -A && git commit -m "chore: validate pending tasks, verify compilation, run tests"` si hubo cambios
- Dame un resumen de qué se hizo, qué pasó y si quedó algo pendiente
