---
name: image-ocr
version: 1.0.0
description: >
  Use this skill to extract job posting info from images via OCR (rapidocr primary,
  pytesseract fallback). Works on single images or batch processes the jobs_images/
  directory. Returns structured job data (title, company, email, description) ready
  for the /apply flow. Trigger phrases: job image, screenshot job, ocr job posting,
  image ocr, parse job image, jobs_images, image to job.
context: fork
allowed-tools: Bash(python3 .agents/skills/image-ocr/cli/ocr_cli.py *)
---

# Image OCR Skill

Extract job posting data from images. Uses **rapidocr** (ONNX, no binary needed) as
primary engine and **pytesseract** (requires Tesseract binary) as fallback.

## When to use

- User shares a job posting image (screenshot, photo)
- Batch-processing the `jobs_images/` directory
- Any time job info arrives as an image rather than text

## Commands

### OCR a single image

```bash
python3 .agents/skills/image-ocr/cli/ocr_cli.py ocr --image path/to/image.png
```

### OCR an image and parse job fields

```bash
python3 .agents/skills/image-ocr/cli/ocr_cli.py extract --image path/to/image.png
```

### Batch OCR a directory

```bash
python3 .agents/skills/image-ocr/cli/ocr_cli.py batch --dir jobs_images/
```

### Parse already-extracted text

```bash
python3 .agents/skills/image-ocr/cli/ocr_cli.py parse --text "raw OCR text"
```

## Output contract

`extract` and `batch` emit:
```json
{
  "raw_text": "...",
  "title": "...",
  "company": "...",
  "location": "...",
  "salary": "...",
  "apply_email": "jobs@company.com",
  "description": "...",
  "url": "...",
  "image_path": "jobs_images/xxx.png"
}
```

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Notes

- Images in `jobs_images/` are organized by source: `jobs_images/whatsapp/`, `jobs_images/telegram/`, etc.
- rapidocr handles Latin text well; for complex layouts install Tesseract separately.
