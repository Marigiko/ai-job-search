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
