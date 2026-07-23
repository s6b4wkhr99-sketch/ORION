"""Volume 28.1 Phase B — in-memory dashboard response cache."""

from __future__ import annotations

import hashlib
import json
import os
import time
from threading import Event, Lock

from app.config import settings

# Bump after promo policy / coverage logic changes so all dashboard namespaces rebuild.
DASHBOARD_BUILD_VERSION = "2026-07-conservative-promo-reach-v4"

_CACHE: dict[str, tuple[float, dict]] = {}
_LOCK = Lock()
_BUILD_WAITERS: dict[str, Event] = {}
_GEN_FILENAME = ".dashboard_cache_gen"
_DISK_CACHE_DIR = "dashboard_cache"
_INVALIDATION_HOOKS: list[callable] = []


def register_dashboard_cache_hook(callback: callable) -> None:
    _INVALIDATION_HOOKS.append(callback)


def dashboard_cache_generation() -> str:
    return _cache_generation()


def _generation_path() -> str:
    return os.path.join(settings.upload_dir, _GEN_FILENAME)


def _disk_cache_dir() -> str:
    path = os.path.join(settings.upload_dir, _DISK_CACHE_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def _disk_cache_path(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return os.path.join(_disk_cache_dir(), f"{digest}.json")


def _cache_generation() -> str:
    path = _generation_path()
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read().strip() or "0"
    except OSError:
        return "0"


def _ttl_seconds() -> int:
    return max(60, int(settings.dashboard_cache_ttl_minutes) * 60)


def cache_get(key: str) -> dict | None:
    with _LOCK:
        entry = _CACHE.get(key)
        if not entry:
            return None
        expires_at, payload = entry
        if time.time() > expires_at:
            _CACHE.pop(key, None)
            return None
        return payload


def cache_set(key: str, payload: dict) -> None:
    with _LOCK:
        _CACHE[key] = (time.time() + _ttl_seconds(), payload)


def _disk_cache_get(key: str) -> dict | None:
    path = _disk_cache_path(key)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return None
        saved_at = float(data.get("_cached_at") or 0)
        if saved_at <= 0 or time.time() - saved_at > _ttl_seconds():
            return None
        payload = data.get("payload")
        return payload if isinstance(payload, dict) else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _disk_cache_set(key: str, payload: dict) -> None:
    path = _disk_cache_path(key)
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"_cached_at": time.time(), "payload": payload}, handle)
    except OSError:
        pass


def invalidate_dashboard_cache() -> None:
    """Bump shared generation so API + worker processes drop stale dashboard payloads."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(_generation_path(), "w", encoding="utf-8") as handle:
        handle.write(str(time.time()))
    with _LOCK:
        _CACHE.clear()
    for hook in _INVALIDATION_HOOKS:
        try:
            hook()
        except Exception:
            pass


def _cache_hit_payload(key: str) -> dict | None:
    hit = cache_get(key)
    if hit is None:
        hit = _disk_cache_get(key)
        if hit is not None:
            cache_set(key, hit)
    if hit is None:
        return None
    cached = dict(hit)
    cached["cache_hit"] = True
    return cached


def cached_dashboard(namespace: str, scope: str, builder) -> dict:
    if not settings.dashboard_cache_enabled:
        return builder()
    key = f"{DASHBOARD_BUILD_VERSION}:{_cache_generation()}:{namespace}:{scope}"
    hit = _cache_hit_payload(key)
    if hit is not None:
        return hit

    waiter: Event | None = None
    is_builder = False
    with _LOCK:
        existing = _BUILD_WAITERS.get(key)
        if existing is None:
            waiter = Event()
            _BUILD_WAITERS[key] = waiter
            is_builder = True
        else:
            waiter = existing

    if not is_builder and waiter is not None:
        waiter.wait(timeout=600)
        hit = _cache_hit_payload(key)
        if hit is not None:
            return hit

    try:
        payload = builder()
        cache_set(key, payload)
        _disk_cache_set(key, payload)
        result = dict(payload)
        result["cache_hit"] = False
        return result
    finally:
        if is_builder:
            with _LOCK:
                done = _BUILD_WAITERS.pop(key, None)
            if done is not None:
                done.set()
