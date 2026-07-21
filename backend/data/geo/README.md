# Geo assets for Market Intelligence

## ZCTA choropleth

Per-state GeoJSON is built from the Census **2020 cartographic boundary** ZCTA shapefile (1:500,000).

### Quick start

```bash
cd backend
python scripts/build_zcta_state_geojson.py --state CA --state TX
```

Or build all states (downloads ~64 MB shapefile once):

```bash
python scripts/build_zcta_state_geojson.py
```

Output files: `data/geo/zcta_{ST}_500k.geojson`

The API (`GET /api/v1/geo/zcta?state=XX`) auto-builds a state file on first request when the national shapefile is present.

### Optional national bundle

You may also place a pre-built national file:

`zcta_us_500k.geojson`

Source: [Census Cartographic Boundary — ZCTA520 (2020)](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html)

### Fallback

Without ZCTA polygons, the API aggregates ZIP metrics to county/city and the frontend renders on the US Atlas county layer.
