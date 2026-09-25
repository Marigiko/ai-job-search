"""Company CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services import company_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    name: str | None = Query(None),
    industry: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CompanyResponse]:
    """List companies with optional name/industry filters and pagination."""
    result = await company_service.list_companies(db, page, per_page, name, industry)
    return PaginatedResponse[CompanyResponse](
        data=[CompanyResponse.model_validate(c) for c in result.items],
        meta=PaginationMeta(page=page, per_page=per_page, total=result.total),
    )


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    """Create a new company."""
    company = await company_service.create_company(db, payload)
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    """Retrieve a single company by ID."""
    company = await company_service.get_company(db, company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return CompanyResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    """Partially update a company."""
    company = await company_service.update_company(db, company_id, payload)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return CompanyResponse.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a company and its job postings (cascade)."""
    deleted = await company_service.delete_company(db, company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
