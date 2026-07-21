"""Bulk ZIP median income import from ACS 5-Year Summary File (Table B19013)."""

from __future__ import annotations

import csv
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.geo.datacommons_client import fetch_zip_median_incomes
from app.geo.zip_economics import INCOME_SOURCE_LABEL, PREMIUM_INCOME_THRESHOLD
from app.models.reference_data import ZipMaster
from app.models.zip import ZipIntelligence

logger = logging.getLogger("cios.geo")

ACS_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "acs"
INCOME_FILE = ACS_DATA_DIR / "acsdt5y2022-b19013.dat"
GEO_FILE = ACS_DATA_DIR / "acs2022_5yr_geography.dat"
ZCTA_GEO_PREFIX = "860Z200US"
INVALID_INCOME = {-666666666, -222222222, -333333333}
TOP50_COUNT = 50


def _normalize_zip(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(c for c in str(value).strip() if c.isdigit())
    if len(digits) >= 5:
        return digits[:5]
    return None


def _parse_income(value: str | None) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        income = int(float(value))
    except (TypeError, ValueError):
        return None
    if income in INVALID_INCOME or income <= 0:
        return None
    return float(income)


def load_zcta_income(
    income_path: Path = INCOME_FILE,
    geo_path: Path = GEO_FILE,
) -> dict[str, float]:
    """Return {zip5: median_household_income} from ACS B19013 ZCTA rows."""
    if not income_path.exists():
        raise FileNotFoundError(f"ACS income file not found: {income_path}")

    incomes: dict[str, float] = {}
    with income_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="|")
        for row in reader:
            geo_id = (row.get("GEO_ID") or "").strip()
            if not geo_id.startswith(ZCTA_GEO_PREFIX):
                continue
            zip_code = geo_id[len(ZCTA_GEO_PREFIX) :]
            if not re.fullmatch(r"\d{5}", zip_code):
                continue
            income = _parse_income(row.get("B19013_E001"))
            if income is not None:
                incomes[zip_code] = income

    if not incomes and geo_path.exists():
        logger.warning("No ZCTA rows in income file; geography fallback not required for B19013.")

    return incomes


def compute_premium_zips(incomes: dict[str, float]) -> set[str]:
    """Top 50 national ZCTAs plus ZIPs above the premium income threshold."""
    ranked = sorted(incomes.items(), key=lambda item: item[1], reverse=True)
    top50 = {zip_code for zip_code, _ in ranked[:TOP50_COUNT]}
    for zip_code, income in incomes.items():
        if income >= PREMIUM_INCOME_THRESHOLD:
            top50.add(zip_code)
    return top50


def _customer_zip_states(db: Session, zips: set[str]) -> dict[str, str]:
    from app.models.customer import Customer

    rows = (
        db.query(Customer.zip, Customer.state)
        .filter(Customer.zip.in_(list(zips)))
        .filter(Customer.state.isnot(None))
        .all()
    )
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for zip_code, state in rows:
        normalized = _normalize_zip(zip_code)
        if not normalized or not state:
            continue
        counts[normalized][str(state).strip().upper()] += 1
    return {zip_code: counter.most_common(1)[0][0] for zip_code, counter in counts.items()}


def collect_target_zips(db: Session, *, all_customer_zips: bool = True, extra_zips: set[str] | None = None) -> set[str]:
    from app.models.customer import Customer

    targets: set[str] = set(extra_zips or set())
    if all_customer_zips:
        rows = db.query(Customer.zip).filter(Customer.zip.isnot(None), Customer.zip != "").distinct().all()
        for (zip_code,) in rows:
            normalized = _normalize_zip(zip_code)
            if normalized:
                targets.add(normalized)
    return targets


