"""
Global administrative division resolver.

Resolves any lat/lon to its top-level administrative division (state, province,
region, prefecture, etc.) with bounding box. Works worldwide.

Strategy:
  1. US locations: Fast lookup from hardcoded US_STATE_BOUNDS (no API call).
  2. All other countries: Nominatim reverse geocode at zoom=5 returns the
     admin-level-1 division name + bounding box for any country worldwide.
  3. In-memory cache prevents repeated lookups for the same division.

This is the translation layer that lets US-specific state-level data loading
work for any country: Canadian provinces, French regions, Japanese prefectures,
Australian states, Brazilian estados, etc.
"""
import logging
import math
import re
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# US state bounding boxes (south_lat, west_lon, north_lat, east_lon)
# Fast fallback that avoids any API call for US locations.
# Source: US Census Bureau TIGER shapefiles, rounded to 1 decimal.
# ---------------------------------------------------------------------------
US_STATE_BOUNDS: Dict[str, Tuple[float, float, float, float]] = {
    "AL": (30.2, -88.5, 35.0, -84.9),
    "AK": (51.2, -179.1, 71.4, 179.8),
    "AZ": (31.3, -114.8, 37.0, -109.0),
    "AR": (33.0, -94.6, 36.5, -89.6),
    "CA": (32.5, -124.4, 42.0, -114.1),
    "CO": (37.0, -109.1, 41.0, -102.0),
    "CT": (41.0, -73.7, 42.1, -71.8),
    "DE": (38.5, -75.8, 39.8, -75.0),
    "FL": (24.5, -87.6, 31.0, -80.0),
    "GA": (30.4, -85.6, 35.0, -80.8),
    "HI": (18.9, -160.2, 22.2, -154.8),
    "ID": (42.0, -117.2, 49.0, -111.0),
    "IL": (37.0, -91.5, 42.5, -87.0),
    "IN": (37.8, -88.1, 41.8, -84.8),
    "IA": (40.4, -96.6, 43.5, -90.1),
    "KS": (37.0, -102.1, 40.0, -94.6),
    "KY": (36.5, -89.6, 39.1, -81.9),
    "LA": (29.0, -94.0, 33.0, -89.0),
    "ME": (43.1, -71.1, 47.5, -66.9),
    "MD": (37.9, -79.5, 39.7, -75.0),
    "MA": (41.2, -73.5, 42.9, -69.9),
    "MI": (41.7, -90.4, 48.3, -82.1),
    "MN": (43.5, -97.2, 49.4, -89.5),
    "MS": (30.2, -91.7, 35.0, -88.1),
    "MO": (36.0, -95.8, 40.6, -89.1),
    "MT": (44.4, -116.0, 49.0, -104.0),
    "NE": (40.0, -104.1, 43.0, -95.3),
    "NV": (35.0, -120.0, 42.0, -114.0),
    "NH": (42.7, -72.6, 45.3, -70.7),
    "NJ": (38.9, -75.6, 41.4, -73.9),
    "NM": (31.3, -109.1, 37.0, -103.0),
    "NY": (40.5, -79.8, 45.0, -71.9),
    "NC": (33.8, -84.3, 36.6, -75.5),
    "ND": (45.9, -104.1, 49.0, -96.6),
    "OH": (38.4, -84.8, 42.0, -80.5),
    "OK": (33.6, -103.0, 37.0, -94.4),
    "OR": (42.0, -124.6, 46.3, -116.5),
    "PA": (39.7, -80.5, 42.3, -74.7),
    "RI": (41.1, -71.9, 42.0, -71.1),
    "SC": (32.0, -83.4, 35.2, -78.5),
    "SD": (42.5, -104.1, 45.9, -96.4),
    "TN": (35.0, -90.3, 36.7, -81.6),
    "TX": (25.8, -106.6, 36.5, -93.5),
    "UT": (37.0, -114.1, 42.0, -109.0),
    "VT": (42.7, -73.4, 45.0, -71.5),
    "VA": (36.5, -83.7, 39.5, -75.2),
    "WA": (45.5, -124.8, 49.0, -116.9),
    "WV": (37.2, -82.6, 40.6, -77.7),
    "WI": (42.5, -92.9, 47.1, -86.8),
    "WY": (41.0, -111.1, 45.0, -104.1),
    "DC": (38.8, -77.1, 39.0, -76.9),
}

# Reverse map: full US state name -> code
_US_STATE_NAMES: Dict[str, str] = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}

# Code -> full name reverse lookup
_US_CODE_TO_NAME: Dict[str, str] = {v: k for k, v in _US_STATE_NAMES.items()}


