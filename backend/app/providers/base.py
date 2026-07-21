"""Volume 15 Section 7 — Provider adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.customer import Customer, CustomerIntelligence


@dataclass
class ExportContext:
    provider_name: str
    campaign_id: str
    campaign_name: str
    rows: list[tuple[Customer, CustomerIntelligence]]
    state_filter: str | None = None
    zip_filter: str | None = None
    segment_filter: str | None = None
    product_filter: str | None = None


@dataclass
class ExportResult:
    file_path: str
    file_name: str
    customer_count: int
    fieldnames: list[str]
    csv_content: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class ImportContext:
    provider_name: str
    file_name: str
    file_path: str
    dataframe: pd.DataFrame
    column_map: dict[str, str | None]
    user_id: str | None = None


@dataclass
class ImportValidation:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provider: str | None = None
    mapped_columns: dict[str, str | None] = field(default_factory=dict)


class ProviderAdapter(ABC):
    """Mapping-only adapter — no intelligence or campaign business rules."""

    provider_name: str

    @abstractmethod
    def generate_export(self, db: Session, ctx: ExportContext) -> ExportResult:
        ...

    @abstractmethod
    def validate_export(self, ctx: ExportContext, csv_content: str, fieldnames: list[str]) -> ImportValidation:
        ...

    @abstractmethod
    def build_import_column_map(self, headers: list[str]) -> dict[str, str | None]:
        ...

    @abstractmethod
    def normalize_metrics(self, row: pd.Series, column_map: dict[str, str | None]) -> dict[str, Any]:
        ...

    @abstractmethod
    def validate_import(self, ctx: ImportContext) -> ImportValidation:
        ...

    @abstractmethod
    def generate_audit_log(
        self,
        *,
        action: str,
        provider: str,
        campaign_id: str | None,
        export_id: str | None,
        import_id: str | None,
        user_id: str | None,
        customer_count: int,
        status: str,
        duration_ms: float,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> dict:
        ...

    def detect_import(self, headers: list[str]) -> bool:
        return False
