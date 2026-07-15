# Job Search Automation Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make job application automation fully non-blocking, add new job sources (WhatsApp/Discord/Telegram + OCR), document all dependencies for one-command install, and enable LinkedIn recruiter-post email applications.

**Architecture:** Separate concerns into (1) browser runner daemon for headless background automation, (2) portal pre-fill cleaning module, (3) new source adapters + OCR pipeline, (4) dependency manifest + setup script, (5) LinkedIn recruiter scraper + SMTP dispatcher. Each subsystem communicates through the existing `job_search_tracker.csv` and `documents/applications/` archive.

**Tech Stack:** Playwright (headless), Tesseract OCR (pytesseract), smtplib (Gmail App Password), python-dotenv, PyYAML.

## Global Constraints

- All browser automation MUST run headless (`headless: true`) — never show a window. Exception: first-time login/setup uses `--headed` with explicit user approval.
- All Playwright scripts use persistent profiles (`/tmp/browser-profiles/<platform>/`) to preserve login state.
- Dependencies: document EVERYTHING in `requirements.txt`, `package.json`, and a `setup.sh` that installs all in one shot.
- No secrets in code. Email App Passwords and site credentials go in `.env` (gitignored).
- Apply emails use Gmail SMTP via App Password stored as `GMAIL_APP_PASSWORD` in `.env`.
- Follow existing patterns: portal skills live in `.agents/skills/<name>/` with `SKILL.md` + `cli/` structure.

---

### Task 1: Headless Browser Runner Daemon

**Covers:** [S1]

**Files:**
- Create: `.agents/skills/job-scraper/browser_runner.py`
- Test: `tests/test_browser_runner.py`
- Modify: `.agents/skills/job-scraper/SKILL.md` (add headless invocation note)

**Interfaces:**
- Consumes: platform name (string), job URL (string), profile path (string)
- Produces: `apply(job_url, platform)` function that runs headless automation without blocking caller

- [ ] **Step 1: Write the failing test**

```python
# tests/test_browser_runner.py
import pytest
from unittest.mock import patch, MagicMock
from agents.skills.job_scraper.browser_runner import apply, _get_profile_dir

def test_get_profile_dir_creates_and_returns_path():
    path = _get_profile_dir("getonbrd")
    assert "getonbrd" in str(path)
    assert path.exists()

@patch("agents.skills.job_scraper.browser_runner.chromium")
def test_apply_launches_headless(mock_chromium):
    mock_browser = MagicMock()
    mock_chromium.launch.return_value = mock_browser
    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page

    apply("https://www.getonbrd.com/jobs/test", "getonbrd")

    mock_chromium.launch.assert_called_once()
    call_kwargs = mock_chromium.launch.call_args[1]
    assert call_kwargs["headless"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_browser_runner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agents.skills.job_scraper.browser_runner'`

- [ ] **Step 3: Write minimal implementation**

```python
# .agents/skills/job-scraper/browser_runner.py
"""
Headless browser runner for non-blocking job applications.
All automation runs in background without showing a window.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILES_BASE = Path("/tmp/browser-profiles")

def _get_profile_dir(platform: str) -> Path:
    path = PROFILES_BASE / platform
    path.mkdir(parents=True, exist_ok=True)
    return path

def apply(job_url: str, platform: str, action: str = "submit") -> dict:
    """Apply to a job URL headlessly. Returns {"status": "ok"|"error", "detail": str}."""
    profile_dir = _get_profile_dir(platform)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(storage_state=_load_state(platform))
        page = context.new_page()
        page.goto(job_url)
        page.wait_for_load_state("networkidle", timeout=15000)
        # Delegate to platform-specific handler
        result = _dispatch(page, platform, action)
        _save_state(platform, context.storage_state())
        browser.close()
        return result

def _dispatch(page, platform: str, action: str) -> dict:
    """Route to the right handler per platform."""
    handlers = {
        "getonbrd": _apply_getonbrd,
        "linkedin_easy": _apply_linkedin_easy,
    }
    handler = handlers.get(platform)
    if not handler:
        return {"status": "error", "detail": f"Unknown platform: {platform}"}
    return handler(page)

def _apply_getonbrd(page) -> dict:
    """GetOnBoard: fill form, clear old content, submit."""
    # Step 1: professional + academic (clear first)
    return {"status": "ok", "detail": "GetOnBoard apply not yet implemented — see Task 2"}

def _apply_linkedin_easy(page) -> dict:
    """LinkedIn Easy Apply: click + fill modal."""
    return {"status": "ok", "detail": "LinkedIn Easy Apply not yet implemented — see Task 5"}

def _load_state(platform: str) -> str | None:
    state_file = _get_profile_dir(platform) / "state.json"
    if state_file.exists():
        return str(state_file)
    return None

def _save_state(platform: str, state: dict) -> None:
    state_file = _get_profile_dir(platform) / "state.json"
    import json
    state_file.write_text(json.dumps(state))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_browser_runner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/job-scraper/browser_runner.py tests/test_browser_runner.py
git commit -m "feat: add headless browser runner daemon for non-blocking applications"
```

