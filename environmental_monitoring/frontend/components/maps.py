"""
Google Maps components for Environmental Monitoring Dashboard.

Supports two modes:
1. Embed API - Simple iframes for basic map display
2. JavaScript API - Full interactive maps with markers, data layers, info windows

The JS API provides:
- AdvancedMarkerElement for custom markers
- Data Layers for GeoJSON visualization
- Info windows with environmental data popups
- Dynamic styling based on data values (AQI, earthquake magnitude, etc.)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote_plus

from dash import dcc, html

from config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_REGION


# ============================================================================
# Google Maps Embed API (Simple iframe-based maps)
# ============================================================================

def build_google_maps_embed_url(
    lat: float,
    lon: float,
    zoom: int = 10,
    maptype: str = "roadmap",
    query: Optional[str] = None,
    mode: str = "place",
    region: Optional[str] = None
) -> str:
    """
    Build a Google Maps Embed API URL.

    Docs: https://developers.google.com/maps/documentation/embed/embedding-map
    """
    if mode not in {"place", "view", "search"}:
        mode = "place"

    if query:
        q_value = quote_plus(query)
    else:
        q_value = quote_plus(f"{lat},{lon}")

    params = [
        f"key={GOOGLE_MAPS_API_KEY}",
        f"zoom={zoom}",
        f"maptype={maptype}",
    ]

    if mode == "place":
        params.append(f"q={q_value}")
    elif mode == "view":
        params.append(f"center={lat},{lon}")
    elif mode == "search":
        params.append(f"q={q_value}")

    if region:
        params.append(f"region={quote_plus(region)}")
    elif GOOGLE_MAPS_REGION:
        params.append(f"region={quote_plus(GOOGLE_MAPS_REGION)}")

    return f"https://www.google.com/maps/embed/v1/{mode}?" + "&".join(params)


def create_google_map_iframe(
    lat: float,
    lon: float,
    zoom: int = 10,
    height: int = 450,
    maptype: str = "roadmap",
    query: Optional[str] = None
) -> html.Div:
    """Create a Google Maps iframe for Dash layouts (Embed API)."""
    if not GOOGLE_MAPS_API_KEY:
        return html.Div(
            "Google Maps API key missing. Set GOOGLE_MAPS_API_KEY in the environment.",
            className="text-muted text-center py-4"
        )

    src = build_google_maps_embed_url(
        lat=lat,
        lon=lon,
        zoom=zoom,
        maptype=maptype,
        query=query,
        mode="place"
    )

    return html.Div(
        html.Iframe(
            src=src,
            width="100%",
            height=str(height),
            style={"border": 0},
            loading="lazy",
            referrerPolicy="no-referrer-when-downgrade",
            allowFullScreen=True,
        )
    )


# ============================================================================
# Google Maps JavaScript API (Full interactive maps)
# ============================================================================

def get_maps_js_api_script() -> html.Script:
    """
    Get the Google Maps JavaScript API script tag.
    
    Should be included in the page head or before the map div.
    Loads the 'maps' and 'marker' libraries for Advanced Markers.
    """
    if not GOOGLE_MAPS_API_KEY:
        return html.Div()
    
    # Load Maps JS API with marker library
    api_url = (
        f"https://maps.googleapis.com/maps/api/js"
        f"?key={GOOGLE_MAPS_API_KEY}"
        f"&libraries=marker"
        f"&loading=async"
        f"&callback=Function.prototype"
    )
    
    return html.Script(src=api_url, async_=True)


def create_interactive_map(
    map_id: str,
    lat: float = 37.7749,
    lon: float = -122.4194,
    zoom: int = 10,
    height: int = 500,
    width: str = "100%",
    category: str = "default",
    data_points: Optional[List[Dict[str, Any]]] = None,
    geojson_data: Optional[Union[Dict, str]] = None,
    show_controls: bool = True
) -> html.Div:
    """
    Create an interactive Google Maps JavaScript API map.
    
    This creates a div that will be initialized by JavaScript.
    The google_maps.js asset file handles the map initialization.
    
    Args:
        map_id: Unique ID for the map element
        lat: Initial center latitude
        lon: Initial center longitude
        zoom: Initial zoom level
        height: Map height in pixels
        width: Map width (CSS value)
        category: Data category for marker styling
        data_points: Optional list of data points to add as markers
        geojson_data: Optional GeoJSON data to display
        show_controls: Whether to show map controls
    
    Returns:
        Dash html.Div containing the map container
    """
    if not GOOGLE_MAPS_API_KEY:
        return html.Div(
            "Google Maps API key missing. Set GOOGLE_MAPS_API_KEY in the environment.",
            className="text-muted text-center py-4"
        )
    
    # Store configuration as data attributes for JavaScript to read
    map_config = {
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "category": category,
        "showControls": show_controls
    }
    
    # Create the map container
    map_container = html.Div(
        id=map_id,
        className="google-map-container",
        style={
            "width": width,
            "height": f"{height}px",
            "borderRadius": "8px",
            "overflow": "hidden"
        },
        **{"data-map-config": json.dumps(map_config)}
    )
    
    # Create initialization script
    init_script = f"""
    (function() {{
        // Wait for Google Maps API and our custom JS to load
        function initMap() {{
            if (typeof google === 'undefined' || typeof window.envMapAPI === 'undefined') {{
                setTimeout(initMap, 100);
                return;
            }}
            
            const config = {json.dumps(map_config)};
            window.envMapAPI.init('{map_id}', config.lat, config.lon, config.zoom).then(function(map) {{
                if (!map) return;
                
                // Add data points if provided
                const dataPoints = {json.dumps(data_points or [])};
                if (dataPoints.length > 0) {{
                    window.envMapAPI.addMarkers(dataPoints, config.category);
                }}
                
                // Load GeoJSON if provided
                const geojsonData = {json.dumps(geojson_data) if geojson_data else 'null'};
                if (geojsonData) {{
                    window.envMapAPI.loadGeoJson(geojsonData);
                }}
            }});
        }}
        
        // Start initialization
        if (document.readyState === 'complete') {{
            initMap();
        }} else {{
            window.addEventListener('load', initMap);
        }}
    }})();
    """
    
    return html.Div([
        map_container,
        html.Script(init_script)
    ])


def create_map_with_store(
    map_id: str,
    store_id: str,
    lat: float = 37.7749,
    lon: float = -122.4194,
    zoom: int = 10,
    height: int = 500,
    category: str = "default"
) -> html.Div:
    """
    Create an interactive map with a Dash Store for dynamic data updates.
    
    Use this when you need to update map data via callbacks.
    Store the data points in the dcc.Store and they will be rendered on the map.
    
    Args:
        map_id: Unique ID for the map element
        store_id: ID for the dcc.Store that holds map data
        lat: Initial center latitude
        lon: Initial center longitude
        zoom: Initial zoom level
        height: Map height in pixels
        category: Data category for marker styling
    
    Returns:
        Dash html.Div with map and store
    """
    if not GOOGLE_MAPS_API_KEY:
        return html.Div(
            "Google Maps API key missing. Set GOOGLE_MAPS_API_KEY in the environment.",
            className="text-muted text-center py-4"
        )
    
    map_config = {
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "category": category
    }
    
    # Map container
    map_container = html.Div(
        id=map_id,
        className="google-map-container",
        style={
            "width": "100%",
            "height": f"{height}px",
            "borderRadius": "8px",
            "overflow": "hidden"
        },
        **{"data-map-config": json.dumps(map_config)}
    )
    
    # Data store for dynamic updates
    data_store = dcc.Store(id=store_id, data={"dataPoints": [], "geojson": None})
    
    # JavaScript to watch store changes and update map
    update_script = f"""
    (function() {{
        let mapInitialized = false;
        
        function initMap() {{
            if (typeof google === 'undefined' || typeof window.envMapAPI === 'undefined') {{
                setTimeout(initMap, 100);
                return;
            }}
            
            const config = {json.dumps(map_config)};
            window.envMapAPI.init('{map_id}', config.lat, config.lon, config.zoom).then(function(map) {{
                if (!map) return;
                mapInitialized = true;
                
                // Set up MutationObserver to watch for store data changes
                const storeElement = document.getElementById('{store_id}');
                if (storeElement) {{
                    const observer = new MutationObserver(function(mutations) {{
                        mutations.forEach(function(mutation) {{
                            if (mutation.type === 'attributes' && mutation.attributeName === 'data') {{
                                updateMapData();
                            }}
                        }});
                    }});
                    
                    observer.observe(storeElement, {{ attributes: true }});
                    
                    // Initial data load
                    updateMapData();
                }}
            }});
        }}
        
        function updateMapData() {{
            if (!mapInitialized) return;
            
            const storeElement = document.getElementById('{store_id}');
            if (!storeElement) return;
            
            try {{
                const data = JSON.parse(storeElement.getAttribute('data') || '{{}}');
                const config = {json.dumps(map_config)};
                
                if (data.dataPoints && data.dataPoints.length > 0) {{
                    window.envMapAPI.addMarkers(data.dataPoints, config.category);
                }}
                
                if (data.geojson) {{
                    window.envMapAPI.loadGeoJson(data.geojson);
                }}
            }} catch (e) {{
                console.error('Error updating map data:', e);
            }}
        }}
        
        if (document.readyState === 'complete') {{
            initMap();
        }} else {{
            window.addEventListener('load', initMap);
        }}
    }})();
    """
    
    return html.Div([
        data_store,
        map_container,
        html.Script(update_script)
    ])


# ============================================================================
# Data Commons Web Components Integration
# ============================================================================

def create_datacommons_map(
    header: str,
    parent_place: str,
    child_place_type: str,
    variable: str,
    date: Optional[str] = None,
    colors: Optional[List[str]] = None,
    allow_zoom: bool = True,
    height: int = 400
) -> html.Div:
    """
    Create a Data Commons map web component.
    
    Uses Google Data Commons to visualize statistical variables on a choropleth map.
    Docs: https://docs.datacommons.org/api/web_components/map
    
    Args:
        header: Chart title
        parent_place: Parent place DCID (e.g., "country/USA")
        child_place_type: Type of child places (e.g., "State", "County")
        variable: Statistical variable DCID
        date: Optional specific date (ISO 8601)
        colors: Optional custom color scale (up to 3 colors)
        allow_zoom: Whether to enable zoom controls
        height: Chart height in pixels
    
    Returns:
        Dash html.Div containing the Data Commons web component
    """
    # Build attributes
    attrs = {
        "header": header,
        "parentPlace": parent_place,
        "childPlaceType": child_place_type,
        "variable": variable
    }
    
    if date:
        attrs["date"] = date
    
    if colors:
        attrs["colors"] = " ".join(colors)
    
    if allow_zoom:
        attrs["allowZoom"] = "true"
    
    # Create the custom element as HTML string
    attrs_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    dc_map_html = f'<datacommons-map {attrs_str}></datacommons-map>'
    
    return html.Div([
        # Data Commons script
        html.Script(src="https://datacommons.org/datacommons.js"),
        # The web component
        html.Div(
            dangerouslySetInnerHTML={"__html": dc_map_html},
            style={"height": f"{height}px"}
        )
    ])


def create_datacommons_line(
    header: str,
    place: Union[str, List[str]],
    variables: Union[str, List[str]],
    height: int = 400
) -> html.Div:
    """
    Create a Data Commons line chart web component.
    
    Args:
        header: Chart title
        place: Place DCID(s)
        variables: Statistical variable DCID(s)
        height: Chart height in pixels
    
    Returns:
        Dash html.Div containing the Data Commons web component
    """
    places = place if isinstance(place, str) else ",".join(place)
    vars_str = variables if isinstance(variables, str) else ",".join(variables)
    
    dc_html = f'''
    <datacommons-line
        header="{header}"
        place="{places}"
        variables="{vars_str}">
    </datacommons-line>
    '''
    
    return html.Div([
        html.Script(src="https://datacommons.org/datacommons.js"),
        html.Div(
            dangerouslySetInnerHTML={"__html": dc_html},
            style={"height": f"{height}px"}
        )
    ])


def create_datacommons_bar(
    header: str,
    places: List[str],
    variables: Union[str, List[str]],
    height: int = 400
) -> html.Div:
    """
    Create a Data Commons bar chart web component.
    
    Args:
        header: Chart title
        places: List of place DCIDs
        variables: Statistical variable DCID(s)
        height: Chart height in pixels
    
    Returns:
        Dash html.Div containing the Data Commons web component
    """
    places_str = ",".join(places)
    vars_str = variables if isinstance(variables, str) else ",".join(variables)
    
    dc_html = f'''
    <datacommons-bar
        header="{header}"
        places="{places_str}"
        variables="{vars_str}">
    </datacommons-bar>
    '''
    
    return html.Div([
        html.Script(src="https://datacommons.org/datacommons.js"),
        html.Div(
            dangerouslySetInnerHTML={"__html": dc_html},
            style={"height": f"{height}px"}
        )
    ])