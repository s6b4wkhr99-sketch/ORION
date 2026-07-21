"""Geographic extents for Top-50 CBSAs used to assign ZCTAs to a metro.

The dataset lacks a ZIP→county / ZIP→CBSA crosswalk (and ZIP lat/lon), so metro membership
is derived from each ZCTA polygon's centroid (which we DO have, from the Census ZCTA GeoJSON):
a ZCTA belongs to the metro whose center it is nearest to, provided it falls within that metro's
approximate radius. Adjacent metros (e.g. LA vs. Riverside, DC vs. Baltimore) are separated by the
nearest-center rule, normalized by each metro's radius so different-sized metros compare fairly.
"""

from __future__ import annotations

import math

# code -> (center_lat, center_lng, radius_km) — approximate metropolitan extents.
CBSA_GEO: dict[str, tuple[float, float, float]] = {
    "35620": (40.71, -74.01, 80),   # New York-Newark-Jersey City
    "31080": (34.05, -118.24, 70),  # Los Angeles-Long Beach-Anaheim
    "16980": (41.88, -87.63, 70),   # Chicago-Naperville-Elgin
    "19100": (32.78, -96.80, 75),   # Dallas-Fort Worth-Arlington
    "26420": (29.76, -95.37, 75),   # Houston-The Woodlands-Sugar Land
    "47900": (38.90, -77.04, 60),   # Washington-Arlington-Alexandria
    "33100": (26.12, -80.20, 80),   # Miami-Fort Lauderdale-Pompano Beach
    "37980": (39.95, -75.16, 60),   # Philadelphia-Camden-Wilmington
    "12060": (33.75, -84.39, 70),   # Atlanta-Sandy Springs-Alpharetta
    "38060": (33.45, -112.07, 65),  # Phoenix-Mesa-Chandler
    "14460": (42.36, -71.06, 60),   # Boston-Cambridge-Newton
    "41860": (37.77, -122.20, 60),  # San Francisco-Oakland-Berkeley
    "40140": (33.98, -117.37, 75),  # Riverside-San Bernardino-Ontario
    "19820": (42.33, -83.05, 60),   # Detroit-Warren-Dearborn
    "42660": (47.61, -122.33, 60),  # Seattle-Tacoma-Bellevue
    "33460": (44.98, -93.27, 60),   # Minneapolis-St. Paul-Bloomington
    "41740": (32.82, -117.13, 55),  # San Diego-Chula Vista-Carlsbad
    "45300": (27.95, -82.46, 60),   # Tampa-St. Petersburg-Clearwater
    "19740": (39.74, -104.99, 60),  # Denver-Aurora-Lakewood
    "12580": (39.29, -76.61, 45),   # Baltimore-Columbia-Towson
    "41180": (38.63, -90.20, 60),   # St. Louis
    "36740": (28.54, -81.38, 55),   # Orlando-Kissimmee-Sanford
    "16740": (35.23, -80.84, 60),   # Charlotte-Concord-Gastonia
    "41700": (29.42, -98.49, 60),   # San Antonio-New Braunfels
    "38900": (45.52, -122.68, 60),  # Portland-Vancouver-Hillsboro
    "40900": (38.58, -121.49, 55),  # Sacramento-Roseville-Folsom
    "38300": (40.44, -79.996, 60),  # Pittsburgh
    "29820": (36.17, -115.14, 55),  # Las Vegas-Henderson-Paradise
    "12420": (30.27, -97.74, 55),   # Austin-Round Rock-Georgetown
    "17140": (39.10, -84.51, 55),   # Cincinnati
    "28140": (39.10, -94.58, 65),   # Kansas City
    "17460": (41.50, -81.69, 55),   # Cleveland-Elyria
    "18140": (39.96, -83.00, 55),   # Columbus
    "26900": (39.77, -86.16, 55),   # Indianapolis-Carmel-Anderson
    "34980": (36.16, -86.78, 60),   # Nashville-Davidson-Murfreesboro-Franklin
    "41940": (37.34, -121.89, 45),  # San Jose-Sunnyvale-Santa Clara
    "47260": (36.85, -76.29, 60),   # Virginia Beach-Norfolk-Newport News
    "39300": (41.82, -71.41, 45),   # Providence-Warwick
    "27260": (30.33, -81.66, 55),   # Jacksonville
    "33340": (43.04, -87.91, 45),   # Milwaukee-Waukesha
    "39580": (35.78, -78.64, 50),   # Raleigh-Cary
    "36420": (35.47, -97.52, 60),   # Oklahoma City
    "32820": (35.15, -90.05, 55),   # Memphis
    "40060": (37.54, -77.44, 50),   # Richmond
    "31140": (38.25, -85.76, 50),   # Louisville/Jefferson County
    "35380": (29.95, -90.07, 50),   # New Orleans-Metairie
    "41620": (40.76, -111.89, 55),  # Salt Lake City
    "25540": (41.76, -72.67, 40),   # Hartford-East Hartford-Middletown
    "15380": (42.89, -78.88, 45),   # Buffalo-Cheektowaga
    "13820": (33.52, -86.80, 50),   # Birmingham-Hoover
}

_EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest_cbsa(lat: float, lng: float) -> str | None:
    """Return the CBSA whose center is nearest (radius-normalized) and within radius, else None."""
    best_code: str | None = None
    best_ratio: float | None = None
    for code, (clat, clng, radius) in CBSA_GEO.items():
        dist = haversine_km(lat, lng, clat, clng)
        if dist <= radius:
            ratio = dist / radius
            if best_ratio is None or ratio < best_ratio:
                best_ratio = ratio
                best_code = code
    return best_code


def geometry_centroid(geometry: dict | None) -> tuple[float, float] | None:
    """Approximate centroid (lat, lng) as the mean of all polygon vertices."""
    if not geometry:
        return None
    coords = geometry.get("coordinates")
    if not coords:
        return None
    sum_lat = 0.0
    sum_lng = 0.0
    count = 0

    def walk(node) -> None:
        nonlocal sum_lat, sum_lng, count
        if isinstance(node, (list, tuple)):
            if len(node) >= 2 and isinstance(node[0], (int, float)) and isinstance(node[1], (int, float)):
                sum_lng += float(node[0])
                sum_lat += float(node[1])
                count += 1
            else:
                for item in node:
                    walk(item)

    walk(coords)
    if count == 0:
        return None
    return (sum_lat / count, sum_lng / count)