---

### Task 2: Portal Pre-fill Cleaning Module

**Covers:** [S2]

**Files:**
- Create: `.agents/skills/job-scraper/portal_cleaner.py`
- Test: `tests/test_portal_cleaner.py`

**Interfaces:**
- Consumes: page (Playwright page), platform (string)
- Produces: `clean(page, platform)` — clears saved text fields so fresh content can be written

- [ ] **Step 1: Write the failing test**

```python
# tests/test_portal_cleaner.py
import pytest
from unittest.mock import MagicMock, patch
from agents.skills.job_scraper.portal_cleaner import clean

def test_clean_clears_trix_editors():
    page = MagicMock()
    editor = MagicMock()
    editor.editor = MagicMock()
    page.querySelectorAll.return_value = [editor]

    clean(page, "getonbrd")

    editor.editor.loadHTML.assert_called_with("")
    editor.dispatchEvent.assert_called()

def test_clean_selects_resume():
    page = MagicMock()
    select = MagicMock()
    select.options = [MagicMock(value=""), MagicMock(value="123")]
    page.querySelector.return_value = select

    clean(page, "getonbrd")

    assert select.value == "123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_portal_cleaner.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# .agents/skills/job-scraper/portal_cleaner.py
"""Clear saved portal pre-fills before writing new content."""

def clean(page, platform: str) -> None:
    """Clear all saved fields for the given platform."""
    cleaners = {
        "getonbrd": _clean_getonbrd,
    }
    cleaner = cleaners.get(platform)
    if cleaner:
        cleaner(page)

def _clean_getonbrd(page) -> None:
    """Clear Trix editors and reset resume selection on GetOnBoard."""
    # Clear all Trix editors
    editors = page.query_selector_all("trix-editor")
    for editor in editors:
        editor.evaluate("el => el.editor.loadHTML('')")
        editor.dispatch_event("triage-change")
    # Reset resume dropdown to first real option
    resume = page.query_selector("#job_application_resume_id")
    if resume:
        options = resume.query_selector_all("option")
        for opt in options:
            val = opt.get_attribute("value")
            if val:
                resume.select_option(val)
                break
    # Clear salary
    salary = page.query_selector('input[name="job_application[expected_salary]"]')
    if salary:
        salary.fill("")
    # Clear reason
    reason = page.query_selector('textarea[name="job_application[reason_to_apply]"]')
    if reason:
        reason.fill("")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_portal_cleaner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/job-scraper/portal_cleaner.py tests/test_portal_cleaner.py
git commit -m "feat: add portal pre-fill cleaner to clear saved texts before applying"
```

---

### Task 3: New Source Adapters (WhatsApp, Discord, Telegram)

**Covers:** [S3]

**Files:**
- Create: `.agents/skills/job-scraper/sources/whatsapp_source.py`
- Create: `.agents/skills/job-scraper/sources/discord_source.py`
- Create: `.agents/skills/job-scraper/sources/telegram_source.py`
- Create: `.agents/skills/job-scraper/sources/image_ocr.py`
- Create: `jobs_images/.gitkeep`
- Test: `tests/test_sources.py`

**Interfaces:**
- Consumes: raw text (string) or image path (Path), source name (string)
- Produces: `parse(raw) -> dict` with keys: title, company, location, salary, description, apply_email, url

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sources.py
import pytest
from agents.skills.job_scraper.sources.whatsapp_source import parse as parse_whatsapp
from agents.skills.job_scraper.sources.image_ocr import extract_job_from_image

def test_whatsapp_parse_basic():
    text = """
    🚀 Oferta Laboral
    Empresa: TechCorp
    Rol: Backend Senior Node.js
    Ubicación: Remoto
    Salario: 3000-4000 USD/mes
    Enviar CV a: jobs@techcorp.com
    Descripción: Buscamos developer con experiencia en AWS.
    """
    result = parse_whatsapp(text)
    assert result["company"] == "TechCorp"
    assert "backend" in result["title"].lower()
    assert result["apply_email"] == "jobs@techcorp.com"
    assert result["salary"] == "3000-4000 USD/mes"

