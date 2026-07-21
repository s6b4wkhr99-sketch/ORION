"""Volume 11 Section 15 — File security extensions."""

import re

from app.rules.upload import (
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    UploadRuleError,
    validate_file_size,
    validate_file_type,
)

ALLOWED_MIME_TYPES = {
    "csv": {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel", "application/octet-stream"},
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
    "xls": {"application/vnd.ms-excel", "application/octet-stream"},
}

FILENAME_PATTERN = re.compile(r"^[\w\s.\-()]+\.(csv|xlsx|xls)$", re.I)


def validate_filename(filename: str | None) -> None:
    if not filename or not FILENAME_PATTERN.match(filename.strip()):
        raise UploadRuleError("RULE-UP-001", "Invalid or unsafe filename")


def validate_mime_type(filename: str | None, content_type: str | None) -> None:
    if not filename:
        return
    ext = filename.lower().rsplit(".", 1)[-1]
    allowed = ALLOWED_MIME_TYPES.get(ext, set())
    if content_type and content_type.split(";")[0].strip().lower() not in allowed:
        raise UploadRuleError("RULE-UP-001", f"MIME type {content_type} not allowed for .{ext}")


def validate_upload_file(filename: str | None, content: bytes, content_type: str | None = None) -> None:
    validate_filename(filename)
    validate_file_type(filename)
    validate_file_size(content)
    validate_mime_type(filename, content_type)