def _fill_missing_incomes_from_datacommons(
    incomes: dict[str, float],
    missing_zips: set[str],
    *,
    api_key: str | None = None,
    enabled: bool | None = None,
) -> tuple[dict[str, float], dict[str, int | str]]:
    """Supplement ACS bulk gaps using Data Commons Observation API."""
    key = (api_key if api_key is not None else settings.datacommons_api_key).strip()
    use_fallback = settings.datacommons_zip_income_fallback if enabled is None else enabled
    stats: dict[str, int | str] = {
        "datacommons_requested": len(missing_zips),
        "datacommons_filled": 0,
        "datacommons_still_missing": 0,
    }

    if not missing_zips or not use_fallback:
        stats["datacommons_still_missing"] = len(missing_zips)
        return incomes, stats
    if not key:
        logger.warning(
            "Skipping Data Commons ZIP income fallback for %s ZIPs (DATACOMMONS_API_KEY not set)",
            len(missing_zips),
        )
        stats["datacommons_still_missing"] = len(missing_zips)
        return incomes, stats

    try:
        fetched = fetch_zip_median_incomes(missing_zips, api_key=key)
    except Exception:
        logger.exception("Data Commons ZIP income fallback failed")
        stats["datacommons_still_missing"] = len(missing_zips)
        return incomes, stats

    merged = dict(incomes)
    filled = 0
    for zip_code, income in fetched.items():
        if zip_code in missing_zips and income is not None:
            merged[zip_code] = income
            filled += 1

    stats["datacommons_filled"] = filled
    stats["datacommons_still_missing"] = len(missing_zips) - filled
    return merged, stats


def import_zip_income(
    db: Session,
    *,
    target_zips: set[str] | None = None,
    income_path: Path = INCOME_FILE,
    geo_path: Path = GEO_FILE,
    source_version: str = "ACS-B19013-unitedstateszipcodes",
    use_datacommons_fallback: bool | None = None,
    datacommons_api_key: str | None = None,
) -> dict[str, int | str]:
    """
    Upsert zip_intelligence and zip_master for target ZIPs using ACS median income.
    ZIPs missing from the local ACS bulk file are optionally filled via Data Commons.
    Existing rows are updated in place (no destructive overwrite of unrelated ZIPs).
    """
    incomes = load_zcta_income(income_path=income_path, geo_path=geo_path)
    acs_row_count = len(incomes)

    if target_zips is None:
        target_zips = collect_target_zips(db)

    missing_zips = {zip_code for zip_code in target_zips if zip_code not in incomes}
    incomes, datacommons_stats = _fill_missing_incomes_from_datacommons(
        incomes,
        missing_zips,
        api_key=datacommons_api_key,
        enabled=use_datacommons_fallback,
    )
    if int(datacommons_stats.get("datacommons_filled", 0)) > 0:
        source_version = f"{source_version}+DataCommons"

    premium_zips = compute_premium_zips(incomes)
    zip_states = _customer_zip_states(db, target_zips)

    stats: dict[str, int | str] = {
        "source_version": source_version,
        "income_reference": INCOME_SOURCE_LABEL,
        "acs_zcta_rows": acs_row_count,
        "target_zips": len(target_zips),
        "matched": 0,
        "inserted": 0,
        "updated": 0,
        "missing_in_acs": 0,
        "premium_zips": 0,
        **datacommons_stats,
    }

    for zip_code in sorted(target_zips):
        income = incomes.get(zip_code)
        if income is None:
            stats["missing_in_acs"] = int(stats["missing_in_acs"]) + 1
            continue

        state = zip_states.get(zip_code, "US")
        top50 = zip_code in premium_zips
        if top50:
            stats["premium_zips"] = int(stats["premium_zips"]) + 1

        existing = db.query(ZipIntelligence).filter(ZipIntelligence.zip == zip_code).first()
        if existing:
            existing.median_income = income
            existing.state = state
            existing.top50_rank = top50
            stats["updated"] = int(stats["updated"]) + 1
        else:
            db.add(
                ZipIntelligence(
                    zip=zip_code,
                    state=state,
                    median_income=income,
                    top50_rank=top50,
                )
            )
            stats["inserted"] = int(stats["inserted"]) + 1

        master = db.query(ZipMaster).filter(ZipMaster.zip_code == zip_code).first()
        if master:
            master.median_income = income
            master.state_code = state
            master.top_income_indicator = top50
        else:
            db.add(
                ZipMaster(
                    zip_code=zip_code,
                    state_code=state,
                    median_income=income,
                    top_income_indicator=top50,
                )
            )

        stats["matched"] = int(stats["matched"]) + 1

    db.commit()
    logger.info("ZIP income import complete: %s", stats)
    return stats
