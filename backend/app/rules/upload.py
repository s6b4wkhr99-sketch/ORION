"""Volume 10 Section 4 — Upload business rules."""

from app.rules.library import get_rule

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # RULE-UP-002: 100 MB
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}


class UploadRuleError(Exception):
    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        super().__init__(message)


def validate_file_type(filename: str | None) -> None:
    """RULE-UP-001 — Accepted Upload File Types."""
    rule = get_rule("RULE-UP-001")
    if not filename:
        raise UploadRuleError(rule.rule_id if rule else "RULE-UP-001", "File name is required")
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadRuleError(
            "RULE-UP-001",
            "Only CSV and XLSX files are supported",
        )


def validate_file_size(content: bytes) -> None:
    """RULE-UP-002 — Upload Size Validation."""
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadRuleError(
            "RULE-UP-002",
            f"File exceeds maximum upload size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )


def validate_upload_file(filename: str | None, content: bytes) -> None:
    validate_file_type(filename)
    validate_file_size(content)
