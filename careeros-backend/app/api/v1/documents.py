"""Document endpoints — CV/CL generation, versioning, preview, download."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.document import Document, DocumentType
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentGenerateResponse,
    DocumentListItem,
    DocumentPreviewResponse,
    DocumentResponse,
    DocumentVersionsList,
)
from app.services import document_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DocumentListItem])
async def list_documents(db: AsyncSession = Depends(get_db)) -> PaginatedResponse[DocumentListItem]:
    """List all documents."""
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).limit(100)
    )
    documents = result.scalars().all()
    items = [
        DocumentListItem(
            id=d.id,
            job_posting_id=d.job_posting_id,
            company_id=d.company_id,
            document_type=d.document_type,
            version=d.version,
            status=d.status,
            file_path=d.pdf_path,
            file_size=d.file_size_bytes,
            created_at=d.created_at.isoformat() if d.created_at else None,
            job_title=None,
            company_name=None,
        )
        for d in documents
    ]
    return PaginatedResponse[DocumentListItem](data=items, meta=PaginationMeta(page=1, per_page=100, total=len(items)))


@router.post(
    "/generate",
    response_model=DocumentGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_document(
    payload: DocumentGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> DocumentGenerateResponse:
    """Generate a CV or cover letter for a specific job posting.

    Returns immediately with a 202 Accepted; LaTeX compilation runs in the
    background. Poll GET /documents/{id} to track status.
    """
    result = await document_service.generate_document(db, payload)
    background_tasks.add_task(document_service.compile_latex, result.id, db)
    return DocumentGenerateResponse(
        id=result.id,
        status=result.status,
        message="Document queued for generation. Poll the document endpoint for status.",
    )


@router.get("/versions", response_model=DocumentVersionsList)
async def list_document_versions(
    job_posting_id: int = Query(..., description="Job posting ID to filter by"),
    document_type: DocumentType = Query(..., description="cv or cover_letter"),
    db: AsyncSession = Depends(get_db),
) -> DocumentVersionsList:
    """List all versions of a document type for a given job posting."""
    docs = await document_service.list_document_versions(db, job_posting_id, document_type)
    versions = [
        {
            "id": d.id,
            "document_type": d.document_type,
            "version": d.version,
            "template_name": d.template_name,
            "status": d.status,
            "pdf_path": d.pdf_path,
            "file_size_bytes": d.file_size_bytes,
            "created_at": d.created_at,
        }
        for d in docs
    ]
    return DocumentVersionsList(
        job_posting_id=job_posting_id,
        document_type=document_type,
        versions=versions,
    )


@router.get("/stats")
async def get_document_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """Return document generation statistics."""
    from sqlalchemy import func, case
    total = await db.execute(select(func.count(Document.id)))
    by_type = await db.execute(
        select(Document.document_type, func.count(Document.id)).group_by(Document.document_type)
    )
    by_week = await db.execute(
        select(
            func.strftime("%Y-%W", Document.created_at).label("week"),
            func.count(Document.id).label("count"),
        ).group_by("week")
    )
    return {
        "total_generated": total.scalar_one(),
        "by_type": {t: c for t, c in by_type.all()},
        "by_week": [{"week": w, "count": c} for w, c in by_week.all() if w],
    }


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Fetch a single document's metadata and current status."""
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return DocumentResponse.model_validate(doc)


@router.get("/{doc_id}/status", response_model=DocumentGenerateResponse)
async def get_document_status(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentGenerateResponse:
    """Lightweight status check for polling."""
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return DocumentGenerateResponse(
        id=doc.id,
        status=doc.status,
        message=f"Document status: {doc.status}",
    )


@router.get("/{doc_id}/preview", response_model=DocumentPreviewResponse)
async def preview_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentPreviewResponse:
    """Return preview/download metadata for a generated document."""
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    return DocumentPreviewResponse(
        document_id=doc.id,
        preview_url=f"/api/v1/documents/{doc.id}/download",
        download_url=f"/api/v1/documents/{doc.id}/download",
        status=doc.status,
    )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download the generated PDF."""
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    if doc.status != "ready" or doc.pdf_path is None:
        raise HTTPException(
            status_code=409,
            detail=f"Document not ready (status: {doc.status}). Retry later.",
        )

    from pathlib import Path

    pdf_path = Path(doc.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing from storage")

    filename = f"{doc.document_type}_v{doc.version}_{doc.template_name}.pdf"
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete a document and its associated files."""
    deleted = await document_service.delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return MessageResponse(message="Document deleted", detail=str(doc_id))
