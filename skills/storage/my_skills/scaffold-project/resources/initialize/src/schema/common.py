"""
Common reusable schemas and generic data contracts.
"""

from __future__ import annotations

from typing import Generic, TypeVar, Sequence, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class StatusResponse(BaseModel):
    """Standard operation acknowledgement."""
    status: str = "ok"
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic envelope for paginated collections."""
    items: Sequence[T]
    total: int = Field(ge=0, description="Total number of items across all pages")
    page: int = Field(ge=1, default=1, description="Current page number (1-indexed)")
    page_size: int = Field(ge=1, default=50, description="Number of items per page")
    total_pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[T]:
        """Convenience constructor to calculate total_pages automatically."""
        import math
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
