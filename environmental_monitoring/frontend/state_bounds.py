"""
US State bounding boxes and reverse-geocode-to-state utility.

Used by the dashboard map to load state-level data for all data sources.
Bounding boxes are (south_lat, west_lon, north_lat, east_lon).
"""
import logging
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# US state bounding boxes: {state_code: (south_lat, west_lon, north_lat, east_lon)}
# Source: US Census Bureau TIGER shapefiles, rounded to 1 decimal
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


def get_state_from_coords(
    lat: float,
    lon: float,
    google_api_key: str = "",
) -> Optional[Dict]:
    """Reverse geocode lat/lon to determine the US state.

    Uses Google Geocoding API if key is available, otherwise falls back
    to bounding-box lookup.

    Returns dict with keys: state_code, state_name, bounds (south, west, north, east)
    or None if not in a US state.
    """
    # Try Google reverse geocoding first for accuracy
    if google_api_key:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{lat},{lon}",
                "key": google_api_key,
                "result_type": "administrative_area_level_1",
            }
            with httpx.Client(timeout=8) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") == "OK" and data.get("results"):
                    result = data["results"][0]
                    for comp in result.get("address_components", []):
                        types = comp.get("types", [])
                        if "administrative_area_level_1" in types:
                            state_code = comp.get("short_name", "")
                            state_name = comp.get("long_name", "")
                            if state_code in US_STATE_BOUNDS:
                                bounds = US_STATE_BOUNDS[state_code]
                                return {
                                    "state_code": state_code,
                                    "state_name": state_name,
                                    "bounds": bounds,
                                }
        except Exception as exc:
            logger.warning("Reverse geocode failed: %s", exc)

    # Fallback: simple bounding-box containment check
    for code, (s, w, n, e) in US_STATE_BOUNDS.items():
        if s <= lat <= n and w <= lon <= e:
            return {
                "state_code": code,
                "state_name": code,  # No full name available in fallback
                "bounds": (s, w, n, e),
            }

    return None


def generate_grid_points(
    bounds: Tuple[float, float, float, float],
    n_points: int = 9,
) -> List[Tuple[float, float]]:
    """Generate a grid of sample points within a bounding box.

    For state-level map coverage we want data from multiple locations
    across the state. Returns a list of (lat, lon) tuples arranged
    in a roughly uniform grid.

    Args:
        bounds: (south_lat, west_lon, north_lat, east_lon)
        n_points: approximate number of grid points (will be nearest square)
    """
    import math
    s_lat, w_lon, n_lat, e_lon = bounds

    # Calculate grid dimensions
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


def get_state_bbox_string(bounds: Tuple[float, float, float, float]) -> str:
    """Format bounding box as comma-separated string for API queries.

    Returns: 'west_lon,south_lat,east_lon,north_lat'
    """
    s_lat, w_lon, n_lat, e_lon = bounds
    return f"{w_lon:.2f},{s_lat:.2f},{e_lon:.2f},{n_lat:.2f}"
