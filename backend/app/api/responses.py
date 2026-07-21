"""Volume 07 Section 12 — Standard API response envelope."""

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def success(data: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": True, "data": data})


def failure(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": False, "message": message})


def ok(data: Any = None) -> dict:
    """Return dict for FastAPI auto JSON (when not using JSONResponse)."""
    return {"success": True, "data": data}


def err(message: str) -> None:
    raise HTTPException(status_code=400, detail={"success": False, "message": message})