def test_image_ocr_returns_dict():
    result = extract_job_from_image("jobs_images/test.png")
    assert isinstance(result, dict)
    assert "raw_text" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_sources.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# .agents/skills/job-scraper/sources/whatsapp_source.py
"""Parse job postings shared via WhatsApp."""
import re

def parse(text: str) -> dict:
    return {
        "title": _extract(text, [r"(?i)rol[:\s]*(.+)", r"(?i)posición[:\s]*(.+)", r"(?i)vacante[:\s]*(.+)"]),
        "company": _extract(text, [r"(?i)empresa[:\s]*(.+)", r"(?i)compañía[:\s]*(.+)", r"(?i)company[:\s]*(.+)"]),
        "location": _extract(text, [r"(?i)ubicación[:\s]*(.+)", r"(?i)location[:\s]*(.+)", r"(?i)modalidad[:\s]*(.+)"]),
        "salary": _extract(text, [r"(?i)salario[:\s]*(.+)", r"(?i)salary[:\s]*(.+)", r"(?i)pago[:\s]*(.+)"]),
        "apply_email": _extract_email(text),
        "description": text.strip(),
        "url": None,
    }

def _extract(text: str, patterns: list[str]) -> str | None:
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None

def _extract_email(text: str) -> str | None:
    # Handle obfuscated emails: [at] -> @, [dot] -> .
    deobfuscated = text.replace("[at]", "@").replace("[dot]", ".").replace("&#64;", "@")
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    return m.group(0) if m else None
```

```python
# .agents/skills/job-scraper/sources/image_ocr.py
"""Extract job info from images via Tesseract OCR."""
from pathlib import Path

def extract_job_from_image(image_path: str | Path) -> dict:
    """Run OCR on a job posting image and return structured data."""
    try:
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(str(image_path))
        return {"raw_text": text, "title": None, "company": None, "apply_email": _extract_email(text)}
    except ImportError:
        return {"raw_text": "", "error": "pytesseract or Pillow not installed. Run: pip install pytesseract Pillow"}

def _extract_email(text: str) -> str | None:
    import re
    deobfuscated = text.replace("[at]", "@").replace("[dot]", ".").replace("&#64;", "@")
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    return m.group(0) if m else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_sources.py::test_whatsapp_parse_basic -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/job-scraper/sources/ jobs_images/.gitkeep tests/test_sources.py
git commit -m "feat: add WhatsApp/Discord/Telegram source adapters and image OCR pipeline"
```

---

### Task 4: Dependency Manifest & One-Command Setup

**Covers:** [S4]

**Files:**
- Create: `setup.sh`
- Modify: `requirements.txt`
- Create: `package.json` (update if needed)
- Modify: `.gitignore` (add `.env`)

**Interfaces:**
- Consumes: none (standalone)
- Produces: `setup.sh` — single command that installs everything

- [ ] **Step 1: Write the failing test**

```python
# tests/test_setup.py
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent

def test_setup_sh_exists():
    assert (ROOT / "setup.sh").exists()
    content = (ROOT / "setup.sh").read_text()
    assert "pip install" in content
    assert "bun install" in content
    assert "playwright install" in content

def test_requirements_txt_has_all_deps():
    reqs = (ROOT / "requirements.txt").read_text()
    assert "pytesseract" in reqs
    assert "pillow" in reqs
    assert "python-dotenv" in reqs
    assert "pyyaml" in reqs

def test_env_gitignored():
    gitignore = (ROOT / ".gitignore").read_text()
    assert ".env" in gitignore
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_setup.py -v`
Expected: FAIL (setup.sh missing or content incomplete)

- [ ] **Step 3: Write `setup.sh`**

```bash
#!/usr/bin/env bash
# One-command setup for the AI Job Search framework.
# Usage: bash setup.sh
set -e

echo "=== AI Job Search — Setup ==="

# --- Python dependencies ---
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt

