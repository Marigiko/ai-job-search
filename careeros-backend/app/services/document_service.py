"""Document service — async LaTeX compilation, CV/CL generation, version tracking."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus, DocumentType
from app.schemas.document import DocumentCompileResult, DocumentGenerateRequest

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _storage_root() -> Path:
    """Root directory for generated PDFs. Defaults to ./storage/documents."""
    settings = get_settings()
    env_override = getattr(settings, "document_storage_path", None)
    if env_override:
        return Path(env_override).resolve()
    return (Path(__file__).resolve().parent.parent.parent / "storage" / "documents").resolve()


def _templates_root() -> Path:
    """Root directory for LaTeX templates. Defaults to ../../templates."""
    return (Path(__file__).resolve().parent.parent.parent / "templates" / "documents").resolve()


def _build_output_dir(job_posting_id: int, doc_type: DocumentType, version: int) -> Path:
    """Return and create the output directory for a specific document version."""
    root = _storage_root()
    out = root / f"job_{job_posting_id}" / f"{doc_type}_v{version}"
    out.mkdir(parents=True, exist_ok=True)
    return out


# ---------------------------------------------------------------------------
# Version tracking
# ---------------------------------------------------------------------------


async def _next_version(db: AsyncSession, job_posting_id: int, doc_type: DocumentType) -> int:
    """Compute the next version number for a (job, type) pair."""
    result = await db.execute(
        select(func.max(Document.version)).where(
            Document.job_posting_id == job_posting_id,
            Document.document_type == doc_type,
        )
    )
    current = result.scalar_one_or_none()
    return (current or 0) + 1


# ---------------------------------------------------------------------------
# Document generation orchestration
# ---------------------------------------------------------------------------


@dataclass
class GeneratedDocument:
    id: int
    status: DocumentStatus


async def generate_document(
    db: AsyncSession, payload: DocumentGenerateRequest
) -> GeneratedDocument:
    """Create a Document row and kick off async compilation.

    Returns immediately with the document ID; the caller can poll status
    or trigger compilation in the background via FastAPI BackgroundTasks.
    """
    if payload.document_type not in ("cv", "cover_letter"):
        raise ValidationError(f"Invalid document_type: {payload.document_type}")

    version = await _next_version(db, payload.job_posting_id, payload.document_type)

    doc = Document(
        job_posting_id=payload.job_posting_id,
        application_id=payload.application_id,
        document_type=payload.document_type,
        version=version,
        template_name=payload.template_name,
        variables_json=json.dumps(payload.variables) if payload.variables else None,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(
        "Document queued: id=%d job=%d type=%s version=%d template=%s",
        doc.id,
        payload.job_posting_id,
        payload.document_type,
        version,
        payload.template_name,
    )
    return GeneratedDocument(id=doc.id, status="pending")


# ---------------------------------------------------------------------------
# LaTeX compilation (async subprocess)
# ---------------------------------------------------------------------------


def _resolve_template_path(template_name: str, doc_type: DocumentType) -> Path:
    """Locate the .tex template file by name.

    Search order:
      1. templates/documents/{cv,cover_letter}/{template_name}.tex
      2. Fallback: exact path if template_name already includes extension.
    """
    subdir = "cv" if doc_type == "cv" else "cover_letter"
    candidate = _templates_root() / subdir / f"{template_name}.tex"
    if candidate.exists():
        return candidate

    # Allow full relative paths as a fallback
    alt = _templates_root() / subdir / template_name
    if alt.exists():
        return alt

    raise NotFoundError(
        f"Template '{template_name}' not found for type '{doc_type}' "
        f"(looked in {_templates_root() / subdir})"
    )


def _select_latex_engine(tex_path: Path) -> str:
    """Pick the best LaTeX engine based on template content.

    Heuristics:
      - xelatex: if fontspec detected (modern CL templates)
      - lualatex: if moderncv detected (CV templates)
      - pdflatex: safe fallback
    """
    try:
        content = tex_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return "pdflatex"

    if "fontspec" in content:
        return "xelatex"
    if "moderncv" in content:
        return "lualatex"
    return "pdflatex"


COMPILE_TIMEOUT = int(os.environ.get("DOCUMENT_COMPILE_TIMEOUT", "60"))


async def compile_latex(
    doc_id: int,
    db: AsyncSession,
) -> DocumentCompileResult:
    """Compile a pending Document's LaTeX to PDF.

    Designed to be awaited directly or scheduled as a background task.
    Updates the Document row with status, paths, and log.
    """
    doc = await db.get(Document, doc_id)
    if doc is None:
        raise NotFoundError(f"Document {doc_id} not found")

    # Mark as compiling
    doc.status = "compiling"
    await db.commit()

    try:
        template_path = _resolve_template_path(doc.template_name, doc.document_type)
    except NotFoundError as exc:
        doc.status = "failed"
        doc.compilation_log = str(exc)
        await db.commit()
        return DocumentCompileResult(success=False, log=str(exc))

    output_dir = _build_output_dir(
        doc.job_posting_id or 0, doc.document_type, doc.version
    )
    engine = _select_latex_engine(template_path)
    tex_dest = output_dir / template_path.name

    # Copy template into the output dir so relative includes resolve
    shutil.copy2(template_path, tex_dest)

    # Optional: interpolate variables into a local copy if needed.
    # For now we rely on pre-rendered templates (matching existing workflow).
    cmd = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory",
        str(output_dir),
        str(tex_dest),
    ]

    logger.info("Compiling document %d with %s", doc_id, engine)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(output_dir),
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=COMPILE_TIMEOUT
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            log_output = f"Compilation timed out after {COMPILE_TIMEOUT}s"
            doc.status = "failed"
            doc.compilation_log = log_output
            await db.commit()
            return DocumentCompileResult(success=False, log=log_output)
    except FileNotFoundError:
        log_output = f"LaTeX engine '{engine}' not found on PATH"
        doc.status = "failed"
        doc.compilation_log = log_output
        await db.commit()
        return DocumentCompileResult(success=False, log=log_output)

    log_text = (stdout or b"").decode("utf-8", errors="ignore")
    if stderr:
        log_text += "\n[stderr]\n" + stderr.decode("utf-8", errors="ignore")

    # Locate the produced PDF
    pdf_candidate = tex_dest.with_suffix(".pdf")
    if pdf_candidate.exists() and proc.returncode == 0:
        doc.status = "ready"
        doc.pdf_path = str(pdf_candidate)
        doc.tex_path = str(tex_dest)
        doc.file_size_bytes = pdf_candidate.stat().st_size
        doc.compilation_log = log_text[-4000:] if log_text else None
        await db.commit()
        logger.info(
            "Document %d compiled successfully (%d bytes)",
            doc_id,
            doc.file_size_bytes,
        )
        return DocumentCompileResult(
            success=True,
            pdf_path=str(pdf_candidate),
            log=doc.compilation_log,
            file_size_bytes=doc.file_size_bytes,
        )

    # Non-zero exit or missing PDF → failed
    doc.status = "failed"
    doc.compilation_log = log_text[-4000:] if log_text else "Compilation failed (no output)"
    if pdf_candidate.exists():
        # Partial PDF may exist even on error — remove it
        pdf_candidate.unlink(missing_ok=True)
    await db.commit()
    logger.warning("Document %d compilation failed (exit=%s)", doc_id, proc.returncode)
    return DocumentCompileResult(success=False, log=doc.compilation_log)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


async def get_document(db: AsyncSession, doc_id: int) -> Document | None:
    """Fetch a single document by ID."""
    return await db.get(Document, doc_id)


async def list_document_versions(
    db: AsyncSession, job_posting_id: int, doc_type: DocumentType
) -> list[Document]:
    """Return all versions of a document for a given job, newest first."""
    result = await db.execute(
        select(Document)
        .where(
            Document.job_posting_id == job_posting_id,
            Document.document_type == doc_type,
        )
        .order_by(Document.version.desc())
    )
    return list(result.scalars().all())


async def list_all_documents(
    db: AsyncSession,
    page: int,
    per_page: int,
    status_filter: str | None = None,
    doc_type: str | None = None,
) -> tuple[list[Document], int]:
    """Paginated document listing with optional filters."""
    query = select(Document)
    count_query = select(func.count()).select_from(Document)

    if status_filter:
        query = query.where(Document.status == status_filter)
        count_query = count_query.where(Document.status == status_filter)
    if doc_type:
        query = query.where(Document.document_type == doc_type)
        count_query = count_query.where(Document.document_type == doc_type)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Document.created_at.desc())

    items = (await db.execute(query)).scalars().all()
    total = (await db.execute(count_query)).scalar_one()
    return list(items), total


async def delete_document(db: AsyncSession, doc_id: int) -> bool:
    """Delete a document record and its associated PDF/tex files."""
    doc = await db.get(Document, doc_id)
    if doc is None:
        return False

    # Clean up filesystem artifacts
    for path_str in (doc.pdf_path, doc.tex_path):
        if path_str:
            path = Path(path_str)
            if path.exists():
                path.unlink(missing_ok=True)

    await db.delete(doc)
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# Application-level update helpers
# ---------------------------------------------------------------------------


async def update_application_document_versions(
    db: AsyncSession, application_id: int, cv_version: str | None, cl_version: str | None
) -> None:
    """Stamp the latest CV/CL versions onto an Application record."""
    from app.models.application import Application

    application = await db.get(Application, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")

    if cv_version is not None:
        application.cv_version = cv_version
    if cl_version is not None:
        application.cover_letter_version = cl_version
    await db.commit()
