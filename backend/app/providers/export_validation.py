"""Volume 15 Section 14 — Export validation."""

import csv
import io

from app.providers.config import PROVIDER_EXPORT_REQUIRED, SUPPORTED_PROVIDERS
from app.providers.base import ExportContext, ImportValidation


class ExportValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_export(ctx: ExportContext, csv_content: str, fieldnames: list[str]) -> ImportValidation:
    errors: list[str] = []
    warnings: list[str] = []

    if ctx.provider_name not in SUPPORTED_PROVIDERS:
        errors.append(f"Unsupported provider: {ctx.provider_name}")

    if len(ctx.rows) == 0:
        errors.append("Customer count is zero")

    if not fieldnames:
        errors.append("CSV header is required")

    try:
        csv_content.encode("utf-8")
    except UnicodeEncodeError:
        errors.append("Encoding error — UTF-8 required")

    if not ctx.campaign_id:
        errors.append("Campaign ID is required")

    reader = csv.DictReader(io.StringIO(csv_content))
    emails: list[str] = []
    for row in reader:
        email = None
        for key in row:
            if key and "email" in key.lower():
                email = (row.get(key) or "").strip().lower()
                break
        if not email:
            errors.append("Missing email in export row")
            break
        if email in emails:
            errors.append("Duplicate email in export")
            break
        emails.append(email)

    required_internal = PROVIDER_EXPORT_REQUIRED.get(ctx.provider_name, ["email_address"])
    label_checks = {
        "email_address": lambda labels: any("email" in l.lower() for l in labels),
        "campaign_id": lambda labels: any("campaign" in l.lower() and "id" in l.lower() for l in labels),
        "recommended_product": lambda labels: any("product" in l.lower() or "recommended" in l.lower() for l in labels),
        "message_direction": lambda labels: any("message" in l.lower() or "direction" in l.lower() for l in labels),
        "campaign_name": lambda labels: any("campaign" in l.lower() and "name" in l.lower() for l in labels),
    }
    for req in required_internal:
        checker = label_checks.get(req)
        if checker and not checker(fieldnames):
            warnings.append(f"Recommended export column for {req} may be missing")

    return ImportValidation(is_valid=len(errors) == 0, errors=errors, warnings=warnings, provider=ctx.provider_name)
