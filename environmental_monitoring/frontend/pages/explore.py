"""
Explore Page - Data exploration with filtering and visualization.
"""
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time

from api_client import (
    get_sources, get_categories, get_location_data, get_category_data,
    proxy_request
)
from components.progress_box import create_progress_box, make_entry, render_entries
from components.charts import (
    create_time_series_chart,
    create_histogram,
    create_box_plot
)
from components.layout import (
    create_data_source_selector,
    create_time_range_selector
)
from data_processing import DataProcessor
from config import DATA_CATEGORIES, MAP_CONFIG, TIME_RANGES, API_BASE_URL


def create_explore_layout() -> html.Div:
    """Create the data exploration page layout."""
    return html.Div([
        # Page Header
        html.Div([
            html.H3("🔍 Data Exploration", className="mb-2"),
            html.P("Browse, filter, and visualize environmental data from 24+ sources", 
                   className="text-muted")
        ], className="mb-4"),
        
        # Data Source Selection
        create_data_source_selector(),
        
        # Time Range Selection - Simple Dropdown (uses global time range from sidebar)
        dbc.Card([
            dbc.CardHeader(html.H5("📅 Time Range", className="mb-0")),
            dbc.CardBody([
                dcc.Dropdown(
                    id="explore-time-range",
                    options=[
                        {"label": tr["label"], "value": tr["value"]}
                        for tr in TIME_RANGES if tr["value"] != "custom"
                    ],
                    value="7D",
                    clearable=False,
                    className="mb-2"
                ),
                html.Div(id="explore-time-display", className="text-muted small")
            ])
        ], className="mb-4"),
        
        # Location Filter
        dbc.Card([
            dbc.CardHeader(html.H5("📍 Location Filter", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Latitude"),
                        dbc.Input(id="explore-lat", type="number", step=0.0001, value=MAP_CONFIG["default_lat"])
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Longitude"),
                        dbc.Input(id="explore-lon", type="number", step=0.0001, value=MAP_CONFIG["default_lon"])
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Radius (km)"),
                        dbc.Input(id="explore-radius", type="number", value=50, min=1, max=500)
                    ], md=3),
                    dbc.Col([
                        dbc.Label(" ", className="d-block"),
                        dbc.Button([
                            html.I(className="fas fa-search me-2"),
                            "Search Location"
                        ], id="explore-search-btn", color="primary", className="w-100")
                    ], md=3)
                ])
            ])
        ], className="mb-4"),
        
        # Results Section
        dbc.Tabs([
            dbc.Tab([
                html.Div(id="explore-map-container", className="mt-3")
            ], label="📍 Map View", tab_id="map-tab"),
            
            dbc.Tab([
                html.Div(id="explore-table-container", className="mt-3")
            ], label="📋 Data Table", tab_id="table-tab"),
            
            dbc.Tab([
                html.Div(id="explore-charts-container", className="mt-3")
            ], label="📈 Charts", tab_id="charts-tab"),
            
            dbc.Tab([
                html.Div(id="explore-raw-container", className="mt-3")
            ], label="🔧 Raw Data", tab_id="raw-tab")
        ], id="explore-tabs", active_tab="map-tab", className="mb-4"),
        
        # Hidden store for data
        dcc.Store(id="explore-data-store"),
        
        # Loading indicator
        dcc.Loading(
            id="explore-loading",
            type="circle",
            children=html.Div(id="explore-loading-output")
        ),

        # ── Activity Log ──
        create_progress_box("explore", [
            "progress-explore-fetch",
        ]),
    ])


# ==================== TIME RANGE CALLBACK ====================

@callback(
    Output("explore-time-display", "children"),
    Input("explore-time-range", "value"),
    prevent_initial_call=False
)
def handle_explore_time_dropdown(selected_value):
    """Display selected time range."""
    time_labels = {
        "1H": "Last 1 Hour",
        "6H": "Last 6 Hours", 
        "24H": "Last 24 Hours",
        "7D": "Last 7 Days",
        "30D": "Last 30 Days",
        "90D": "Last 90 Days",
        "1Y": "Last Year"
    }
    return f"Selected: {time_labels.get(selected_value, selected_value)}"


