"""Top-50 CBSA reference + ZIP/city resolution for metro rollups."""

from __future__ import annotations

from dataclasses import dataclass

from app.geo.brand_familiarity_geo import CITY_ASIAN_ALONE_PCT, US_ASIAN_ALONE_BASELINE_PCT

# Top 50 US metropolitan areas by population (2022 Census CBSA estimates).
# Figures (population/median income/Asian %) are approximate 2022 estimates and
# geo centers/radii below are approximate — validate against official Census data if precision matters.
TOP_METRO_CBSAS: tuple[dict, ...] = (
    {"code": "35620", "name": "New York-Newark-Jersey City, NY-NJ-PA", "population": 19_978_000, "median_income": 86800, "asian_pct": 12.8, "states": ("NY", "NJ", "PA")},
    {"code": "31080", "name": "Los Angeles-Long Beach-Anaheim, CA", "population": 12_916_000, "median_income": 82300, "asian_pct": 15.4, "states": ("CA",)},
    {"code": "16980", "name": "Chicago-Naperville-Elgin, IL-IN-WI", "population": 9_618_000, "median_income": 79100, "asian_pct": 7.2, "states": ("IL", "IN", "WI")},
    {"code": "19100", "name": "Dallas-Fort Worth-Arlington, TX", "population": 8_121_000, "median_income": 78500, "asian_pct": 7.8, "states": ("TX",)},
    {"code": "26420", "name": "Houston-The Woodlands-Sugar Land, TX", "population": 7_340_000, "median_income": 74100, "asian_pct": 7.1, "states": ("TX",)},
    {"code": "47900", "name": "Washington-Arlington-Alexandria, DC-VA-MD-WV", "population": 6_385_000, "median_income": 112400, "asian_pct": 10.9, "states": ("DC", "VA", "MD", "WV")},
    {"code": "33100", "name": "Miami-Fort Lauderdale-Pompano Beach, FL", "population": 6_138_000, "median_income": 62900, "asian_pct": 2.8, "states": ("FL",)},
    {"code": "37980", "name": "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", "population": 6_245_000, "median_income": 79800, "asian_pct": 5.9, "states": ("PA", "NJ", "DE", "MD")},
    {"code": "12060", "name": "Atlanta-Sandy Springs-Alpharetta, GA", "population": 6_271_000, "median_income": 76800, "asian_pct": 5.4, "states": ("GA",)},
    {"code": "38060", "name": "Phoenix-Mesa-Chandler, AZ", "population": 5_070_000, "median_income": 72400, "asian_pct": 4.2, "states": ("AZ",)},
    {"code": "14460", "name": "Boston-Cambridge-Newton, MA-NH", "population": 4_941_000, "median_income": 99800, "asian_pct": 7.5, "states": ("MA", "NH")},
    {"code": "41860", "name": "San Francisco-Oakland-Berkeley, CA", "population": 4_623_000, "median_income": 126200, "asian_pct": 24.2, "states": ("CA",)},
    {"code": "40140", "name": "Riverside-San Bernardino-Ontario, CA", "population": 4_688_000, "median_income": 72400, "asian_pct": 7.0, "states": ("CA",)},
    {"code": "19820", "name": "Detroit-Warren-Dearborn, MI", "population": 4_345_000, "median_income": 68900, "asian_pct": 3.6, "states": ("MI",)},
    {"code": "42660", "name": "Seattle-Tacoma-Bellevue, WA", "population": 4_018_000, "median_income": 102600, "asian_pct": 14.8, "states": ("WA",)},
    {"code": "33460", "name": "Minneapolis-St. Paul-Bloomington, MN-WI", "population": 3_690_000, "median_income": 88200, "asian_pct": 5.8, "states": ("MN", "WI")},
    {"code": "41740", "name": "San Diego-Chula Vista-Carlsbad, CA", "population": 3_286_000, "median_income": 91200, "asian_pct": 12.1, "states": ("CA",)},
    {"code": "45300", "name": "Tampa-St. Petersburg-Clearwater, FL", "population": 3_194_000, "median_income": 62800, "asian_pct": 3.4, "states": ("FL",)},
    {"code": "19740", "name": "Denver-Aurora-Lakewood, CO", "population": 2_963_000, "median_income": 90200, "asian_pct": 4.9, "states": ("CO",)},
    {"code": "12580", "name": "Baltimore-Columbia-Towson, MD", "population": 2_834_000, "median_income": 91200, "asian_pct": 5.6, "states": ("MD",)},
    {"code": "41180", "name": "St. Louis, MO-IL", "population": 2_820_000, "median_income": 70100, "asian_pct": 2.7, "states": ("MO", "IL")},
    {"code": "36740", "name": "Orlando-Kissimmee-Sanford, FL", "population": 2_691_000, "median_income": 65200, "asian_pct": 3.8, "states": ("FL",)},
    {"code": "16740", "name": "Charlotte-Concord-Gastonia, NC-SC", "population": 2_756_000, "median_income": 74200, "asian_pct": 3.9, "states": ("NC", "SC")},
    {"code": "41700", "name": "San Antonio-New Braunfels, TX", "population": 2_601_000, "median_income": 64100, "asian_pct": 2.9, "states": ("TX",)},
    {"code": "38900", "name": "Portland-Vancouver-Hillsboro, OR-WA", "population": 2_512_000, "median_income": 84200, "asian_pct": 6.2, "states": ("OR", "WA")},
    {"code": "40900", "name": "Sacramento-Roseville-Folsom, CA", "population": 2_397_000, "median_income": 81200, "asian_pct": 11.4, "states": ("CA",)},
    {"code": "38300", "name": "Pittsburgh, PA", "population": 2_370_000, "median_income": 67800, "asian_pct": 2.5, "states": ("PA",)},
    {"code": "29820", "name": "Las Vegas-Henderson-Paradise, NV", "population": 2_265_000, "median_income": 67400, "asian_pct": 9.8, "states": ("NV",)},
    {"code": "12420", "name": "Austin-Round Rock-Georgetown, TX", "population": 2_352_000, "median_income": 89200, "asian_pct": 5.6, "states": ("TX",)},
    {"code": "17140", "name": "Cincinnati, OH-KY-IN", "population": 2_256_000, "median_income": 72800, "asian_pct": 2.4, "states": ("OH", "KY", "IN")},
    {"code": "28140", "name": "Kansas City, MO-KS", "population": 2_199_000, "median_income": 74300, "asian_pct": 2.6, "states": ("MO", "KS")},
    {"code": "17460", "name": "Cleveland-Elyria, OH", "population": 2_158_000, "median_income": 61800, "asian_pct": 2.3, "states": ("OH",)},
    {"code": "18140", "name": "Columbus, OH", "population": 2_151_000, "median_income": 72100, "asian_pct": 4.4, "states": ("OH",)},
    {"code": "26900", "name": "Indianapolis-Carmel-Anderson, IN", "population": 2_112_000, "median_income": 70200, "asian_pct": 3.4, "states": ("IN",)},
    {"code": "34980", "name": "Nashville-Davidson-Murfreesboro-Franklin, TN", "population": 2_012_000, "median_income": 72300, "asian_pct": 2.5, "states": ("TN",)},
    {"code": "41940", "name": "San Jose-Sunnyvale-Santa Clara, CA", "population": 1_952_000, "median_income": 141600, "asian_pct": 38.0, "states": ("CA",)},
    {"code": "47260", "name": "Virginia Beach-Norfolk-Newport News, VA-NC", "population": 1_787_000, "median_income": 74600, "asian_pct": 4.0, "states": ("VA", "NC")},
    {"code": "39300", "name": "Providence-Warwick, RI-MA", "population": 1_676_000, "median_income": 76200, "asian_pct": 3.2, "states": ("RI", "MA")},
    {"code": "27260", "name": "Jacksonville, FL", "population": 1_675_000, "median_income": 67500, "asian_pct": 4.6, "states": ("FL",)},
    {"code": "33340", "name": "Milwaukee-Waukesha, WI", "population": 1_566_000, "median_income": 68200, "asian_pct": 3.6, "states": ("WI",)},
    {"code": "39580", "name": "Raleigh-Cary, NC", "population": 1_449_000, "median_income": 89000, "asian_pct": 6.6, "states": ("NC",)},
    {"code": "36420", "name": "Oklahoma City, OK", "population": 1_441_000, "median_income": 63400, "asian_pct": 3.3, "states": ("OK",)},
    {"code": "32820", "name": "Memphis, TN-MS-AR", "population": 1_336_000, "median_income": 58200, "asian_pct": 2.1, "states": ("TN", "MS", "AR")},
    {"code": "40060", "name": "Richmond, VA", "population": 1_314_000, "median_income": 76400, "asian_pct": 4.1, "states": ("VA",)},
    {"code": "31140", "name": "Louisville/Jefferson County, KY-IN", "population": 1_286_000, "median_income": 64300, "asian_pct": 2.5, "states": ("KY", "IN")},
    {"code": "35380", "name": "New Orleans-Metairie, LA", "population": 1_271_000, "median_income": 58500, "asian_pct": 3.0, "states": ("LA",)},
    {"code": "41620", "name": "Salt Lake City, UT", "population": 1_257_000, "median_income": 85300, "asian_pct": 4.4, "states": ("UT",)},
    {"code": "25540", "name": "Hartford-East Hartford-Middletown, CT", "population": 1_214_000, "median_income": 87500, "asian_pct": 4.3, "states": ("CT",)},
    {"code": "15380", "name": "Buffalo-Cheektowaga, NY", "population": 1_166_000, "median_income": 65200, "asian_pct": 3.4, "states": ("NY",)},
    {"code": "13820", "name": "Birmingham-Hoover, AL", "population": 1_115_000, "median_income": 62100, "asian_pct": 1.7, "states": ("AL",)},
)

