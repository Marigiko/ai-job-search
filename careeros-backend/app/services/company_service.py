"""Company CRUD service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


@dataclass
class PaginatedResult:
    items: list[Company]
    total: int


async def list_companies(
    db: AsyncSession,
    page: int,
    per_page: int,
    name: str | None = None,
    industry: str | None = None,
) -> PaginatedResult:
    """Query companies with optional filters and pagination."""
    query = select(Company)
    count_query = select(func.count()).select_from(Company)

    if name:
        query = query.where(Company.name.ilike(f"%{name}%"))
        count_query = count_query.where(Company.name.ilike(f"%{name}%"))
    if industry:
        query = query.where(Company.industry.ilike(f"%{industry}%"))
        count_query = count_query.where(Company.industry.ilike(f"%{industry}%"))

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Company.name)

    items = (await db.execute(query)).scalars().all()
    total = (await db.execute(count_query)).scalar_one()
    return PaginatedResult(items=list(items), total=total)


async def create_company(db: AsyncSession, payload: CompanyCreate) -> Company:
    """Create a new company."""
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def get_company(db: AsyncSession, company_id: int) -> Company | None:
    """Fetch a company by ID, or None if not found."""
    return await db.get(Company, company_id)


async def update_company(
    db: AsyncSession, company_id: int, payload: CompanyUpdate
) -> Company | None:
    """Update an existing company, returning None if not found."""
    company = await db.get(Company, company_id)
    if company is None:
        return None

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, key, value)

    await db.commit()
    await db.refresh(company)
    return company


async def delete_company(db: AsyncSession, company_id: int) -> bool:
    """Delete a company. Returns True if deleted."""
    company = await db.get(Company, company_id)
    if company is None:
        return False
    await db.delete(company)
    await db.commit()
    return True
