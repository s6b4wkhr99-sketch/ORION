"""
Geographic market signals for Pain Index, Brand Familiarity, and Digital Engagement.

Hypotheses encoded:
- Dense metros: chiropractor access per capita is strained → appointment/wait friction raises Pain Index.
- Korean/Chinese enclave ZIPs: elevated Ceragem brand familiarity from Asia market exposure.
- Top-50 metros (e.g. NYC vs upstate NY): higher online shopping comfort → Digital Engagement boost.
"""

from __future__ import annotations

import re

from app.geo.brand_familiarity_geo import (
    US_ASIAN_ALONE_BASELINE_PCT,
    asian_city_signals,
    korean_metro_signals,
    korean_state_signals,
)
from app.reference.chronic_pain_geo import chronic_pain_city_boost, state_chronic_pain_score, state_chronic_pain_tier

GEO_SIGNAL_VERSION = "2026.07-geo-market-v5"

# ACS 2022 Korean state population rank (United Koreans / Census TOP 10).
# PA is excluded — not in top-10 Korean states; Philadelphia uses metro tier-3 only.
STATE_BRAND_AFFINITY: dict[str, float] = {
    "CA": 0.12,
    "NY": 0.11,
    "TX": 0.10,
    "NJ": 0.09,
    "WA": 0.08,
    "VA": 0.08,
    "GA": 0.07,
    "IL": 0.07,
    "MD": 0.06,
    "HI": 0.06,
}

# Tier-1 digital/commerce metros (highest online order frequency proxy).
TIER1_METRO_ZIPS: frozenset[str] = frozenset(
    {
        "10001", "10002", "10003", "10011", "10012", "10013", "10016", "10017", "10018", "10019",
        "10021", "10022", "10023", "10024", "10025", "10028", "10036", "10038", "10065", "10128",
        "11201", "11211", "11215", "11217", "11222", "11231", "11354", "11355", "11375",
        "07024", "07030", "07302", "07310",
        "90001", "90004", "90005", "90006", "90010", "90012", "90017", "90019", "90024", "90025",
        "90028", "90034", "90035", "90036", "90046", "90048", "90064", "90066", "90210", "90211",
        "94102", "94103", "94107", "94109", "94110", "94114", "94115", "94118",
        "60601", "60602", "60605", "60606", "60607", "60610", "60611", "60614", "60654",
        "02108", "02109", "02110", "02116", "02134", "02139", "02210",
        "20001", "20002", "20005", "20007", "20009", "20036",
        "33109", "33130", "33131", "33132", "33139", "33140",
        "75201", "75202", "75204", "75205", "75219", "75225",
        "77002", "77005", "77006", "77007", "77019", "77024", "77056",
        "98101", "98102", "98103", "98104", "98109", "98112",
        "30303", "30305", "30306", "30308", "30309", "30318", "30324",
        "19102", "19103", "19106", "19107", "19063",
    }
)

# Tier-2 major metros (top-50 MSA proxy subset).
TIER2_METRO_STATE_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("TX", "AUSTIN"), ("TX", "DALLAS"), ("TX", "HOUSTON"), ("TX", "SAN ANTONIO"),
        ("CA", "SAN DIEGO"), ("CA", "SAN JOSE"), ("CA", "OAKLAND"), ("CA", "SACRAMENTO"),
        ("AZ", "PHOENIX"), ("AZ", "SCOTTSDALE"), ("AZ", "TEMPE"),
        ("CO", "DENVER"), ("NV", "LAS VEGAS"), ("NV", "HENDERSON"),
        ("FL", "MIAMI"), ("FL", "ORLANDO"), ("FL", "TAMPA"), ("FL", "JACKSONVILLE"),
        ("NC", "CHARLOTTE"), ("NC", "RALEIGH"), ("TN", "NASHVILLE"),
        ("OH", "COLUMBUS"), ("OH", "CLEVELAND"), ("MI", "DETROIT"),
        ("MN", "MINNEAPOLIS"), ("MO", "KANSAS CITY"), ("MO", "ST LOUIS"),
        ("WI", "MILWAUKEE"), ("IN", "INDIANAPOLIS"), ("PA", "PITTSBURGH"),
        ("VA", "ARLINGTON"), ("VA", "ALEXANDRIA"), ("MD", "BALTIMORE"),
        ("OR", "PORTLAND"), ("WA", "SEATTLE"), ("UT", "SALT LAKE CITY"),
    }
)