# Backwards-compatible alias (list expanded from 30 to 50 metros).
TOP_30_CBSAS = TOP_METRO_CBSAS

# Principal cities for metro resolution (state, city upper).
METRO_CITY_INDEX: dict[tuple[str, str], str] = {}
for metro in TOP_30_CBSAS:
    code = metro["code"]
    for state in metro["states"]:
        METRO_CITY_INDEX.setdefault((state, state), code)
    for (st, city), _pct in CITY_ASIAN_ALONE_PCT.items():
        if st in metro["states"]:
            METRO_CITY_INDEX[(st, city.upper())] = code

# Explicit principal cities per CBSA.
_EXTRA_CITIES: dict[str, list[tuple[str, str]]] = {
    "35620": [("NY", "NEW YORK"), ("NY", "BROOKLYN"), ("NY", "QUEENS"), ("NJ", "JERSEY CITY"), ("NJ", "NEWARK")],
    "31080": [("CA", "LOS ANGELES"), ("CA", "LONG BEACH"), ("CA", "ANAHEIM"), ("CA", "IRVINE"), ("CA", "KOREATOWN")],
    "16980": [("IL", "CHICAGO"), ("IL", "NAPERVILLE"), ("IL", "SCHAUMBURG")],
    "19100": [("TX", "DALLAS"), ("TX", "FORT WORTH"), ("TX", "ARLINGTON"), ("TX", "PLANO"), ("TX", "IRVING")],
    "26420": [("TX", "HOUSTON"), ("TX", "KATY"), ("TX", "SUGAR LAND"), ("TX", "SPRING")],
    "47900": [("DC", "WASHINGTON"), ("VA", "ARLINGTON"), ("VA", "ALEXANDRIA"), ("MD", "BETHESDA"), ("MD", "ROCKVILLE")],
    "33100": [("FL", "MIAMI"), ("FL", "FORT LAUDERDALE"), ("FL", "HOLLYWOOD")],
    "37980": [("PA", "PHILADELPHIA"), ("NJ", "CAMDEN"), ("DE", "WILMINGTON")],
    "12060": [("GA", "ATLANTA"), ("GA", "DULUTH"), ("GA", "SUWANEE")],
    "38060": [("AZ", "PHOENIX"), ("AZ", "MESA"), ("AZ", "CHANDLER"), ("AZ", "SCOTTSDALE")],
    "14460": [("MA", "BOSTON"), ("MA", "CAMBRIDGE"), ("MA", "NEWTON")],
    "41860": [("CA", "SAN FRANCISCO"), ("CA", "OAKLAND"), ("CA", "BERKELEY")],
    "40140": [("CA", "RIVERSIDE"), ("CA", "SAN BERNARDINO"), ("CA", "ONTARIO")],
    "19820": [("MI", "DETROIT"), ("MI", "WARREN"), ("MI", "DEARBORN")],
    "42660": [("WA", "SEATTLE"), ("WA", "TACOMA"), ("WA", "BELLEVUE"), ("WA", "FEDERAL WAY")],
    "33460": [("MN", "MINNEAPOLIS"), ("MN", "ST PAUL"), ("MN", "BLOOMINGTON")],
    "41740": [("CA", "SAN DIEGO"), ("CA", "CHULA VISTA"), ("CA", "CARLSBAD")],
    "45300": [("FL", "TAMPA"), ("FL", "ST PETERSBURG"), ("FL", "CLEARWATER")],
    "19740": [("CO", "DENVER"), ("CO", "AURORA"), ("CO", "LAKEWOOD")],
    "12580": [("MD", "BALTIMORE"), ("MD", "COLUMBIA"), ("MD", "TOWSON")],
    "41180": [("MO", "ST LOUIS"), ("IL", "ST LOUIS")],
    "36740": [("FL", "ORLANDO"), ("FL", "KISSIMMEE"), ("FL", "SANFORD")],
    "16740": [("NC", "CHARLOTTE"), ("NC", "CONCORD"), ("SC", "GASTONIA")],
    "41700": [("TX", "SAN ANTONIO"), ("TX", "NEW BRAUNFELS")],
    "38900": [("OR", "PORTLAND"), ("WA", "VANCOUVER"), ("OR", "HILLSBORO")],
    "40900": [("CA", "SACRAMENTO"), ("CA", "ROSEVILLE"), ("CA", "FOLSOM")],
    "38300": [("PA", "PITTSBURGH")],
    "29820": [("NV", "LAS VEGAS"), ("NV", "HENDERSON"), ("NV", "PARADISE")],
    "12420": [("TX", "AUSTIN"), ("TX", "ROUND ROCK"), ("TX", "GEORGETOWN")],
    "17140": [("OH", "CINCINNATI"), ("KY", "COVINGTON")],
    "28140": [("MO", "KANSAS CITY"), ("KS", "OVERLAND PARK"), ("KS", "KANSAS CITY")],
    "17460": [("OH", "CLEVELAND"), ("OH", "ELYRIA"), ("OH", "PARMA")],
    "18140": [("OH", "COLUMBUS"), ("OH", "DUBLIN"), ("OH", "WESTERVILLE")],
    "26900": [("IN", "INDIANAPOLIS"), ("IN", "CARMEL"), ("IN", "FISHERS")],
    "34980": [("TN", "NASHVILLE"), ("TN", "FRANKLIN"), ("TN", "MURFREESBORO")],
    "41940": [("CA", "SAN JOSE"), ("CA", "SUNNYVALE"), ("CA", "SANTA CLARA")],
    "47260": [("VA", "VIRGINIA BEACH"), ("VA", "NORFOLK"), ("VA", "CHESAPEAKE")],
    "39300": [("RI", "PROVIDENCE"), ("RI", "WARWICK"), ("RI", "CRANSTON")],
    "27260": [("FL", "JACKSONVILLE")],
    "33340": [("WI", "MILWAUKEE"), ("WI", "WAUKESHA")],
    "39580": [("NC", "RALEIGH"), ("NC", "CARY")],
    "36420": [("OK", "OKLAHOMA CITY"), ("OK", "NORMAN"), ("OK", "EDMOND")],
    "32820": [("TN", "MEMPHIS"), ("MS", "SOUTHAVEN")],
    "40060": [("VA", "RICHMOND"), ("VA", "HENRICO")],
    "31140": [("KY", "LOUISVILLE"), ("IN", "JEFFERSONVILLE")],
    "35380": [("LA", "NEW ORLEANS"), ("LA", "METAIRIE")],
    "41620": [("UT", "SALT LAKE CITY"), ("UT", "WEST VALLEY CITY")],
    "25540": [("CT", "HARTFORD"), ("CT", "WEST HARTFORD"), ("CT", "MIDDLETOWN")],
    "15380": [("NY", "BUFFALO"), ("NY", "CHEEKTOWAGA")],
    "13820": [("AL", "BIRMINGHAM"), ("AL", "HOOVER")],
}
for cbsa_code, cities in _EXTRA_CITIES.items():
    for st, city in cities:
        METRO_CITY_INDEX[(st, city)] = cbsa_code