@callback(
    Output("source-selector", "options"),
    [Input("source-category-filter", "value"),
     Input("explore-data-store", "data")],
    prevent_initial_call=False
)
def update_source_options(category, loaded_data):
    """Update available data sources based on category filter and loaded data."""
    options = []
    seen_ids = set()

    # First: add sources from loaded data so they appear in the list
    if loaded_data and isinstance(loaded_data, dict):
        for cat_id, sources_list in loaded_data.get("data", {}).items():
            if category and cat_id != category:
                continue
            if isinstance(sources_list, list):
                for source in sources_list:
                    if isinstance(source, dict) and source.get("success"):
                        src_id = source.get("source_id", source.get("source", ""))
                        src_name = source.get("source", src_id)
                        if src_id and src_id not in seen_ids:
                            seen_ids.add(src_id)
                            options.append({
                                "label": f"{src_name} ({cat_id}) [loaded]",
                                "value": src_id
                            })

    # Then: add available sources from the API registry
    try:
        sources = get_sources(category)
        source_list = sources.get("sources", [])
        for s in source_list:
            src_id = s.get("id", "")
            if src_id and src_id not in seen_ids:
                seen_ids.add(src_id)
                options.append({
                    "label": f"{s.get('name', 'Unknown')} ({s.get('category', 'N/A')})",
                    "value": src_id
                })
    except Exception:
        pass

    return options


@callback(
    Output("source-status-badges", "children"),
    Input("source-selector", "value"),
    prevent_initial_call=True
)
def update_source_badges(selected_sources):
    """Show status badges for selected sources."""
    if not selected_sources:
        return html.P("No sources selected", className="text-muted")
    
    badges = []
    for source_id in selected_sources:
        badges.append(
            dbc.Badge(
                [source_id, " ", html.I(className="fas fa-check-circle")],
                color="success",
                className="me-2"
            )
        )
    
    return html.Div(badges)


@callback(
    [Output("explore-data-store", "data"),
     Output("explore-loading-output", "children"),
     Output("progress-explore-fetch", "data")],
    [Input("explore-search-btn", "n_clicks"),
     Input("category-checklist", "value")],
    [State("explore-lat", "value"),
     State("explore-lon", "value"),
     State("explore-radius", "value"),
     State("source-selector", "value"),
     State("explore-time-range", "value")],
    prevent_initial_call=False
)
def fetch_exploration_data(n_clicks, categories, lat, lon, radius, sources, time_range):
    """Fetch data based on exploration filters. Auto-loads on page visit."""
    _t0 = time.time()
    lat = lat or MAP_CONFIG["default_lat"]
    lon = lon or MAP_CONFIG["default_lon"]
    
    # Convert time range to days for API
    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365
    }
    days = time_to_days.get(time_range, 7)
    
    try:
        # Get location data with time range
        result = get_location_data(lat, lon, radius_km=radius or 50, categories=categories)
        if isinstance(result, dict):
            result["selected_time_range"] = time_range
            result["selected_days"] = days

            # Backfill categories that are not location-based using category endpoints
            result.setdefault("data", {})
            if categories:
                for category in categories:
                    if category in result["data"]:
                        continue

                    cat_resp = get_category_data(category, lat=lat, lon=lon)
                    if isinstance(cat_resp, dict):
                        result["data"][category] = cat_resp.get("data", [])
        
        if result.get("error"):
            return None, dbc.Alert(f"Error: {result['error']}", color="danger"), [
                make_entry("error", f"API error: {str(result['error'])[:60]}"),
            ]
        
        # Count successful sources
        sources_count = 0
        records_count = 0
        _cat_progress = []
        
        if "data" in result:
            for category, sources_list in result.get("data", {}).items():
                _cat_sources = 0
                _cat_records = 0
                if isinstance(sources_list, list):
                    for source in sources_list:
                        if source.get("success"):
                            _cat_sources += 1
                            sources_count += 1
                            # Count records in data
                            source_data = source.get("data", {})
                            if isinstance(source_data, dict):
                                for dkey in ("features", "results", "fires", "observations",
                                             "stations", "records", "measurements"):
                                    dl = source_data.get(dkey, [])
                                    if isinstance(dl, list):
                                        _cat_records += len(dl)
                                        records_count += len(dl)
                                # Check for soil layers
                                layers = source_data.get("properties", {}).get("layers", [])
                                if layers:
                                    _cat_records += len(layers)
                                    records_count += len(layers)
                                # Check for timeseries/hourly/daily
                                for ts_key in ("hourly", "daily", "current", "current_weather"):
                                    ts = source_data.get(ts_key)
                                    if isinstance(ts, dict) and ts:
                                        n_vars = len([k for k in ts if k != "time"])
                                        _cat_records += n_vars
                                        records_count += n_vars
                                # USGS water
                                ts_list = source_data.get("value", {}).get("timeSeries", [])
                                if isinstance(ts_list, list) and ts_list:
                                    _cat_records += len(ts_list)
                                    records_count += len(ts_list)
                        else:
                            _err = source.get("error", "failed")
                            _cat_progress.append(make_entry(
                                "error",
                                f"{category}/{source.get('source', '?')}: {str(_err)[:50]}",
                            ))

                if _cat_sources > 0:
                    _cat_progress.append(make_entry(
                        "complete",
                        f"{category}: {_cat_sources} source(s), {_cat_records} records",
                    ))
                elif _cat_sources == 0 and isinstance(sources_list, list) and sources_list:
                    _cat_progress.append(make_entry(
                        "warning", f"{category}: all sources failed",
                    ))
        
        _elapsed = int((time.time() - _t0) * 1000)
        _prog = [
            make_entry("info", f"Exploring ({lat:.2f}, {lon:.2f}), radius {radius or 50} km"),
        ]
        _prog.extend(_cat_progress)
        _prog.append(make_entry(
            "complete",
            f"Total: {sources_count} sources, {records_count} records",
            duration_ms=_elapsed,
        ))
        _prog.append(make_entry("separator", ""))
        _prog.append(make_entry("success", "Exploration data loaded"))

        return result, dbc.Alert(
            f"\u2705 Found data from {sources_count} sources ({records_count} records)",
            color="success"
        ), _prog
        
    except Exception as e:
        return None, dbc.Alert(f"Error fetching data: {str(e)}", color="danger"), [
            make_entry("error", f"Fetch failed: {str(e)[:60]}"),
        ]


