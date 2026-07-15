# tests/test_sources.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import importlib.util

def _load(name):
    _spec = importlib.util.spec_from_file_location(
        name,
        Path(__file__).resolve().parent.parent / ".agents" / "skills" / "job-scraper" / "sources" / f"{name}.py",
    )
    mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(mod)
    return mod

whatsapp = _load("whatsapp_source")
discord = _load("discord_source")
telegram = _load("telegram_source")
image_ocr = _load("image_ocr")


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
    result = whatsapp.parse(text)
    assert result["company"] == "TechCorp"
    assert "backend" in result["title"].lower()
    assert result["apply_email"] == "jobs@techcorp.com"
    assert result["salary"] == "3000-4000 USD/mes"


def test_whatsapp_obfuscated_email():
    text = "Enviar CV a contacto [at] empresa [dot] com"
    result = whatsapp.parse(text)
    assert result["apply_email"] == "contacto@empresa.com"


def test_discord_parse():
    text = """
    **Hiring: Senior Backend Engineer**
    Company: StartupXYZ
    Location: Remote (Worldwide)
    Salary: $4000-6000/month
    Apply: careers@startupxyz.com
    """
    result = discord.parse(text)
    assert result["company"] == "StartupXYZ"
    assert result["apply_email"] == "careers@startupxyz.com"


def test_telegram_parse():
    text = """
    🔥 VACANTE
    Empresa: DevHouse
    Rol: Full Stack Developer
    Ubicación: Híbrido, México
    Salario: $3500 USD/mes
    Aplica a: jobs@devhouse.mx
    """
    result = telegram.parse(text)
    assert result["company"] == "DevHouse"
    assert result["apply_email"] == "jobs@devhouse.mx"


def test_image_ocr_no_pillow():
    result = image_ocr.extract_job_from_image("jobs_images/nonexistent.png")
    assert isinstance(result, dict)
    # Either works (if pytesseract installed) or returns error gracefully
    assert "raw_text" in result or "error" in result