_CBSA_BY_CODE = {m["code"]: m for m in TOP_30_CBSAS}


def normalize_city(city: str | None) -> str:
    return (city or "").strip().upper()


def resolve_cbsa(state: str | None, city: str | None, zip_code: str | None = None) -> str | None:
    st = (state or "").strip().upper()
    city_key = normalize_city(city)
    if st and city_key:
        hit = METRO_CITY_INDEX.get((st, city_key))
        if hit:
            return hit
    if st:
        for metro in TOP_30_CBSAS:
            if st in metro["states"]:
                return metro["code"]
    return None


def cbsa_meta(code: str) -> dict | None:
    return _CBSA_BY_CODE.get(code)


def asian_relative_index(state: str | None, city: str | None) -> float | None:
    st = (state or "").strip().upper()
    city_key = normalize_city(city)
    pct = CITY_ASIAN_ALONE_PCT.get((st, city_key))
    if pct is None:
        return None
    return round(pct / US_ASIAN_ALONE_BASELINE_PCT, 2)


def state_asian_pct_estimate(state: str | None) -> float | None:
    st = (state or "").strip().upper()
    values = [pct for (s, _c), pct in CITY_ASIAN_ALONE_PCT.items() if s == st]
    if not values:
        for metro in TOP_30_CBSAS:
            if st in metro["states"]:
                return metro["asian_pct"]
        return None
    return round(sum(values) / len(values), 1)