@callback(
    Output("explore-map-container", "children"),
    Input("explore-data-store", "data"),
    [State("explore-lat", "value"),
     State("explore-lon", "value")],
    prevent_initial_call=True
)
def update_explore_map(data, lat, lon):
    """Update the exploration map view."""
    if not data:
        return html.P("No data to display. Use the search above to explore data.", 
                      className="text-muted text-center py-5")
    
    center_lat = lat or MAP_CONFIG['default_lat']
    center_lon = lon or MAP_CONFIG['default_lon']

    # Extract location data for mapping
    map_data = []
    
    # Handle nested structure: data -> category -> list of sources -> source data
    for category, sources_list in data.get("data", {}).items():
        if isinstance(sources_list, list):
            for source in sources_list:
                if not source.get("success"):
                    continue
                    
                source_name = source.get("source", category)
                source_data = source.get("data", {})
                if not isinstance(source_data, dict):
                    continue

                # Handle GeoJSON features (e.g., earthquakes)
                if "features" in source_data:
                    for feature in source_data.get("features", [])[:50]:
                        geom = feature.get("geometry", {})
                        props = feature.get("properties", {})
                        if geom.get("type") == "Point" and geom.get("coordinates"):
                            coords = geom["coordinates"]
                            map_data.append({
                                "source": source_name,
                                "category": category,
                                "latitude": coords[1],
                                "longitude": coords[0],
                                "value": props.get("mag", props.get("title", "N/A"))
                            })
                
                # Handle current weather (single point)
                elif "current_weather" in source_data:
                    cw = source_data.get("current_weather", {})
                    if isinstance(cw, dict):
                        map_data.append({
                            "source": source_name,
                            "category": category,
                            "latitude": source_data.get("latitude", center_lat),
                            "longitude": source_data.get("longitude", center_lon),
                            "value": f"{cw.get('temperature', 'N/A')}\u00b0C"
                        })
                
                # Handle results array (biodiversity GBIF, OpenAQ, etc.)
                elif "results" in source_data:
                    for item in source_data.get("results", [])[:50]:
                        if isinstance(item, dict):
                            item_lat = item.get("decimalLatitude", item.get("latitude", item.get("lat")))
                            item_lon = item.get("decimalLongitude", item.get("longitude", item.get("lon")))
                            if item_lat and item_lon:
                                val = item.get("species", item.get("scientificName",
                                      item.get("value", item.get("name", "N/A"))))
                                map_data.append({
                                    "source": source_name,
                                    "category": category,
                                    "latitude": float(item_lat),
                                    "longitude": float(item_lon),
                                    "value": val
                                })

                # Handle NASA FIRMS fire points
                elif "fires" in source_data:
                    for fp in source_data.get("fires", [])[:50]:
                        if isinstance(fp, dict) and fp.get("latitude") and fp.get("longitude"):
                            try:
                                frp = float(fp.get("frp", fp.get("brightness", 0)) or 0)
                            except (ValueError, TypeError):
                                frp = 0
                            map_data.append({
                                "source": source_name,
                                "category": category,
                                "latitude": float(fp["latitude"]),
                                "longitude": float(fp["longitude"]),
                                "value": f"FRP {frp:.1f} MW"
                            })

                # Handle observations array (AirNow, marine)
                elif "observations" in source_data:
                    for obs in source_data.get("observations", [])[:30]:
                        if isinstance(obs, dict):
                            obs_lat = obs.get("Latitude", obs.get("latitude", obs.get("lat")))
                            obs_lon = obs.get("Longitude", obs.get("longitude", obs.get("lon")))
                            if obs_lat and obs_lon:
                                param = obs.get("ParameterName", obs.get("parameter", ""))
                                val = obs.get("AQI", obs.get("value", "N/A"))
                                map_data.append({
                                    "source": source_name,
                                    "category": category,
                                    "latitude": float(obs_lat),
                                    "longitude": float(obs_lon),
                                    "value": f"{param}: {val}" if param else str(val)
                                })

                # Handle USGS water timeSeries
                elif "value" in source_data and isinstance(source_data.get("value"), dict):
                    for ts in source_data["value"].get("timeSeries", [])[:15]:
                        if isinstance(ts, dict):
                            geo = ts.get("sourceInfo", {}).get("geoLocation", {})
                            slat = geo.get("latitude") or geo.get("geogLocation", {}).get("latitude")
                            slon = geo.get("longitude") or geo.get("geogLocation", {}).get("longitude")
                            if slat and slon:
                                site_name = ts.get("sourceInfo", {}).get("siteName", "Station")
                                map_data.append({
                                    "source": source_name,
                                    "category": category,
                                    "latitude": float(slat),
                                    "longitude": float(slon),
                                    "value": site_name[:30]
                                })

                # Handle soil data (SoilGrids) - pin at search location
                elif "properties" in source_data and "layers" in source_data.get("properties", {}):
                    layers = source_data["properties"]["layers"]
                    names = [ly.get("name", "?") for ly in layers[:3] if isinstance(ly, dict)]
                    map_data.append({
                        "source": source_name,
                        "category": category,
                        "latitude": center_lat,
                        "longitude": center_lon,
                        "value": f"Soil: {', '.join(names)}"
                    })

                # Handle hourly/daily data - pin at search location
                elif "hourly" in source_data or "daily" in source_data:
                    hourly = source_data.get("hourly", {})
                    daily = source_data.get("daily", {})
                    data_lat = source_data.get("latitude", center_lat)
                    data_lon = source_data.get("longitude", center_lon)
                    label_parts = []
                    if hourly:
                        n_vars = len([k for k in hourly if k != "time"])
                        label_parts.append(f"{n_vars} hourly vars")
                    if daily:
                        n_vars = len([k for k in daily if k != "time"])
                        label_parts.append(f"{n_vars} daily vars")
                    map_data.append({
                        "source": source_name,
                        "category": category,
                        "latitude": float(data_lat),
                        "longitude": float(data_lon),
                        "value": ", ".join(label_parts) if label_parts else "Time series data"
                    })

                # Handle current (Open-Meteo marine, radiation)
                elif "current" in source_data and isinstance(source_data.get("current"), dict):
                    cur = source_data["current"]
                    data_lat = source_data.get("latitude", center_lat)
                    data_lon = source_data.get("longitude", center_lon)
                    vals = [f"{k}: {v}" for k, v in cur.items() if k != "time" and v is not None]
                    map_data.append({
                        "source": source_name,
                        "category": category,
                        "latitude": float(data_lat),
                        "longitude": float(data_lon),
                        "value": "; ".join(vals[:3]) if vals else "Current data"
                    })

                # Handle stations (marine, radiation)
                elif "stations" in source_data:
                    for stn in source_data.get("stations", [])[:20]:
                        if isinstance(stn, dict):
                            slat = stn.get("latitude", stn.get("lat"))
                            slon = stn.get("longitude", stn.get("lon"))
                            if slat and slon:
                                map_data.append({
                                    "source": source_name,
                                    "category": category,
                                    "latitude": float(slat),
                                    "longitude": float(slon),
                                    "value": stn.get("name", stn.get("stationId", "Station"))
                                })

    if not map_data:
        # Just show the search location
        map_data = [{
            "source": "Search Location", "category": "search",
            "latitude": center_lat, "longitude": center_lon,
            "value": "Center"
        }]
    
    # Build Plotly Scattermapbox (no API key needed, uses OpenStreetMap tiles)
    # Group points by source for separate colored traces
    cat_colors = {
        "earthquakes": "#C73E1D", "wildfires": "#F18F01", "air_quality": "#2E86AB",
        "radiation": "#8F3F97", "marine": "#00B4D8", "biodiversity": "#2D6A4F",
        "weather": "#E9C46A", "water": "#0077B6", "climate": "#6C757D",
        "soil": "#BC6C25", "search": "#333333", "Search Location": "#333333",
    }

    by_source: dict = {}
    for pt in map_data:
        src = pt.get("source", "Unknown")
        by_source.setdefault(src, []).append(pt)

    # Per-source offsets to prevent stacking
    _OFFSETS = [
        (0.0, 0.0), (0.003, 0.002), (-0.003, 0.002),
        (0.002, -0.003), (-0.002, -0.003), (0.004, 0.0),
        (-0.004, 0.0), (0.0, 0.004), (0.003, -0.003),
        (-0.003, -0.003), (0.005, 0.003), (-0.005, 0.003),
    ]
    _source_names = list(by_source.keys())

    fig = go.Figure()
    for src_idx, source_name in enumerate(_source_names):
        points = by_source[source_name]
        dlat, dlon = _OFFSETS[src_idx % len(_OFFSETS)]
        lats = [p["latitude"] + dlat for p in points]
        lons = [p["longitude"] + dlon for p in points]
        texts = [f"{source_name}: {p.get('value', '')}" for p in points]
        # Use category color if available
        cat_for_color = points[0].get("category", source_name) if points else source_name
        color = cat_colors.get(cat_for_color, cat_colors.get(source_name, "#6C757D"))
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons, mode="markers",
            marker=dict(size=10, color=color, opacity=0.85),
            text=texts, hoverinfo="text",
            name=source_name.replace("_", " ").title(),
        ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6 if len(map_data) > 5 else 8,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.85)", font=dict(size=11),
        ),
    )

    map_component = dcc.Graph(
        figure=fig,
        config={"displayModeBar": True, "scrollZoom": True},
        style={"borderRadius": "8px", "overflow": "hidden"},
    )

    return html.Div([
        map_component,
        html.Div(f"{len(map_data)} data points", className="text-muted small mt-2")
    ])


