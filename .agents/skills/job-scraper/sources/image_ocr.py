# .agents/skills/job-scraper/sources/image_ocr.py
"""Extract job info from images via OCR.

Primary: rapidocr (ONNX, no binary needed).
Fallback: pytesseract (requires Tesseract binary).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared_parser import parse_job_text


def extract_job_from_image(image_path: str | Path) -> dict:
    """Run OCR on a job posting image and return structured data."""
    image_path = str(image_path)
    text = _ocr(image_path)
    if not text:
        return {"raw_text": "", "error": "OCR produced no text", "title": None, "company": None, "apply_email": None}
    return {"raw_text": text, **parse_job_text(text)}


def _ocr(image_path: str) -> str:
    """Try rapidocr first, then pytesseract."""
    try:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR()
        result, _ = engine(image_path)
        if result:
            return "\n".join(line[1] for line in result)
    except ImportError:
        pass
    except Exception:
        pass

    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(image_path))
    except ImportError:
        pass
    except Exception:
        pass

    return ""


def batch_ocr(image_dir: str | Path) -> list[dict]:
    """Run OCR on all images in a directory. Returns list of {path, raw_text, ...}."""
    image_dir = Path(image_dir)
    results = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"):
        for img in image_dir.glob(ext):
            entry = extract_job_from_image(img)
            entry["image_path"] = str(img)
            results.append(entry)
    return results
