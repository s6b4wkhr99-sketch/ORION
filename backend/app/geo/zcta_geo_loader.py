"""Load or build per-state ZCTA GeoJSON from Census cartographic boundary shapefiles."""

from __future__ import annotations

import json
import logging
import zipfile
from functools import lru_cache
from pathlib import Path
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)

GEO_DIR = Path(__file__).resolve().parents[2] / "data" / "geo"
NATIONAL_GEOJSON = GEO_DIR / "zcta_us_500k.geojson"
NATIONAL_SHAPEFILE_ZIP = GEO_DIR / "cb_2020_us_zcta520_500k.zip"
NATIONAL_SHAPEFILE_SHP = GEO_DIR / "cb_2020_us_zcta520_500k.shp"
CENSUS_ZCTA_ZIP_URL = "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip"

# Approximate lon/lat envelopes (WGS84) for state filtering.
STATE_BBOX: dict[str, tuple[float, float, float, float]] = {
    "AL": (-88.5, 30.1, -84.9, 35.0),
    "AK": (-179.0, 51.0, -129.0, 71.5),
    "AZ": (-114.8, 31.3, -109.0, 37.0),
    "AR": (-94.6, 33.0, -89.6, 36.5),
    "CA": (-124.5, 32.5, -114.0, 42.1),
    "CO": (-109.1, 36.9, -102.0, 41.0),
    "CT": (-73.7, 40.9, -71.8, 42.1),
    "DE": (-75.8, 38.4, -75.0, 39.8),
    "DC": (-77.1, 38.8, -76.9, 39.0),
    "FL": (-87.6, 24.4, -80.0, 31.1),
    "GA": (-85.6, 30.4, -80.8, 35.0),
    "HI": (-160.3, 18.9, -154.8, 22.3),
    "ID": (-117.2, 42.0, -111.0, 49.0),
    "IL": (-91.5, 36.9, -87.5, 42.5),
    "IN": (-88.1, 37.8, -84.8, 41.8),
    "IA": (-96.6, 40.4, -90.1, 43.5),
    "KS": (-102.1, 37.0, -94.6, 40.0),
    "KY": (-89.6, 36.5, -81.9, 39.2),
    "LA": (-94.0, 28.9, -88.8, 33.0),
    "ME": (-71.1, 43.0, -66.9, 47.5),
    "MD": (-79.5, 37.9, -75.0, 39.7),
    "MA": (-73.5, 41.2, -69.9, 42.9),
    "MI": (-90.4, 41.7, -82.4, 48.3),
    "MN": (-97.2, 43.5, -89.5, 49.4),
    "MS": (-91.7, 30.2, -88.1, 35.0),
    "MO": (-95.8, 36.0, -89.1, 40.6),
    "MT": (-116.1, 44.4, -104.0, 49.0),
    "NE": (-104.1, 40.0, -95.3, 43.0),
    "NV": (-120.0, 35.0, -114.0, 42.0),
    "NH": (-72.6, 42.7, -70.6, 45.3),
    "NJ": (-75.6, 38.9, -73.9, 41.4),
    "NM": (-109.1, 31.3, -103.0, 37.0),
    "NY": (-79.8, 40.5, -71.8, 45.0),
    "NC": (-84.3, 33.8, -75.5, 36.6),
    "ND": (-104.1, 45.9, -96.6, 49.0),
    "OH": (-84.8, 38.4, -80.5, 42.0),
    "OK": (-103.0, 33.6, -94.4, 37.0),
    "OR": (-124.6, 42.0, -116.5, 46.3),
    "PA": (-80.5, 39.7, -74.7, 42.3),
    "RI": (-71.9, 41.1, -71.1, 42.0),
    "SC": (-83.4, 32.0, -78.5, 35.2),
    "SD": (-104.1, 42.5, -96.4, 45.9),
    "TN": (-90.3, 34.9, -81.6, 36.7),
    "TX": (-106.7, 25.8, -93.5, 36.5),
    "UT": (-114.1, 37.0, -109.0, 42.0),
    "VT": (-73.4, 42.7, -71.5, 45.0),
    "VA": (-83.7, 36.5, -75.2, 39.5),
    "WA": (-124.8, 45.5, -116.9, 49.0),
    "WV": (-82.6, 37.2, -77.7, 40.6),
    "WI": (-92.9, 42.5, -86.2, 47.1),
    "WY": (-111.1, 41.0, -104.0, 45.0),
}


def state_geojson_path(state: str) -> Path:
    return GEO_DIR / f"zcta_{state.upper()}_500k.geojson"


