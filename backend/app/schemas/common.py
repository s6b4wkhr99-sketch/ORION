"""Volume 08 Rule 003 — Shared request/response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None


class PaginatedRows(BaseModel):
    total: int
    page: int
    limit: int
    rows: list[Any]
