"""
Explore Page - Data exploration with filtering and visualization.
"""
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta
import json

from api_client import (
    get_sources, get_categories, get_location_data, get_category_data,
    proxy_request, get_air_quality, get_water_quality, get_weather, get_marine_data
)
from components.charts import (
    create_time_series_chart,
    create_histogram,
    create_box_plot,
    create_mapbox_scatter
)
from components.layout import (
    create_data_source_selector,
    create_time_range_selector
)
from data_processing import DataProcessor
from config import DATA_CATEGORIES, MAP_CONFIG, TIME_RANGES


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
        
        # Time Range Selection - Simplified inline version
        dbc.Card([
            dbc.CardHeader(html.H5("📅 Time Range", className="mb-0")),
            dbc.CardBody([
                dbc.ButtonGroup([
                    dbc.Button(tr["label"], id=f"explore-time-{tr['value']}", 
                              color="outline-primary" if tr["value"] != "7D" else "primary", 
                              size="sm", className="me-1")
                    for tr in TIME_RANGES if tr["value"] != "custom"
                ], className="mb-3 flex-wrap"),
                dcc.Store(id="explore-time-range", data="7D"),
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
                        dbc.Input(id="explore-lat", type="number", value=37.7749, step=0.0001)
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Longitude"),
                        dbc.Input(id="explore-lon", type="number", value=-122.4194, step=0.0001)
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
        )
    ])


# ==================== TIME RANGE CALLBACKS ====================

@callback(
    [Output("explore-time-range", "data"),
     Output("explore-time-display", "children"),
     Output("explore-time-1H", "color"),
     Output("explore-time-6H", "color"),
     Output("explore-time-24H", "color"),
     Output("explore-time-7D", "color"),
     Output("explore-time-30D", "color"),
     Output("explore-time-90D", "color"),
     Output("explore-time-1Y", "color")],
    [Input("explore-time-1H", "n_clicks"),
     Input("explore-time-6H", "n_clicks"),
     Input("explore-time-24H", "n_clicks"),
     Input("explore-time-7D", "n_clicks"),
     Input("explore-time-30D", "n_clicks"),
     Input("explore-time-90D", "n_clicks"),
     Input("explore-time-1Y", "n_clicks")],
    prevent_initial_call=False
)
def handle_explore_time_buttons(*args):
    """Handle time range button clicks for explore page."""
    button_ids = ["1H", "6H", "24H", "7D", "30D", "90D", "1Y"]
    time_labels = {
        "1H": "Last 1 Hour",
        "6H": "Last 6 Hours", 
        "24H": "Last 24 Hours",
        "7D": "Last 7 Days",
        "30D": "Last 30 Days",
        "90D": "Last 90 Days",
        "1Y": "Last Year"
    }
    
    # Default to 7D
    selected = "7D"
    
    if ctx.triggered_id:
        triggered = ctx.triggered_id.replace("explore-time-", "")
        if triggered in button_ids:
            selected = triggered
    
    # Set button colors
    colors = ["primary" if bid == selected else "outline-primary" for bid in button_ids]
    display_text = f"Selected: {time_labels.get(selected, selected)}"
    
    return [selected, display_text] + colors


@callback(
    Output("source-selector", "options"),
    Input("source-category-filter", "value"),
    prevent_initial_call=False
)
def update_source_options(category):
    """Update available data sources based on category filter."""
    try:
        sources = get_sources(category)
        source_list = sources.get("sources", [])
        
        return [
            {"label": f"{s.get('name', 'Unknown')} ({s.get('category', 'N/A')})", 
             "value": s.get("id", "")}
            for s in source_list
        ]
    except Exception:
        return []


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
     Output("explore-loading-output", "children")],
    Input("explore-search-btn", "n_clicks"),
    [State("explore-lat", "value"),
     State("explore-lon", "value"),
     State("explore-radius", "value"),
     State("source-selector", "value"),
     State("category-checklist", "value"),
     State("explore-time-range", "data")],
    prevent_initial_call=True
)
def fetch_exploration_data(n_clicks, lat, lon, radius, sources, categories, time_range):
    """Fetch data based on exploration filters."""
    if lat is None or lon is None:
        return None, dbc.Alert("Please enter valid coordinates", color="warning")
    
    # Convert time range to days for API
    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365
    }
    days = time_to_days.get(time_range, 7)
    
    try:
        # Get location data with time range
        result = get_location_data(lat, lon, radius_km=radius or 50, categories=categories)
        
        if result.get("error"):
            return None, dbc.Alert(f"Error: {result['error']}", color="danger")
        
        # Count successful sources
        sources_count = 0
        records_count = 0
        
        if "data" in result:
            for category, sources_list in result.get("data", {}).items():
                if isinstance(sources_list, list):
                    for source in sources_list:
                        if source.get("success"):
                            sources_count += 1
                            # Count records in data
                            source_data = source.get("data", {})
                            if isinstance(source_data, dict):
                                if "features" in source_data:
                                    records_count += len(source_data.get("features", []))
                                elif "results" in source_data:
                                    records_count += len(source_data.get("results", []))
        
        return result, dbc.Alert(
            f"✅ Found data from {sources_count} sources ({records_count} records)",
            color="success"
        )
        
    except Exception as e:
        return None, dbc.Alert(f"Error fetching data: {str(e)}", color="danger")


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
                
                # Handle GeoJSON features (e.g., earthquakes)
                if "features" in source_data:
                    for feature in source_data.get("features", [])[:50]:
                        geom = feature.get("geometry", {})
                        props = feature.get("properties", {})
                        if geom.get("type") == "Point" and geom.get("coordinates"):
                            coords = geom["coordinates"]
                            map_data.append({
                                "source": source_name,
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
                            "latitude": source_data.get("latitude", lat),
                            "longitude": source_data.get("longitude", lon),
                            "value": f"{cw.get('temperature', 'N/A')}°C"
                        })
                
                # Handle results array
                elif "results" in source_data:
                    for item in source_data.get("results", [])[:50]:
                        if isinstance(item, dict):
                            item_lat = item.get("latitude", item.get("lat"))
                            item_lon = item.get("longitude", item.get("lon"))
                            if item_lat and item_lon:
                                map_data.append({
                                    "source": source_name,
                                    "latitude": item_lat,
                                    "longitude": item_lon,
                                    "value": item.get("value", item.get("name", "N/A"))
                                })
    
    if not map_data:
        # Just show the search location
        map_data = [{"source": "Search Location", "latitude": lat, "longitude": lon, "value": "Center"}]
    
    fig = create_mapbox_scatter(
        map_data,
        lat_col="latitude",
        lon_col="longitude",
        color_col="source",
        hover_cols=["source", "value"],
        title="Environmental Data Points",
        center_lat=lat or 37.7749,
        center_lon=lon or -122.4194,
        zoom=8,
        height=500
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": True})


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
    
    if not tables:
        return html.P("No tabular data available for the selected sources.", 
                      className="text-muted")
    
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
    prevent_initial_call=True
)
def quick_fetch_data(n_clicks):
    """Quick fetch for specific data types."""
    if not ctx.triggered_id or not any(n_clicks):
        return None
    
    source_type = ctx.triggered_id["index"]
    
    try:
        if source_type == "air_quality":
            return get_air_quality(country="US")
        elif source_type == "water_quality":
            return get_water_quality(state_code="CA")
        elif source_type == "weather":
            return get_weather(37.7749, -122.4194)
        elif source_type == "marine":
            return get_marine_data(station_id="46026")
        else:
            return None
    except Exception as e:
        return {"error": str(e)}