# Korean / broader Asian-brand familiarity enclaves (Ceragem Asia exposure proxy).
BRAND_ENCLAVE_ZIPS: frozenset[str] = frozenset(
    {
        "90004", "90005", "90006", "90019", "90638", "92821",
        "11354", "11355", "11358", "11362", "11364",
        "07024", "07650", "07660", "07631",
        "30096", "30024", "30340",
        "75006", "75035", "75038", "75062", "75070", "75248", "76063", "76244",
        "60016", "60056", "60074", "60090",
        "98030", "98032", "98052",
        "22102", "22003", "22304",
        "94538", "94539", "95014", "95035",
        "97229", "97230",
        "77036", "77072", "77083", "77084", "77494", "77449", "77429", "77433",
        "19106", "19107", "19116", "19120", "19020", "19067", "19335", "19380",
    }
)

# ZIP prefixes for high-growth Asian corridors in TX (DFW/Houston/Katy) and PA (Philadelphia metro).
BRAND_ENCLAVE_ZIP_PREFIXES: frozenset[str] = frozenset(
    {
        "7703", "7707", "7708", "7709",
        "7506", "7501", "7503", "7507", "7524", "7525", "7606", "7624",
        "7749", "7745", "7742", "7743",
        "1910", "1911", "1912",
        "1901", "1902", "1903", "1932", "1933", "1938",
    }
)

BRAND_ENCLAVE_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("CA", "KOREATOWN"), ("CA", "IRVINE"), ("CA", "FULLERTON"),
        ("NY", "FLUSHING"), ("NY", "BAYSIDE"), ("NJ", "PALISADES PARK"), ("NJ", "FORT LEE"),
        ("NJ", "RIDGEFIELD"), ("NJ", "LEONIA"), ("GA", "DULUTH"), ("GA", "SUWANEE"),
        ("TX", "CARROLLTON"), ("TX", "IRVING"), ("TX", "PLANO"),
        ("IL", "NAPERVILLE"), ("IL", "SCHAUMBURG"), ("WA", "FEDERAL WAY"),
        ("VA", "ANNANDALE"), ("VA", "CENTREVILLE"),
    }
)

# TX — Korean corporate/expat corridor (DFW, Houston, Austin suburbs).
KOREAN_CORRIDOR_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("TX", "PLANO"), ("TX", "IRVING"), ("TX", "CARROLLTON"), ("TX", "RICHARDSON"),
        ("TX", "FRISCO"), ("TX", "MCKINNEY"), ("TX", "KATY"), ("TX", "SPRING"),
        ("TX", "CYPRESS"), ("TX", "SUGAR LAND"), ("TX", "LEWISVILLE"), ("TX", "GARLAND"),
        ("TX", "HOUSTON"), ("TX", "DALLAS"), ("TX", "ARLINGTON"), ("TX", "ROUND ROCK"),
        ("TX", "STAFFORD"), ("TX", "MISSOURI CITY"), ("TX", "PEARLAND"), ("TX", "ALLEN"),
    }
)

# PA — Chinese American population concentration (Philadelphia metro, Pittsburgh).
CHINESE_CORRIDOR_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("PA", "PHILADELPHIA"), ("PA", "PITTSBURGH"), ("PA", "NORRISTOWN"),
        ("PA", "ALLENTOWN"), ("PA", "BETHLEHEM"), ("PA", "EASTON"), ("PA", "LANCASTER"),
        ("PA", "HARRISBURG"), ("PA", "YORK"), ("PA", "READING"), ("PA", "LEVITTOWN"),
    }
)

# Innerbody 2026 — top sleep-deprived U.S. cities (CDC BRFSS + PLACES proxy).
# Source: https://www.innerbody.com/most-sleep-deprived-cities
SLEEP_DEPRIVED_TIER1_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("VA", "NORFOLK"),
        ("LA", "NEW ORLEANS"),
        ("MI", "DETROIT"),
        ("OH", "TOLEDO"),
        ("OH", "CINCINNATI"),
        ("IN", "INDIANAPOLIS"),
        ("PA", "PHILADELPHIA"),
        ("TX", "LAREDO"),
        ("OH", "CLEVELAND"),
        ("TN", "MEMPHIS"),
    }
)

SLEEP_DEPRIVED_TIER2_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("TX", "CORPUS CHRISTI"),
        ("OH", "COLUMBUS"),
        ("NV", "LAS VEGAS"),
        ("NV", "NORTH LAS VEGAS"),
        ("TX", "SAN ANTONIO"),
        ("HI", "HONOLULU"),
    }
)

ZIP_PATTERN = re.compile(r"^\d{5}$")