@callback(
    Output("explore-table-container", "children"),
    Input("explore-data-store", "data"),
    prevent_initial_call=True
)
def update_explore_table(data):
    """Update the data table view."""
    if not data:
        return html.P("No data to display. Use the search above to explore data.", 
                      className="text-muted text-center py-5")
    
    tables = []
    
    # Handle nested structure: data -> category -> list of sources -> source data
    for category, sources_list in data.get("data", {}).items():
        if not isinstance(sources_list, list):
            continue
            
        for source in sources_list:
            if not source.get("success"):
                continue
                
            source_name = source.get("source", category)
            source_data = source.get("data", {})
            
            # Handle GeoJSON features (earthquakes)
            if "features" in source_data:
                features = source_data.get("features", [])[:20]
                if features:
                    rows = []
                    for f in features:
                        props = f.get("properties", {})
                        geom = f.get("geometry", {})
                        coords = geom.get("coordinates", [None, None, None])
                        rows.append({
                            "Magnitude": props.get("mag", "N/A"),
                            "Place": props.get("place", "N/A")[:50] if props.get("place") else "N/A",
                            "Time": props.get("time", "N/A"),
                            "Depth (km)": coords[2] if len(coords) > 2 else "N/A",
                            "Type": props.get("type", "N/A")
                        })
                    
                    df = pd.DataFrame(rows)
                    tables.append(html.Div([
                        html.H6(f"🌍 {source_name}", className="mt-3"),
                        dbc.Table.from_dataframe(
                            df.head(10),
                            striped=True, bordered=True, hover=True, responsive=True, size="sm"
                        )
                    ]))
            
            # Handle weather data
            elif "current_weather" in source_data:
                cw = source_data.get("current_weather", {})
                if isinstance(cw, dict):
                    df = pd.DataFrame([{
                        "Temperature (°C)": cw.get("temperature", "N/A"),
                        "Wind Speed (km/h)": cw.get("windspeed", "N/A"),
                        "Wind Direction (°)": cw.get("winddirection", "N/A"),
                        "Weather Code": cw.get("weathercode", "N/A"),
                        "Is Day": "Yes" if cw.get("is_day") else "No"
                    }])
                    tables.append(html.Div([
                        html.H6(f"🌤️ {source_name}", className="mt-3"),
                        dbc.Table.from_dataframe(
                            df,
                            striped=True, bordered=True, hover=True, responsive=True, size="sm"
                        )
                    ]))
            
            # Handle results array
            elif "results" in source_data:
                results = source_data.get("results", [])[:20]
                if results and isinstance(results[0], dict):
                    df = pd.DataFrame(results)
                    display_cols = [c for c in df.columns if c not in ["id", "_id", "raw"]][:8]
                    tables.append(html.Div([
                        html.H6(f"📊 {source_name}", className="mt-3"),
                        dbc.Table.from_dataframe(
                            df[display_cols].head(10),
                            striped=True, bordered=True, hover=True, responsive=True, size="sm"
                        )
                    ]))

            # Handle climate daily data (Open-Meteo Climate format)
            elif "daily" in source_data:
                daily = source_data.get("daily", {})
                times = daily.get("time", [])
                if times:
                    rows = []
                    t_max = daily.get("temperature_2m_max", [])
                    t_min = daily.get("temperature_2m_min", [])
                    precip = daily.get("precipitation_sum", [])
                    for i, t in enumerate(times[:30]):
                        row = {"Date": t}
                        if i < len(t_max) and t_max[i] is not None:
                            row["Max Temp (°C)"] = t_max[i]
                        if i < len(t_min) and t_min[i] is not None:
                            row["Min Temp (°C)"] = t_min[i]
                        if i < len(precip) and precip[i] is not None:
                            row["Precip (mm)"] = precip[i]
                        rows.append(row)
                    if rows:
                        df = pd.DataFrame(rows)
                        tables.append(html.Div([
                            html.H6(f"🌡️ {source_name}", className="mt-3"),
                            dbc.Table.from_dataframe(
                                df,
                                striped=True, bordered=True, hover=True, responsive=True, size="sm"
                            )
                        ]))

            # Handle soil layers (SoilGrids format)
            elif "properties" in source_data and "layers" in source_data.get("properties", {}):
                layers = source_data["properties"]["layers"]
                if isinstance(layers, list) and layers:
                    rows = []
                    for layer in layers:
                        if not isinstance(layer, dict):
                            continue
                        name = layer.get("name", "Unknown")
                        unit = layer.get("unit_measure", {}).get("mapped_units", "")
                        depths = layer.get("depths", [])
                        mean_val = None
                        depth_label = ""
                        if depths and isinstance(depths, list):
                            depth_label = depths[0].get("label", "")
                            mean_val = depths[0].get("values", {}).get("mean")
                        rows.append({
                            "Property": name,
                            "Value": mean_val if mean_val is not None else "N/A",
                            "Unit": unit,
                            "Depth": depth_label,
                        })
                    if rows:
                        df = pd.DataFrame(rows)
                        tables.append(html.Div([
                            html.H6(f"🌱 {source_name}", className="mt-3"),
                            dbc.Table.from_dataframe(
                                df,
                                striped=True, bordered=True, hover=True, responsive=True, size="sm"
                            )
                        ]))

            # Handle Open-Meteo hourly data (AQ, Marine, Radiation, Weather hourly)
            elif "hourly" in source_data:
                hourly = source_data.get("hourly") or {}
                times = hourly.get("time", [])
                if times and isinstance(hourly, dict):
                    rows = []
                    # Collect all numeric hourly columns
                    hourly_cols = [k for k in hourly if k != "time" and isinstance(hourly[k], list)]
                    for i, t in enumerate(times[:30]):
                        row = {"Time": t}
                        for col in hourly_cols[:6]:
                            vals = hourly[col]
                            if i < len(vals) and vals[i] is not None:
                                row[col.replace("_", " ").title()] = vals[i]
                        rows.append(row)
                    if rows:
                        df = pd.DataFrame(rows)
                        tables.append(html.Div([
                            html.H6(f"📈 {source_name}", className="mt-3"),
                            dbc.Table.from_dataframe(
                                df.head(15),
                                striped=True, bordered=True, hover=True, responsive=True, size="sm"
                            )
                        ]))

            # Handle Open-Meteo current data (single point)
            elif "current" in source_data:
                current = source_data.get("current") or {}
                if isinstance(current, dict) and len(current) > 1:
                    row = {}
                    for k, v in current.items():
                        if k in ("time", "interval"):
                            continue
                        row[k.replace("_", " ").title()] = v
                    if row:
                        df = pd.DataFrame([row])
                        tables.append(html.Div([
                            html.H6(f"📊 {source_name}", className="mt-3"),
                            dbc.Table.from_dataframe(
                                df,
                                striped=True, bordered=True, hover=True, responsive=True, size="sm"
                            )
                        ]))
    
    if not tables:
        api_links = []
        for cat in DATA_CATEGORIES:
            url = f"{API_BASE_URL}/api/v1/hub/category/{cat['id']}?lat={MAP_CONFIG['default_lat']}&lon={MAP_CONFIG['default_lon']}"
            api_links.append(html.Li(html.A(f"{cat['icon']} {cat['name']} raw data", href=url, target="_blank")))
        return html.Div([
            html.P("No tabular data available for the selected sources.", className="text-muted"),
            html.P("Explore raw API data:", className="fw-bold mt-3"),
            html.Ul(api_links)
        ])
    
    return html.Div(tables)