# ---------------------------------------------------------------------------
# In-memory cache keyed by rounded coordinates (~11 km resolution)
# ---------------------------------------------------------------------------
_division_cache: Dict[str, Dict] = {}


def _cache_key(lat: float, lon: float) -> str:
    """Create cache key by rounding coords to 1 decimal."""
    return f"{round(lat, 1)},{round(lon, 1)}"


def _nominatim_reverse(lat: float, lon: float) -> Optional[Dict]:
    """Query Nominatim at zoom=5 (state/province level).

    Returns parsed JSON or None on failure.
    Nominatim policy: max 1 req/s, identify with User-Agent.
    """
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "jsonv2",
                    "zoom": 5,
                    "addressdetails": 1,
                },
                headers={"User-Agent": "DeepAgentsAtlas/1.0 (env-monitor)"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning(
            "Nominatim reverse geocode failed for %.4f,%.4f: %s",
            lat, lon, exc,
        )
        return None


def get_admin_division(
    lat: float,
    lon: float,
    google_api_key: str = "",
) -> Optional[Dict]:
    """Resolve any lat/lon to its top-level administrative division.

    Works worldwide. Returns::

        {
            "division_name": "Ontario" | "Wyoming" | "Ile-de-France",
            "division_code": "ON" | "WY" | "IDF",
            "country_code": "ca" | "us" | "fr",
            "country_name": "Canada" | "United States" | "France",
            "bounds": (south_lat, west_lon, north_lat, east_lon),
            "source": "us_fallback" | "nominatim" | "google",
            # Backward compat:
            "state_code": same as division_code,
            "state_name": same as division_name,
        }

    Returns None if location is in open ocean or unmapped.

    Strategy:
      1. Check in-memory cache.
      2. US: Google Geocoding (if key) -> bbox containment fallback.
      3. Non-US or US miss: Nominatim at zoom=5 (universal).
    """
    ck = _cache_key(lat, lon)
    if ck in _division_cache:
        return _division_cache[ck]

    result = None

    # --- Try Google reverse geocoding first (fastest, most accurate) ---
    if google_api_key:
        result = _try_google_geocode(lat, lon, google_api_key)

    # --- US bounding-box containment fallback (no API call) ---
    if not result:
        result = _try_us_bbox_fallback(lat, lon)

    # --- Nominatim: works for ALL countries worldwide ---
    if not result:
        result = _try_nominatim(lat, lon)

    if result:
        _division_cache[ck] = result
    return result


# Backward-compatible alias
get_state_from_coords = get_admin_division


def _try_google_geocode(lat: float, lon: float, api_key: str) -> Optional[Dict]:
    """Google Geocoding API for admin division detection."""
    try:
        params = {
            "latlng": f"{lat},{lon}",
            "key": api_key,
            "result_type": "administrative_area_level_1",
        }
        with httpx.Client(timeout=8) as client:
            resp = client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "OK" or not data.get("results"):
                return None

            result = data["results"][0]
            country_code = ""
            country_name = ""
            division_name = ""
            division_code = ""

            for comp in result.get("address_components", []):
                types = comp.get("types", [])
                if "country" in types:
                    country_code = comp.get("short_name", "").lower()
                    country_name = comp.get("long_name", "")
                if "administrative_area_level_1" in types:
                    division_code = comp.get("short_name", "")
                    division_name = comp.get("long_name", "")

            if not division_name:
                return None

            # US: use hardcoded precise bounds
            if country_code == "us" and division_code in US_STATE_BOUNDS:
                bounds = US_STATE_BOUNDS[division_code]
            else:
                # Use Google's viewport geometry
                geo = result.get("geometry", {})
                vp = geo.get("viewport", geo.get("bounds", {}))
                if vp:
                    ne = vp.get("northeast", {})
                    sw = vp.get("southwest", {})
                    bounds = (
                        sw.get("lat", lat - 1),
                        sw.get("lng", lon - 1),
                        ne.get("lat", lat + 1),
                        ne.get("lng", lon + 1),
                    )
                else:
                    bounds = (lat - 2, lon - 2, lat + 2, lon + 2)

            return _build_result(
                division_name, division_code,
                country_code, country_name, bounds, "google",
            )
    except Exception as exc:
        logger.warning("Google reverse geocode failed: %s", exc)
        return None


def _try_us_bbox_fallback(lat: float, lon: float) -> Optional[Dict]:
    """Fast US state detection using bounding-box containment."""
    for code, (s, w, n, e) in US_STATE_BOUNDS.items():
        if s <= lat <= n and w <= lon <= e:
            full_name = _US_CODE_TO_NAME.get(code, code)
            return _build_result(
                full_name, code, "us", "United States", (s, w, n, e), "us_fallback",
            )
    return None


def _try_nominatim(lat: float, lon: float) -> Optional[Dict]:
    """Nominatim reverse geocode -- universal, works for ANY country.

    Queries at zoom=5 which returns state/province/region level.
    Response ``boundingbox`` gives the admin division's spatial extent.
    """
    data = _nominatim_reverse(lat, lon)
    if not data:
        return None

    addr = data.get("address", {})
    # Nominatim uses different keys depending on country
    division_name = (
        addr.get("state")
        or addr.get("province")
        or addr.get("region")
        or addr.get("state_district")
        or addr.get("county")
        or ""
    )
    if not division_name:
        return None

    country_code = addr.get("country_code", "")
    country_name = addr.get("country", "")

    # Parse bounding box: Nominatim returns [south, north, west, east] as strings
    raw_bbox = data.get("boundingbox", [])
    if len(raw_bbox) >= 4:
        try:
            south = float(raw_bbox[0])
            north = float(raw_bbox[1])
            west = float(raw_bbox[2])
            east = float(raw_bbox[3])
            bounds: Tuple[float, float, float, float] = (south, west, north, east)
        except (ValueError, TypeError):
            bounds = (lat - 2, lon - 2, lat + 2, lon + 2)
    else:
        bounds = (lat - 2, lon - 2, lat + 2, lon + 2)

    division_code = _make_division_code(division_name)

    return _build_result(
        division_name, division_code,
        country_code, country_name, bounds, "nominatim",
    )


def _build_result(
    division_name: str,
    division_code: str,
    country_code: str,
    country_name: str,
    bounds: Tuple[float, float, float, float],
    source: str,
) -> Dict:
    """Build a standardized result dict with backward-compat fields."""
    s_lat, w_lon, n_lat, e_lon = bounds
    return {
        "division_name": division_name,
        "division_code": division_code,
        "country_code": country_code,
        "country_name": country_name,
        "bounds": bounds,
        "bbox_string": f"{w_lon:.2f},{s_lat:.2f},{e_lon:.2f},{n_lat:.2f}",
        "source": source,
        # Backward compatibility with old get_state_from_coords
        "state_code": division_code,
        "state_name": division_name,
        "code": division_code,
    }


def _make_division_code(name: str) -> str:
    """Generate a short code from an admin division name.

    Examples:
        'Ontario' -> 'ONT'
        'Ile-de-France' -> 'IDF'
        'New South Wales' -> 'NSW'
    """
    # CJK: take first 3 chars
    if any("\u4e00" <= c <= "\u9fff" or "\u3040" <= c <= "\u30ff" for c in name):
        clean = re.sub(r"[^\w]", "", name)
        return clean[:3].upper() if clean else name[:3].upper()
    # Latin: take first letter of each word
    words = re.split(r"[\s\-']+", name)
    if len(words) == 1:
        return name[:3].upper()
    code = "".join(w[0] for w in words if w).upper()
    return code[:4]


# ---------------------------------------------------------------------------
# Grid generation utilities
# ---------------------------------------------------------------------------

def generate_grid_points(
    bounds: Tuple[float, float, float, float],
    n_points: int = 9,
) -> List[Tuple[float, float]]:
    """Generate a grid of sample points within a bounding box.

    Args:
        bounds: (south_lat, west_lon, north_lat, east_lon)
        n_points: approximate number of grid points (nearest perfect square)

    Returns:
        List of (lat, lon) tuples in a roughly uniform grid.
    """
    s_lat, w_lon, n_lat, e_lon = bounds

    side = max(2, int(math.sqrt(n_points)))
    lat_step = (n_lat - s_lat) / (side + 1)
    lon_step = (e_lon - w_lon) / (side + 1)

    points = []
    for i in range(1, side + 1):
        for j in range(1, side + 1):
            p_lat = s_lat + i * lat_step
            p_lon = w_lon + j * lon_step
            points.append((round(p_lat, 4), round(p_lon, 4)))

    return points


def get_state_bbox_string(bounds) -> str:
    """Format bounding box as 'west_lon,south_lat,east_lon,north_lat'.

    Accepts either a (s_lat, w_lon, n_lat, e_lon) tuple or a US state code
    string (e.g. 'CA').
    """
    if isinstance(bounds, str):
        # Treat as US state code
        state_bounds = US_STATE_BOUNDS.get(bounds.upper())
        if not state_bounds:
            return ""
        bounds = state_bounds
    s_lat, w_lon, n_lat, e_lon = bounds
    return f"{w_lon:.2f},{s_lat:.2f},{e_lon:.2f},{n_lat:.2f}"