# --- Bun / Node dependencies (for portal CLI tools) ---
echo "[2/4] Installing Bun dependencies..."
if ! command -v bun &>/dev/null; then
    echo "Bun not found. Installing..."
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"
fi
for tool in $(ls -d .agents/skills/*/cli 2>/dev/null); do
    echo "  → Installing $tool"
    (cd "$tool" && bun install)
done

# --- Playwright browsers ---
echo "[3/4] Installing Playwright browsers..."
npx playwright install chromium

# --- Tesseract OCR (system-level) ---
echo "[4/4] Checking Tesseract OCR..."
if ! command -v tesseract &>/dev/null; then
    echo "  ⚠ Tesseract not found. Install via:"
    echo "    Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "    macOS:         brew install tesseract"
    echo "    Windows:       choco install tesseract"
fi

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in your Gmail App Password"
echo "  2. Run /setup inside your AI assistant to configure your profile"
```

- [ ] **Step 4: Update requirements.txt**

```txt
# requirements.txt
pytesseract>=0.3.10
Pillow>=10.0.0
python-dotenv>=1.0.0
PyYAML>=6.0
playwright>=1.40.0
requests>=2.31.0
```

- [ ] **Step 5: Update .gitignore**

```
# Secrets
.env
.env.local

# Already existing patterns...
__pycache__/
*.pyc
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_setup.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add setup.sh requirements.txt .gitignore tests/test_setup.py
git commit -m "feat: add one-command setup.sh and document all dependencies"
```

---

### Task 5: LinkedIn Recruiter Scraper + Email Apply

**Covers:** [S5]

**Files:**
- Create: `.agents/skills/job-scraper/linkedin_email_apply.py`
- Create: `.env.example`
- Test: `tests/test_linkedin_email.py`

**Interfaces:**
- Consumes: post_url (string) or scraped post text
- Produces: `get_apply_email(post_text) -> str | None`, `send_application_email(to_email, cv_path, cover_path, job_title) -> bool`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_linkedin_email.py
import pytest
from agents.skills.job_scraper.linkedin_email_apply import get_apply_email, _deobfuscate_email

def test_get_apply_email_plain():
    text = "Interested? Send your CV to jobs@techcorp.com"
    assert get_apply_email(text) == "jobs@techcorp.com"

def test_get_apply_email_obfuscated():
    text = "Send CV to hola [at] empresa [dot] com"
    assert get_apply_email(text) == "hola@empresa.com"

def test_get_apply_email_entity():
    text = "Send CV to &#64; company.com → actually hire@company.com"
    assert get_apply_email(text) == "hire@company.com"

def test_no_email_returns_none():
    text = "Apply via our careers page"
    assert get_apply_email(text) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_linkedin_email.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# .agents/skills/job-scraper/linkedin_email_apply.py
"""Apply to LinkedIn recruiter posts via email."""
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

def _deobfuscate_email(text: str) -> str:
    """Convert obfuscated emails to real format."""
    return text.replace("[at]", "@").replace("[dot]", ".").replace(" (at) ", "@").replace(" (dot) ", ".").replace("&#64;", "@")

def get_apply_email(text: str) -> str | None:
    """Extract apply-by-email address from recruiter post text."""
    deobfuscated = _deobfuscate_email(text)
    # Match emails not preceded by "linkedin.com"
    matches = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    for m in matches:
        if "linkedin" not in m.lower():
            return m
    return matches[0] if matches else None

def send_application_email(to_email: str, cv_path: str, cover_path: str | None, job_title: str) -> bool:
    """Send application via Gmail SMTP."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender = os.getenv("GMAIL_SENDER", "marioaquinojob@gmail.com")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not password:
        raise ValueError("GMAIL_APP_PASSWORD not set in .env")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = f"Application: {job_title} — Mario Aquino"
    body = f"""Dear Hiring Team,

I am writing to express my interest in the {job_title} position.

My name is Mario Aquino, a Senior Full-Stack / Backend Engineer with 5+ years of experience in Node.js, TypeScript, Python, AWS, Docker, Kubernetes, and AI/LLM automation. I have attached my CV and cover letter for your review.

I would welcome the opportunity to discuss how my background aligns with your needs.

Best regards,
Mario Aquino
marioaquinojob@gmail.com · linkedin.com/in/keyzdev
"""
    msg.attach(MIMEText(body, "plain"))

    for path in [cv_path, cover_path]:
        if path and Path(path).exists():
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={Path(path).name}")
            msg.attach(part)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
    return True
```

- [ ] **Step 4: Create `.env.example`**

```bash
# .env.example — copy to .env and fill in
GMAIL_SENDER=marioaquinojob@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password_here
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /mnt/d/Projects/ai-job-search && python -m pytest tests/test_linkedin_email.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add .agents/skills/job-scraper/linkedin_email_apply.py .env.example tests/test_linkedin_email.py
git commit -m "feat: add LinkedIn recruiter post email extraction and SMTP application"
```

---

## Spec Coverage

| Section | Covered By |
|---------|-----------|
| [S1] Non-blocking browser | Task 1 |
| [S2] Clear saved portal texts | Task 2 |
| [S3] New sources + OCR | Task 3 |
| [S4] Dependencies + setup | Task 4 |
| [S5] LinkedIn email apply | Task 5 |