@callback(
    Output("explore-charts-container", "children"),
    Input("explore-data-store", "data"),
    prevent_initial_call=True
)
def update_explore_charts(data):
    """Update the charts view."""
    if not data:
        return html.P("No data to display. Use the search above to explore data.", 
                      className="text-muted text-center py-5")
    
    charts = []
    
    # Handle nested structure: data -> category -> list of sources -> source data
    for category, sources_list in data.get("data", {}).items():
        if not isinstance(sources_list, list):
            continue
            
        for source in sources_list:
            if not source.get("success"):
                continue
                
            source_name = source.get("source", category)
            source_data = source.get("data", {})
            
            # Handle earthquake magnitudes
            if "features" in source_data:
                features = source_data.get("features", [])
                if features:
                    magnitudes = [
                        f.get("properties", {}).get("mag") 
                        for f in features 
                        if f.get("properties", {}).get("mag") is not None
                    ]
                    if magnitudes:
                        fig = create_histogram(
                            magnitudes,
                            title=f"{source_name} - Earthquake Magnitudes",
                            x_title="Magnitude",
                            height=300
                        )
                        charts.append(
                            dbc.Col([dcc.Graph(figure=fig)], md=6, className="mb-3")
                        )
            
            # Handle weather data (create a simple bar chart)
            elif "current_weather" in source_data:
                cw = source_data.get("current_weather", {})
                if isinstance(cw, dict):
                    import plotly.graph_objects as go
                    fig = go.Figure(data=[
                        go.Bar(
                            x=["Temperature", "Wind Speed"],
                            y=[cw.get("temperature", 0), cw.get("windspeed", 0)],
                            marker_color=["#FF6B6B", "#4ECDC4"]
                        )
                    ])
                    fig.update_layout(
                        title=f"{source_name} - Current Conditions",
                        height=300,
                        showlegend=False
                    )
                    charts.append(
                        dbc.Col([dcc.Graph(figure=fig)], md=6, className="mb-3")
                    )
            
            # Handle results with numeric data
            elif "results" in source_data:
                results = source_data.get("results", [])
                if results and isinstance(results, list) and isinstance(results[0], dict):
                    df = pd.DataFrame(results)
                    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    
                    if numeric_cols:
                        col = numeric_cols[0]
                        fig = create_histogram(
                            df[col].dropna(),
                            title=f"{source_name} - {col}",
                            x_title=col,
                            height=300
                        )
                        charts.append(
                            dbc.Col([dcc.Graph(figure=fig)], md=6, className="mb-3")
                        )

            # Handle climate daily data (Open-Meteo Climate format)
            elif "daily" in source_data:
                daily = source_data.get("daily", {})
                times = daily.get("time", [])
                t_max = daily.get("temperature_2m_max", [])
                t_min = daily.get("temperature_2m_min", [])
                if times and (t_max or t_min):
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    if t_max:
                        fig.add_trace(go.Scatter(
                            x=times, y=t_max, name="Max Temp",
                            line=dict(color="#FF6B6B")
                        ))
                    if t_min:
                        fig.add_trace(go.Scatter(
                            x=times, y=t_min, name="Min Temp",
                            line=dict(color="#4ECDC4")
                        ))
                    fig.update_layout(
                        title=f"{source_name} - Daily Temperature",
                        yaxis_title="Temperature (°C)",
                        height=300
                    )
                    charts.append(
                        dbc.Col([dcc.Graph(figure=fig)], md=6, className="mb-3")
                    )

            # Handle soil layers (SoilGrids format)
            elif "properties" in source_data and "layers" in source_data.get("properties", {}):
                layers = source_data["properties"]["layers"]
                if isinstance(layers, list) and layers:
                    import plotly.graph_objects as go
                    names = []
                    vals = []
                    for layer in layers:
                        if not isinstance(layer, dict):
                            continue
                        name = layer.get("name", "Unknown")
                        depths = layer.get("depths", [])
                        if depths and isinstance(depths, list):
                            mean_val = depths[0].get("values", {}).get("mean")
                            if mean_val is not None:
                                names.append(name)
                                vals.append(float(mean_val))
                    if names:
                        fig = go.Figure(data=[
                            go.Bar(x=names, y=vals, marker_color="#8B4513")
                        ])
                        fig.update_layout(
                            title=f"{source_name} - Soil Properties",
                            yaxis_title="Value",
                            height=300
                        )
                        charts.append(
                            dbc.Col([dcc.Graph(figure=fig)], md=6, className="mb-3")
                        )

            # Handle Open-Meteo hourly data (AQ, Marine, Radiation, Weather)
            elif "hourly" in source_data:
                hourly = source_data.get("hourly") or {}
                times = hourly.get("time", [])
                if times and isinstance(hourly, dict):
                    import plotly.graph_objects as go
                    hourly_cols = [k for k in hourly if k != "time" and isinstance(hourly[k], list)]
                    if hourly_cols:
                        fig = go.Figure()
                        colors = ["#2E86AB", "#C73E1D", "#F18F01", "#28A745", "#8F3F97", "#17A2B8"]
                        for idx, col in enumerate(hourly_cols[:4]):
                            vals = hourly[col]
                            clean_times = times[:len(vals)]
                            fig.add_trace(go.Scatter(
                                x=clean_times, y=vals, mode="lines",
                                name=col.replace("_", " ").title(),
                                line=dict(color=colors[idx % len(colors)], width=2),
                            ))
                        fig.update_layout(
                            title=f"{source_name} - Hourly Data",
                            height=300,
                            legend=dict(orientation="h", y=-0.15),
                        )
                        charts.append(
                            dbc.Col([dcc.Graph(figure=fig)], md=6, className="mb-3")
                        )
    
    if not charts:
        return html.P("No chartable data available.", className="text-muted")
    
    return dbc.Row(charts)


