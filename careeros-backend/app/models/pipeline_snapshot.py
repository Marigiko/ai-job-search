"""PipelineSnapshot entity — point-in-time pipeline metrics."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import JSON, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PipelineSnapshot(Base):
    __tablename__ = "pipeline_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    stage_counts: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    conversion_rates: Mapped[dict[str, float] | None] = mapped_column(JSON)