def _normalize_zip(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(c for c in str(value).strip() if c.isdigit())
    if len(digits) >= 5:
        zip_code = digits[:5]
        return zip_code if ZIP_PATTERN.fullmatch(zip_code) else None
    return None


def _normalize_city(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9 ]", "", (value or "").upper()).strip()


def _normalize_state(value: str | None) -> str:
    return (value or "").strip().upper()[:2]


def _population_density_tier(population: int | None) -> str:
    if population is None or population <= 0:
        return "unknown"
    if population >= 50_000:
        return "very_dense"
    if population >= 25_000:
        return "dense"
    if population >= 8_000:
        return "suburban"
    return "rural"


def metro_tier(
    *,
    zip_code: str | None,
    state: str | None,
    city: str | None,
) -> str:
    zip5 = _normalize_zip(zip_code)
    state_code = _normalize_state(state)
    city_key = _normalize_city(city)
    if zip5 and zip5 in TIER1_METRO_ZIPS:
        return "tier1"
    if (state_code, city_key) in TIER2_METRO_STATE_CITIES:
        return "tier2"
    if zip5 and zip5[:3] in {"100", "101", "102", "112", "900", "901", "902", "941", "606", "021", "200", "331"}:
        return "tier2"
    return "other"


def pain_geo_boost(
    *,
    zip_code: str | None,
    state: str | None,
    city: str | None,
    population: int | None,
) -> dict[str, float | str]:
    """
    Pain Index geographic modifier.

    Layers:
    1. Chronic / back-pain city & state signals (Novaalab, Felician, April ABA anchors)
    2. Dense metros: appointment / wait friction for chiropractic care
    3. Rural/low population: distance/access friction per capita provider access
    """
    chronic = chronic_pain_city_boost(state=state, city=city)
    tier = metro_tier(zip_code=zip_code, state=state, city=city)
    density = _population_density_tier(population)
    boost = float(chronic.get("chronic_pain_geo_boost") or 0.0)
    reasons: list[str] = []
    if chronic.get("chronic_pain_geo_reasons") and chronic["chronic_pain_geo_reasons"] != "none":
        reasons.extend(str(chronic["chronic_pain_geo_reasons"]).split(","))

    if tier == "tier1":
        boost += 0.10
        reasons.append("tier1_metro_wait_friction")
    elif tier == "tier2":
        boost += 0.06
        reasons.append("tier2_metro_access_friction")

    if density == "very_dense":
        boost += 0.08
        reasons.append("very_high_population_density")
    elif density == "dense":
        boost += 0.05
        reasons.append("high_population_density")
    elif density == "rural":
        boost += 0.04
        reasons.append("low_provider_density_proxy")

    return {
        "pain_geo_boost": round(min(0.32, boost), 4),
        "metro_tier": tier,
        "density_tier": density,
        "pain_geo_reasons": ",".join(reasons) if reasons else "none",
        "chronic_pain_state_score": chronic.get("chronic_pain_state_score"),
        "chronic_pain_tier": chronic.get("chronic_pain_tier"),
        "chronic_pain_geo_version": chronic.get("chronic_pain_geo_version"),
    }


def customer_brand_enclave_match(
    *,
    zip_code: str | None,
    state: str | None,
    city: str | None,
) -> bool:
    """True when ZIP/city signals elevated Ceragem brand familiarity (granular match)."""
    zip5 = _normalize_zip(zip_code)
    state_code = _normalize_state(state)
    city_key = _normalize_city(city)
    if zip5 and zip5 in BRAND_ENCLAVE_ZIPS:
        return True
    if zip5 and any(zip5.startswith(prefix) for prefix in BRAND_ENCLAVE_ZIP_PREFIXES):
        return True
    if (state_code, city_key) in BRAND_ENCLAVE_CITIES:
        return True
    if (state_code, city_key) in KOREAN_CORRIDOR_CITIES:
        return True
    if (state_code, city_key) in CHINESE_CORRIDOR_CITIES:
        return True
    asian = asian_city_signals(state_code, city_key)
    if asian["asian_city_match"]:
        return True
    korean = korean_metro_signals(state_code, city_key)
    if korean["korean_metro_match"]:
        return True
    return False


def customer_sleep_deprivation_match(
    *,
    state: str | None,
    city: str | None,
) -> bool:
    """True when city is in Innerbody top sleep-deprived metro list."""
    state_code = _normalize_state(state)
    city_key = _normalize_city(city)
    return (
        (state_code, city_key) in SLEEP_DEPRIVED_TIER1_CITIES
        or (state_code, city_key) in SLEEP_DEPRIVED_TIER2_CITIES
    )


def sleep_geo_boost(
    *,
    state: str | None,
    city: str | None,
) -> dict[str, float | str | bool]:
    """
    Sleep-deprivation geographic boost for Pause M Series affinity.

    Tier-1: Innerbody top-10 most sleep-deprived cities (+0.28)
    Tier-2: ranks 11–20 (+0.16)
    """
    state_code = _normalize_state(state)
    city_key = _normalize_city(city)
    if (state_code, city_key) in SLEEP_DEPRIVED_TIER1_CITIES:
        return {
            "sleep_city_boost": 0.28,
            "sleep_geo_boost": 0.28,
            "sleep_deprivation_tier": "tier1_sleep_deprived",
            "sleep_deprivation_match": True,
            "sleep_geo_reasons": "innerbody_top10_sleep_deprived",
        }
    if (state_code, city_key) in SLEEP_DEPRIVED_TIER2_CITIES:
        return {
            "sleep_city_boost": 0.16,
            "sleep_geo_boost": 0.16,
            "sleep_deprivation_tier": "tier2_sleep_deprived",
            "sleep_deprivation_match": True,
            "sleep_geo_reasons": "innerbody_top20_sleep_deprived",
        }
    return {
        "sleep_city_boost": 0.0,
        "sleep_geo_boost": 0.0,
        "sleep_deprivation_tier": "none",
        "sleep_deprivation_match": False,
        "sleep_geo_reasons": "none",
    }


def brand_geo_boost(
    *,
    zip_code: str | None,
    state: str | None,
    city: str | None,
) -> dict[str, float | str | bool]:
    """
    Brand familiarity geographic boost (v4).

    Layers:
    1. State brand affinity (ACS 2022 Korean population rank)
    2. Asian alone % vs US 5.9% baseline (IndexMundi / Census)
    3. Korean metro/state tiers (ACS 2022 via United Koreans)
    4. Granular enclave ZIP / corridor cities
    """
    zip5 = _normalize_zip(zip_code)
    state_code = _normalize_state(state)
    city_key = _normalize_city(city)
    boost = STATE_BRAND_AFFINITY.get(state_code, 0.0)
    reasons: list[str] = []
    if state_code in STATE_BRAND_AFFINITY:
        reasons.append(f"state_brand_affinity_{state_code}")

    asian = asian_city_signals(state_code, city_key)
    if asian["asian_city_boost"]:
        boost += float(asian["asian_city_boost"])
        reasons.append(str(asian["asian_city_tier"]))

    korean = korean_metro_signals(state_code, city_key)
    if korean["korean_metro_boost"]:
        boost += float(korean["korean_metro_boost"])
        reasons.append(f"korean_metro_{korean['korean_metro_key']}")

    korean_state = korean_state_signals(state_code, korean_metro_matched=bool(korean["korean_metro_match"]))
    if korean_state["korean_state_boost"]:
        boost += float(korean_state["korean_state_boost"])
        reasons.append("korean_state_acs_top10")

    if zip5 and zip5 in BRAND_ENCLAVE_ZIPS:
        boost += 0.20
        reasons.append("asian_brand_enclave_zip")
    elif zip5 and any(zip5.startswith(prefix) for prefix in BRAND_ENCLAVE_ZIP_PREFIXES):
        boost += 0.14
        reasons.append("asian_brand_enclave_zip_prefix")

    if (state_code, city_key) in BRAND_ENCLAVE_CITIES:
        boost += 0.16
        reasons.append("asian_brand_enclave_city")
    elif (state_code, city_key) in KOREAN_CORRIDOR_CITIES:
        boost += 0.14
        reasons.append("korean_corridor_city")
    elif (state_code, city_key) in CHINESE_CORRIDOR_CITIES:
        boost += 0.14
        reasons.append("chinese_corridor_city")

    return {
        "brand_geo_boost": round(min(0.45, boost), 4),
        "brand_enclave_match": bool(reasons),
        "brand_geo_reasons": ",".join(reasons) if reasons else "none",
        "asian_baseline_pct": US_ASIAN_ALONE_BASELINE_PCT,
        **asian,
        **korean,
        **korean_state,
    }


def digital_geo_boost(
    *,
    zip_code: str | None,
    state: str | None,
    city: str | None,
) -> dict[str, float | str]:
    """Digital engagement boost for major online-commerce metros."""
    tier = metro_tier(zip_code=zip_code, state=state, city=city)
    boost = {"tier1": 0.24, "tier2": 0.14, "other": 0.0}[tier]
    return {
        "digital_geo_boost": boost,
        "digital_metro_tier": tier,
        "digital_geo_reasons": f"{tier}_metro_online_commerce" if boost else "none",
    }


def build_geo_market_signals(
    *,
    zip_code: str | None,
    state: str | None,
    city: str | None = None,
    population: int | None = None,
) -> dict:
    pain = pain_geo_boost(zip_code=zip_code, state=state, city=city, population=population)
    brand = brand_geo_boost(zip_code=zip_code, state=state, city=city)
    digital = digital_geo_boost(zip_code=zip_code, state=state, city=city)
    sleep = sleep_geo_boost(state=state, city=city)
    return {
        "geo_signal_version": GEO_SIGNAL_VERSION,
        **pain,
        **brand,
        **digital,
        **sleep,
    }