@callback(
    Output("explore-raw-container", "children"),
    Input("explore-data-store", "data"),
    prevent_initial_call=True
)
def update_explore_raw(data):
    """Update the raw data view."""
    if not data:
        return html.P("No data to display. Use the search above to explore data.", 
                      className="text-muted text-center py-5")
    
    # Pretty print JSON
    raw_json = json.dumps(data, indent=2, default=str)
    
    return html.Div([
        dbc.Button([
            html.I(className="fas fa-copy me-2"),
            "Copy to Clipboard"
        ], id="copy-raw-btn", color="outline-primary", size="sm", className="mb-2"),
        html.Pre(
            raw_json,
            style={
                "maxHeight": "600px",
                "overflow": "auto",
                "backgroundColor": "#f8f9fa",
                "padding": "15px",
                "borderRadius": "5px",
                "fontSize": "12px"
            }
        )
    ])


# Quick data fetch callbacks for specific sources
@callback(
    Output("explore-data-store", "data", allow_duplicate=True),
    Input({"type": "quick-fetch", "index": ALL}, "n_clicks"),
    [State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=True
)
def quick_fetch_data(n_clicks, sidebar_lat, sidebar_lon):
    """Quick fetch for specific data types using sidebar coordinates."""
    if not ctx.triggered_id or not any(n_clicks):
        return None

    source_type = ctx.triggered_id["index"]
    lat = sidebar_lat or MAP_CONFIG["default_lat"]
    lon = sidebar_lon or MAP_CONFIG["default_lon"]

    try:
        # Use get_category_data for all data types
        if source_type in ["air_quality", "water_quality", "water", "weather", "marine",
                           "earthquakes", "radiation", "wildfires", "biodiversity",
                           "climate", "soil"]:
            return get_category_data(source_type, lat=lat, lon=lon)
        else:
            return None
    except Exception as e:
        return {"error": str(e)}


# ==================== PROGRESS BOX CALLBACKS ====================

@callback(
    Output("progress-entries-explore", "children"),
    Input("progress-explore-fetch", "data"),
    prevent_initial_call=False,
)
def render_explore_progress(fetch_prog):
    """Render the explore page activity log."""
    entries = []
    if fetch_prog:
        if isinstance(fetch_prog, list):
            entries.extend(fetch_prog)
        else:
            entries.append(fetch_prog)
    else:
        entries.append(make_entry("loading", "Waiting for data exploration request..."))
    return render_entries(entries)


@callback(
    [Output("progress-body-explore", "is_open"),
     Output("progress-icon-explore", "className")],
    Input("progress-toggle-explore", "n_clicks"),
    State("progress-body-explore", "is_open"),
    prevent_initial_call=True,
)
def toggle_explore_progress(n, is_open):
    """Toggle the explore progress box."""
    new_state = not is_open
    return new_state, "fas fa-chevron-up" if new_state else "fas fa-chevron-down"