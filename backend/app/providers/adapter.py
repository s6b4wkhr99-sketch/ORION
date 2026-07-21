"""Volume 15 Section 7 — Default CSV provider adapter (mapping only)."""

import csv
import io
import os
import time
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.mapping.data_dictionary import EXPORT_VALUE_RESOLVERS
from app.providers.export_builder import get_export_headers, resolve_export_value
from app.providers.audit import log_provider_audit
from app.providers.base import ExportContext, ExportResult, ImportContext, ImportValidation, ProviderAdapter
from app.providers.config import PROVIDER_IMPORT_SIGNATURES
from app.providers.export_validation import validate_export
from app.providers.import_validation import validate_import
from app.providers.normalization import build_metric_column_map, normalize_header, normalize_row_metrics
from app.processing.campaign_mapper import build_campaign_column_map


class CSVProviderAdapter(ProviderAdapter):
    """Shared CSV adapter — provider differences live in export_template + config."""

    provider_name = "Generic CSV"

    def generate_export(self, db: Session, ctx: ExportContext) -> ExportResult:
        started = time.perf_counter()
        headers = get_export_headers(db, ctx.provider_name)
        fieldnames = [label for _, label in headers]

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()

        for customer, intel in ctx.rows:
            row_values: dict[str, str] = {}
            for field, label in headers:
                if field == "campaign_id":
                    row_values[label] = ctx.campaign_id
                elif field == "campaign_name":
                    row_values[label] = ctx.campaign_name
                elif field == "ceragem_segment":
                    row_values[label] = intel.ceragem_segment or intel.prizm_proxy_segment or ""
                elif field.startswith("intel_"):
                    intel_field = field.replace("intel_", "")
                    resolver = EXPORT_VALUE_RESOLVERS.get(intel_field)
                    row_values[label] = resolver(customer, intel) if resolver else ""
                else:
                    row_values[label] = resolve_export_value(field, customer, intel)
            writer.writerow(row_values)

        csv_content = buffer.getvalue()
        os.makedirs(settings.upload_dir, exist_ok=True)
        file_name = f"export_{ctx.provider_name.replace(' ', '_').lower()}_{uuid.uuid4().hex[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        file_path = os.path.join(settings.upload_dir, file_name)
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            f.write(csv_content)

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        return ExportResult(
            file_path=file_path,
            file_name=file_name,
            customer_count=len(ctx.rows),
            fieldnames=fieldnames,
            csv_content=csv_content,
            duration_ms=duration_ms,
        )

    def validate_export(self, ctx: ExportContext, csv_content: str, fieldnames: list[str]) -> ImportValidation:
        return validate_export(ctx, csv_content, fieldnames)

    def build_import_column_map(self, headers: list[str]) -> dict[str, str | None]:
        base = build_campaign_column_map(headers)
        metrics = build_metric_column_map(headers)
        base.update(metrics)
        return base

    def normalize_metrics(self, row, column_map: dict[str, str | None]) -> dict:
        return normalize_row_metrics(row, column_map)

    def validate_import(self, ctx: ImportContext) -> ImportValidation:
        return validate_import(ctx)

    def generate_audit_log(self, **kwargs) -> dict:
        return {
            "provider": kwargs.get("provider"),
            "campaignId": kwargs.get("campaign_id"),
            "exportId": kwargs.get("export_id"),
            "importId": kwargs.get("import_id"),
            "userId": kwargs.get("user_id"),
            "customerCount": kwargs.get("customer_count", 0),
            "status": kwargs.get("status", "success"),
            "durationMs": kwargs.get("duration_ms", 0),
            "errors": kwargs.get("errors") or [],
            "warnings": kwargs.get("warnings") or [],
        }

    def detect_import(self, headers: list[str]) -> bool:
        normalized = {normalize_header(h) for h in headers}
        signature = PROVIDER_IMPORT_SIGNATURES.get(self.provider_name, set())
        if not signature:
            return False
        return len(normalized & signature) >= max(1, len(signature) // 2)


def _adapter_class(name: str) -> type[CSVProviderAdapter]:
    return type(f"{name.replace(' ', '')}Adapter", (CSVProviderAdapter,), {"provider_name": name})


ADAPTER_CLASSES: dict[str, type[CSVProviderAdapter]] = {
    name: _adapter_class(name) for name in (
        "Generic CSV",
        "Klaviyo",
        "Mailchimp",
        "HubSpot",
        "Attentive",
        "Salesforce Marketing Cloud",
    )
}
