"""
Google Data Commons Client for Frontend Dashboard

Synchronous client that queries Google Data Commons REST API V2
for environmental statistical observations. Data Commons aggregates
data from NOAA, EPA, World Bank, UN, Census Bureau, WHO, and more.

This client is used by the dashboard's central data loader so that
Data Commons data takes precedence over the backend API's data when
both sources cover the same category.

Docs: https://docs.datacommons.org/api/rest/v2/
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Commons REST V2 base URL and trial API key
# ---------------------------------------------------------------------------
DC_BASE_URL = "https://api.datacommons.org/v2"
DC_API_KEY = os.getenv(
    "DATA_COMMONS_API_KEY",
    "AIzaSyCTI4Xz-UW_G2Q2RfknhcfdAnTHq5X5XuI",  # public trial key
)
DC_TIMEOUT = float(os.getenv("DC_TIMEOUT", "15"))

# ---------------------------------------------------------------------------
# In-memory cache  (key -> (timestamp, data))
# ---------------------------------------------------------------------------
_cache: Dict[str, Tuple[float, Any]] = {}
CACHE_TTL = 600  # 10 minutes


def _cache_get(key: str) -> Optional[Any]:
    if key in _cache:
        ts, data = _cache[key]
        if (datetime.now().timestamp() - ts) < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (datetime.now().timestamp(), data)


# ---------------------------------------------------------------------------
# Low-level HTTP helpers
# ---------------------------------------------------------------------------

def _dc_get(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous GET to Data Commons V2."""
    params["key"] = DC_API_KEY
    url = f"{DC_BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=DC_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("DC GET %s failed: %s", endpoint, exc)
        return {}


