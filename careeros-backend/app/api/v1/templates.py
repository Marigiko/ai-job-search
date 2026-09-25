"""Email template CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.template import (
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
)
from app.services import template_service

router = APIRouter()


@router.get("", response_model=list[EmailTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[EmailTemplateResponse]:
    """List all email templates."""
    templates = await template_service.list_templates(db)
    return [EmailTemplateResponse.model_validate(t) for t in templates]


@router.post("", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> EmailTemplateResponse:
    """Create a new email template."""
    template = await template_service.create_template(db, payload)
    return EmailTemplateResponse.model_validate(template)


@router.patch("/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: int,
    payload: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> EmailTemplateResponse:
    """Partially update an email template."""
    template = await template_service.update_template(db, template_id, payload)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return EmailTemplateResponse.model_validate(template)
