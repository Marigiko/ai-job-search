#!/usr/bin/env python3
"""OCR CLI — extract job info from images via OCR."""
import argparse
import json
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "job-scraper" / "sources"))

from image_ocr import extract_job_from_image, batch_ocr
from shared_parser import parse_job_text


def write_error(msg: str, code: str) -> None:
    sys.stderr.write(json.dumps({"error": msg, "code": code}) + "\n")


def write_output(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def cmd_ocr(args: argparse.Namespace) -> int:
    text = extract_job_from_image(args.image)
    if isinstance(text, dict):
        write_output(text)
        return 0
    write_output({"raw_text": text})
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    result = extract_job_from_image(args.image)
    if "error" in result and not result.get("raw_text"):
        write_error(result["error"], "OCR_FAILED")
        return 1
    write_output(result)
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    image_dir = Path(args.dir)
    if not image_dir.is_dir():
        write_error(f"not a directory: {image_dir}", "BAD_DIR")
        return 1
    results = batch_ocr(image_dir)
    write_output({"meta": {"count": len(results)}, "results": results})
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    write_output(parse_job_text(args.text))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="OCR CLI for job images")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ocr = sub.add_parser("ocr", help="Extract raw text from an image")
    p_ocr.add_argument("--image", required=True)

    p_ext = sub.add_parser("extract", help="Extract + parse job fields from an image")
    p_ext.add_argument("--image", required=True)

    p_batch = sub.add_parser("batch", help="Batch OCR a directory of job images")
    p_batch.add_argument("--dir", required=True)

    p_parse = sub.add_parser("parse", help="Parse raw text into job fields")
    p_parse.add_argument("--text", required=True)

    args = ap.parse_args()
    cmds = {"ocr": cmd_ocr, "extract": cmd_extract, "batch": cmd_batch, "parse": cmd_parse}
    sys.exit(cmds[args.cmd](args))


if __name__ == "__main__":
    main()