def _dc_post(endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous POST to Data Commons V2."""
    url = f"{DC_BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=DC_TIMEOUT, follow_redirects=True) as client:
            resp = client.post(
                url,
                json=body,
                headers={"X-API-Key": DC_API_KEY},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("DC POST %s failed: %s", endpoint, exc)
        return {}


# ---------------------------------------------------------------------------
# Place resolution  (lat/lon -> DCID hierarchy)
# ---------------------------------------------------------------------------

def resolve_coordinates(lat: float, lon: float) -> List[Dict[str, str]]:
    """
    Resolve lat/lon to a hierarchy of Data Commons place DCIDs.

    Returns a list of dicts like:
        [{"dcid": "geoId/0649670", "type": "City"},
         {"dcid": "geoId/06085",   "type": "County"},
         {"dcid": "geoId/06",      "type": "State"},
         {"dcid": "country/USA",   "type": "Country"}]
    """
    cache_key = f"resolve:{lat:.2f}#{lon:.2f}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    coord_str = f"{lat:.2f}#{lon:.2f}"
    result = _dc_post("/resolve", {
        "nodes": [coord_str],
        "property": "<-geoCoordinate->dcid",
    })

    places: List[Dict[str, str]] = []
    for entity in result.get("entities", []):
        for cand in entity.get("candidates", []):
            dcid = cand.get("dcid", "")
            dtype = cand.get("dominantType", "")
            if dcid:
                places.append({"dcid": dcid, "type": dtype})

    _cache_set(cache_key, places)
    return places


def _best_place_dcid(
    places: List[Dict[str, str]],
    preferred_types: Optional[List[str]] = None,
) -> Optional[str]:
    """Pick the best DCID from a resolved set, preferring county or state."""
    if not places:
        return None
    if preferred_types is None:
        preferred_types = ["County", "State", "Country"]
    for ptype in preferred_types:
        for p in places:
            if p.get("type") == ptype:
                return p["dcid"]
    # fallback: first entry
    return places[0]["dcid"]


# ---------------------------------------------------------------------------
# Observation fetcher
# ---------------------------------------------------------------------------

def get_observations(
    entity_dcid: str,
    variable_dcids: List[str],
    date: str = "LATEST",
) -> Dict[str, Any]:
    """
    Fetch statistical observations from Data Commons.

    Args:
        entity_dcid: Place DCID (e.g. "geoId/06085")
        variable_dcids: List of statistical variable DCIDs
        date: "LATEST", a specific date, or "" for all dates

    Returns:
        Raw DC response dict with byVariable -> byEntity structure
    """
    cache_key = f"obs:{entity_dcid}:{','.join(sorted(variable_dcids))}:{date}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    body: Dict[str, Any] = {
        "date": date,
        "variable": {"dcids": variable_dcids},
        "entity": {"dcids": [entity_dcid]},
        "select": ["entity", "variable", "value", "date"],
    }

    result = _dc_post("/observation", body)
    _cache_set(cache_key, result)
    return result


def _extract_latest_value(
    obs_result: Dict[str, Any],
    variable_dcid: str,
    entity_dcid: str,
) -> Optional[Dict[str, Any]]:
    """Extract the latest observation {date, value, facet} for one variable."""
    by_var = obs_result.get("byVariable", {})
    var_data = by_var.get(variable_dcid, {})
    entity_data = var_data.get("byEntity", {}).get(entity_dcid, {})
    facets = entity_data.get("orderedFacets", [])
    if not facets:
        return None
    # First facet is typically the most authoritative
    first = facets[0]
    obs_list = first.get("observations", [])
    if obs_list:
        return {
            "date": obs_list[0].get("date"),
            "value": obs_list[0].get("value"),
            "facetId": first.get("facetId"),
        }
    return None


def _extract_time_series(
    obs_result: Dict[str, Any],
    variable_dcid: str,
    entity_dcid: str,
) -> List[Dict[str, Any]]:
    """Extract all observations for one variable as a time series."""
    by_var = obs_result.get("byVariable", {})
    var_data = by_var.get(variable_dcid, {})
    entity_data = var_data.get("byEntity", {}).get(entity_dcid, {})
    facets = entity_data.get("orderedFacets", [])
    if not facets:
        return []
    # Use the facet with the most observations
    best_facet = max(facets, key=lambda f: f.get("obsCount", 0))
    series = best_facet.get("observations", [])
    return [{"date": o["date"], "value": o["value"]} for o in series if "value" in o]


# ---------------------------------------------------------------------------
# Category-specific variable mappings
# ---------------------------------------------------------------------------

# Maps our 10 dashboard categories to Data Commons statistical variable DCIDs.
# Only categories with known DC coverage are listed.
CATEGORY_VARIABLES: Dict[str, List[Dict[str, str]]] = {
    "air_quality": [
        {"dcid": "Mean_Concentration_AirPollutant_PM2.5", "label": "PM2.5", "unit": "ug/m3"},
        {"dcid": "Mean_Concentration_AirPollutant_Ozone", "label": "Ozone", "unit": "ppb"},
        {"dcid": "AirQualityIndex_AirPollutant", "label": "AQI", "unit": ""},
        {"dcid": "Annual_Emissions_CarbonDioxide_NonBiogenic", "label": "CO2 (non-bio)", "unit": "metric tons"},
    ],
    "climate": [
        {"dcid": "Mean_Temperature", "label": "Mean Temperature", "unit": "C"},
        {"dcid": "Max_Temperature", "label": "Max Temperature", "unit": "C"},
        {"dcid": "Min_Temperature", "label": "Min Temperature", "unit": "C"},
        {"dcid": "Mean_Precipitation", "label": "Precipitation", "unit": "mm"},
        {"dcid": "Annual_Emissions_CarbonDioxide", "label": "CO2 Emissions", "unit": "metric tons"},
        {"dcid": "Annual_Emissions_GreenhouseGas", "label": "GHG Emissions", "unit": "metric tons CO2e"},
    ],
    "weather": [
        {"dcid": "Mean_Temperature", "label": "Mean Temperature", "unit": "C"},
        {"dcid": "Max_Temperature", "label": "Max Temperature", "unit": "C"},
        {"dcid": "Min_Temperature", "label": "Min Temperature", "unit": "C"},
        {"dcid": "Mean_Precipitation", "label": "Mean Precipitation", "unit": "mm"},
    ],
    "water": [
        {"dcid": "Mean_WaterTemperature", "label": "Water Temp", "unit": "C"},
        {"dcid": "Annual_Consumption_Water", "label": "Water Consumption", "unit": "gallons"},
    ],
    "radiation": [
        {"dcid": "Annual_Emissions_RadionuclidesInclRn_Land", "label": "Radionuclide Emissions (Land)", "unit": ""},
    ],
    "wildfires": [
        {"dcid": "Area_FireEvent", "label": "Fire Area", "unit": "acres"},
        {"dcid": "Count_FireEvent", "label": "Fire Count", "unit": ""},
    ],
    "biodiversity": [
        {"dcid": "Count_Species", "label": "Species Count", "unit": ""},
        {"dcid": "Count_Species_Endangered", "label": "Endangered Species", "unit": ""},
    ],
    "soil": [
        {"dcid": "Mean_SoilMoisture", "label": "Soil Moisture", "unit": "%"},
        {"dcid": "Mean_SoilTemperature", "label": "Soil Temperature", "unit": "C"},
    ],
}


# ---------------------------------------------------------------------------
# High-level category data fetcher
# ---------------------------------------------------------------------------

def get_dc_category_data(
    category_id: str,
    lat: float,
    lon: float,
) -> Dict[str, Any]:
    """
    Fetch Data Commons data for a dashboard category at a given location.

    Returns a dict shaped for merging into the dashboard's data pipeline:
    {
        "source": "data_commons",
        "place_dcid": "geoId/06085",
        "place_type": "County",
        "variables": {
            "PM2.5": {"value": 12.3, "date": "2023", "unit": "ug/m3", "dcid": "..."},
            ...
        },
        "time_series": {
            "PM2.5": [{"date": "2018", "value": 10.1}, ...],
            ...
        },
    }
    """
    var_defs = CATEGORY_VARIABLES.get(category_id)
    if not var_defs:
        return {}

    # 1) Resolve coordinates to place hierarchy
    places = resolve_coordinates(lat, lon)
    if not places:
        logger.info("DC: no places resolved for (%s, %s)", lat, lon)
        return {}

    # Prefer County for granular stats, fall back to State / Country
    dcid = _best_place_dcid(places, ["County", "State", "Country"])
    if not dcid:
        return {}

    place_type = next(
        (p["type"] for p in places if p["dcid"] == dcid), "Unknown"
    )

    # 2) Fetch latest observations for all variables in this category
    var_dcids = [v["dcid"] for v in var_defs]
    obs_latest = get_observations(dcid, var_dcids, date="LATEST")

    # 3) Also fetch full time-series (empty date = all dates)
    obs_all = get_observations(dcid, var_dcids, date="")

    # 4) Build result dict
    variables: Dict[str, Any] = {}
    time_series: Dict[str, List[Dict]] = {}

    for vdef in var_defs:
        vid = vdef["dcid"]
        label = vdef["label"]

        latest = _extract_latest_value(obs_latest, vid, dcid)
        if latest and latest.get("value") is not None:
            variables[label] = {
                "value": latest["value"],
                "date": latest.get("date"),
                "unit": vdef["unit"],
                "dcid": vid,
            }

        ts = _extract_time_series(obs_all, vid, dcid)
        if ts:
            time_series[label] = ts

    if not variables and not time_series:
        return {}

    return {
        "source": "data_commons",
        "place_dcid": dcid,
        "place_type": place_type,
        "variables": variables,
        "time_series": time_series,
    }


def get_dc_summary_for_category(
    category_id: str,
    dc_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a lightweight summary dict from DC data (for intersection graphs).
    Mirrors extract_category_summary() shape in dashboard.py.
    """
    variables = dc_data.get("variables", {})
    summary: Dict[str, Any] = {}

    if category_id == "air_quality":
        aqi = variables.get("AQI", {})
        if aqi:
            summary["us_aqi"] = aqi.get("value")
        pm25 = variables.get("PM2.5", {})
        if pm25:
            summary["pm25"] = pm25.get("value")

    elif category_id in ("weather", "climate"):
        temp = variables.get("Mean Temperature", {})
        if temp:
            summary["temperature_c"] = temp.get("value")

    return summary
