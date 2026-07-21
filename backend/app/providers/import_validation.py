"""Volume 15 Section 15 — Import validation."""

import re

import pandas as pd

from app.providers.base import ImportContext, ImportValidation
from app.providers.config import PROVIDER_IMPORT_METRICS, SUPPORTED_PROVIDERS
from app.processing.campaign_mapper import validate_campaign_column_map


class ImportValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _valid_revenue(value) -> bool:
    if value is None or str(value).strip() == "":
        return True
    text = str(value).replace(",", "").replace("$", "").strip()
    try:
        float(text)
        return True
    except ValueError:
        return False


def validate_import(ctx: ImportContext) -> ImportValidation:
    errors: list[str] = []
    warnings: list[str] = []
    df = ctx.dataframe

    if ctx.provider_name not in SUPPORTED_PROVIDERS:
        errors.append(f"Unknown provider: {ctx.provider_name}")

    base = validate_campaign_column_map(ctx.column_map)
    if not base["is_valid"]:
        errors.extend(base["missing_required"])

    campaign_id_col = ctx.column_map.get("campaign_id")
    campaign_name_col = ctx.column_map.get("campaign_name")
    if not campaign_id_col and not campaign_name_col:
        errors.append("Invalid campaign — campaign_id or campaign_name required")

    if len(df) == 0:
        errors.append("Invalid file — no data rows")

    required_metrics = PROVIDER_IMPORT_METRICS.get(ctx.provider_name, [])
    for metric in required_metrics:
        if metric in ("total_sent", "opened", "clicked", "delivered", "actual_revenue") and not ctx.column_map.get(metric):
            if metric == "total_sent" and ctx.column_map.get("delivered"):
                continue
            warnings.append(f"Missing recommended metric column: {metric}")

    if df.duplicated().any().any():
        warnings.append("Duplicate rows detected")

    revenue_col = ctx.column_map.get("actual_revenue")
    if revenue_col:
        for val in df[revenue_col].head(50):
            if not _valid_revenue(val):
                errors.append("Revenue format invalid")
                break

    date_cols = [c for c in df.columns if re.search(r"date", str(c), re.I)]
    for col in date_cols[:1]:
        sample = df[col].dropna().head(5)
        for val in sample:
            if str(val).strip() and not re.match(r"[\d\-/T: ]+", str(val)):
                warnings.append(f"Date format may be invalid in column {col}")
                break

    return ImportValidation(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        provider=ctx.provider_name,
        mapped_columns={k: v for k, v in ctx.column_map.items() if v},
    )