def _bbox_intersects(shape_bbox: tuple[float, float, float, float], state: str) -> bool:
    bbox = STATE_BBOX.get(state.upper())
    if not bbox:
        return False
    lon_min, lat_min, lon_max, lat_max = bbox
    xmin, ymin, xmax, ymax = shape_bbox
    return not (xmax < lon_min or xmin > lon_max or ymax < lat_min or ymin > lat_max)


def ensure_national_shapefile() -> Path | None:
    """Download and extract Census 2020 ZCTA 500k shapefile if missing."""
    if NATIONAL_SHAPEFILE_SHP.exists():
        return NATIONAL_SHAPEFILE_SHP

    GEO_DIR.mkdir(parents=True, exist_ok=True)
    if not NATIONAL_SHAPEFILE_ZIP.exists():
        try:
            logger.info("Downloading Census ZCTA shapefile…")
            urlretrieve(CENSUS_ZCTA_ZIP_URL, NATIONAL_SHAPEFILE_ZIP)
        except OSError as exc:
            logger.warning("ZCTA shapefile download failed: %s", exc)
            return None

    try:
        with zipfile.ZipFile(NATIONAL_SHAPEFILE_ZIP) as zf:
            zf.extractall(GEO_DIR)
    except (OSError, zipfile.BadZipFile) as exc:
        logger.warning("ZCTA shapefile extract failed: %s", exc)
        return None

    return NATIONAL_SHAPEFILE_SHP if NATIONAL_SHAPEFILE_SHP.exists() else None


def build_state_geojson(state: str) -> dict | None:
    """Build GeoJSON for one state from the national shapefile."""
    state = state.upper()
    shp_path = ensure_national_shapefile()
    if not shp_path:
        return None

    try:
        import shapefile  # pyshp
    except ImportError:
        logger.warning("pyshp not installed — cannot build ZCTA GeoJSON")
        return None

    reader = shapefile.Reader(str(shp_path))
    fields = [f[0] for f in reader.fields[1:]]
    zip_field = next((f for f in fields if "ZCTA" in f.upper()), fields[0] if fields else None)

    features: list[dict] = []
    for shape_rec in reader.iterShapeRecords():
        if not _bbox_intersects(shape_rec.shape.bbox, state):
            continue
        rec = shape_rec.record.as_dict() if hasattr(shape_rec.record, "as_dict") else {}
        zip_code = str(rec.get(zip_field or "") or (shape_rec.record[0] if shape_rec.record else "")).zfill(5)
        if len(zip_code) != 5:
            continue
        features.append(
            {
                "type": "Feature",
                "id": zip_code,
                "properties": {
                    "ZCTA5CE20": zip_code,
                    "GEOID20": zip_code,
                    "zip": zip_code,
                    "STUSPS": state,
                },
                "geometry": shape_rec.shape.__geo_interface__,
            }
        )

    if not features:
        return None

    collection = {"type": "FeatureCollection", "features": features}
    out_path = state_geojson_path(state)
    out_path.write_text(json.dumps(collection), encoding="utf-8")
    logger.info("Built %s ZCTA features for %s", len(features), state)
    return collection


@lru_cache(maxsize=60)
def load_state_zcta_geojson(state: str) -> dict | None:
    """Return cached state ZCTA GeoJSON, building from shapefile on first use."""
    state = state.upper()
    if not state:
        return None

    path = state_geojson_path(state)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    if NATIONAL_GEOJSON.exists():
        try:
            national = json.loads(NATIONAL_GEOJSON.read_text(encoding="utf-8"))
            features = []
            for feature in national.get("features") or []:
                props = feature.get("properties") or {}
                zip_code = str(props.get("ZCTA5CE20") or props.get("GEOID20") or props.get("ZCTA5") or "").zfill(5)
                st = str(props.get("STUSPS") or props.get("state") or "").upper()
                if st and st != state:
                    continue
                if not st and zip_code:
                    # Filter by bbox using geometry bounds when state code absent.
                    geom = feature.get("geometry") or {}
                    coords = geom.get("coordinates")
                    if coords and not _geometry_in_state(coords, state):
                        continue
                if zip_code:
                    features.append(feature)
            if features:
                return {"type": "FeatureCollection", "features": features}
        except (OSError, json.JSONDecodeError):
            pass

    return build_state_geojson(state)


def _geometry_in_state(coords, state: str) -> bool:
    bbox = STATE_BBOX.get(state.upper())
    if not bbox:
        return True
    lon_min, lat_min, lon_max, lat_max = bbox

    def walk(node):
        if isinstance(node, (list, tuple)):
            if len(node) >= 2 and isinstance(node[0], (int, float)):
                lon, lat = float(node[0]), float(node[1])
                return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max
            return any(walk(item) for item in node)
        return False

    return walk(coords)
