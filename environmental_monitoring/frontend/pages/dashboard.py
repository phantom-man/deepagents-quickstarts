"""
Dashboard Page - Main overview with key metrics and visualizations.

Reactive Design Pattern:
- Central dcc.Store holds all loaded data
- Search button, category checklist, and time range all trigger data reload
- Map and graphs update reactively from the data store
- Filter bar shows current selections visually
"""
from dash import html, dcc, callback, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
from datetime import datetime
from typing import Dict, Any, List

from api_client import (
    get_hub_info, get_sources, quick_check, get_health, get_category_data
)
from components.charts import create_aqi_gauge, create_mapbox_scatter
from components.graphs import get_graph_for_category, create_intersection_graph
from components.layout import create_stats_cards
from config import DATA_CATEGORIES, MAP_CONFIG


def create_dashboard_layout() -> html.Div:
    """Create the main dashboard page layout with reactive data loading."""
    return html.Div([
        # === Central Data Store - triggers on location/category/time changes ===
        dcc.Store(id="dashboard-data-store", data={}),
        dcc.Store(id="loaded-category-data", data={}),
        
        # === Initial Load Trigger - fires once after page renders ===
        dcc.Interval(id="initial-load-trigger", interval=500, n_intervals=0, max_intervals=1),
        
        # === Filter Status Bar - shows current selections ===
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-filter me-2"),
                            html.Strong("Active Filters: "),
                            html.Span(id="filter-location-display", className="badge bg-primary me-2"),
                            html.Span(id="filter-time-display", className="badge bg-info me-2"),
                            html.Span(id="filter-categories-display", className="badge bg-success"),
                        ], className="d-flex align-items-center flex-wrap")
                    ], md=10),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-sync-alt me-1"), "Reload All"],
                            id="reload-all-data-btn",
                            color="outline-primary",
                            size="sm"
                        )
                    ], md=2, className="text-end")
                ])
            ], className="py-2")
        ], className="mb-3 filter-status-bar"),
        
        # Stats Cards Row
        html.Div(id="dashboard-stats-row"),
        
        # Quick Check Panel
        dbc.Card([
            dbc.CardHeader([
                html.H5("⚡ Quick Environmental Check", className="mb-0"),
                dbc.Spinner(
                    html.Span(id="loading-indicator", className="text-muted small"),
                    size="sm",
                    color="primary"
                )
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Latitude"),
                        dbc.Input(id="quick-check-lat", type="number", value=37.7749, step=0.0001)
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Longitude"),
                        dbc.Input(id="quick-check-lon", type="number", value=-122.4194, step=0.0001)
                    ], md=3),
                    dbc.Col([
                        dbc.Label(" ", className="d-block"),
                        dbc.Button(
                            [html.I(className="fas fa-search me-1"), "Check Location"],
                            id="quick-check-btn",
                            color="primary"
                        )
                    ], md=2),
                    dbc.Col([
                        html.Div(id="quick-check-status", className="mt-4")
                    ], md=4)
                ])
            ])
        ], className="mb-4"),
        
        # Main Content Row - Map and Current Conditions
        dbc.Row([
            # Map Column (larger)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🗺️ Environmental Data Map", className="mb-0"),
                        html.Small(id="map-data-count", className="text-muted")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id="dashboard-map", style={"height": "450px"}),
                            type="circle"
                        )
                    ])
                ])
            ], md=8),
            
            # AQI and Weather Column
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("🌡️ Current Conditions", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="aqi-gauge-container"),
                        html.Hr(),
                        html.Div(id="weather-summary-container")
                    ])
                ])
            ], md=4)
        ], className="mb-4"),
        
        # Dynamic Category Graphs Section
        dbc.Card([
            dbc.CardHeader([
                html.H5("📊 Data Visualizations", className="mb-0"),
                html.Small("Select categories in sidebar to view graphs", className="text-muted")
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dcc.Loading(
                    html.Div(id="category-graphs-container"),
                    type="default"
                )
            ])
        ], className="mb-4"),
        
        # Intersection Graph (shows when 2+ compatible categories selected)
        html.Div(id="intersection-graph-container", className="mb-4"),
        
        # Data Categories Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("📈 Data Categories", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="categories-summary-container")
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🌐 Data Sources Status", className="mb-0"),
                        dbc.Button("View All", href="/explore", color="link", size="sm")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="data-sources-status-container")
                    ])
                ])
            ], md=6)
        ])
    ])


# ==================== FILTER STATUS BAR CALLBACKS ====================

@callback(
    [Output("filter-location-display", "children"),
     Output("filter-time-display", "children"),
     Output("filter-categories-display", "children")],
    [Input("quick-check-lat", "value"),
     Input("quick-check-lon", "value"),
     Input("selected-time-range", "data"),
     Input("category-checklist", "value")],
    prevent_initial_call=False
)
def update_filter_display(lat, lon, time_range, categories):
    """Update the filter status bar to show current selections."""
    lat = lat or 37.7749
    lon = lon or -122.4194
    time_range = time_range or "7D"
    categories = categories or []
    
    location_text = f"📍 {lat:.2f}, {lon:.2f}"
    time_text = f"📅 {time_range}"
    cat_text = f"📊 {len(categories)} categories"
    
    return location_text, time_text, cat_text


# ==================== CENTRAL DATA LOADING CALLBACK ====================

@callback(
    Output("loaded-category-data", "data"),
    [Input("quick-check-btn", "n_clicks"),
     Input("search-btn", "n_clicks"),
     Input("category-checklist", "value"),
     Input("reload-all-data-btn", "n_clicks"),
     Input("initial-load-trigger", "n_intervals")],
    [State("quick-check-lat", "value"),
     State("quick-check-lon", "value"),
     State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=False
)
def load_all_category_data(quick_clicks, search_clicks, categories, reload_clicks, n_intervals,
                           quick_lat, quick_lon, sidebar_lat, sidebar_lon):
    """
    Central data loading callback - triggers on:
    - Quick check button
    - Search button (sidebar)
    - Category selection changes
    - Reload all button
    - Initial page load (via interval)
    
    Loads data for all selected categories and stores in dcc.Store.
    """
    # Determine which location to use
    triggered = ctx.triggered_id
    
    if triggered == "search-btn":
        lat = sidebar_lat or 37.7749
        lon = sidebar_lon or -122.4194
    else:
        lat = quick_lat or 37.7749
        lon = quick_lon or -122.4194
    
    # Use default categories if none provided (for initial load)
    if not categories:
        categories = ["air_quality", "weather", "earthquakes", "radiation", "climate", "soil"]
    
    loaded_data = {
        "location": {"lat": lat, "lon": lon},
        "timestamp": datetime.now().isoformat(),
        "categories": {}
    }
    
    # Load data for each selected category
    for cat_id in categories:
        try:
            cat_data = get_category_data(cat_id, lat, lon)
            # Extract the actual data from sources
            sources = cat_data.get("sources", [])
            combined_data = {}
            
            for source in sources:
                if source.get("status") == "available":
                    source_data = source.get("data", {})
                    # Merge source data
                    for key, value in source_data.items():
                        if key not in combined_data:
                            combined_data[key] = value
                        elif isinstance(value, list) and isinstance(combined_data[key], list):
                            combined_data[key].extend(value)
            
            loaded_data["categories"][cat_id] = combined_data
            
        except Exception as e:
            loaded_data["categories"][cat_id] = {"error": str(e)}
    
    return loaded_data


# ==================== MAP UPDATE CALLBACK ====================

@callback(
    [Output("dashboard-map", "figure"),
     Output("map-data-count", "children")],
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_dashboard_map(loaded_data):
    """Update the map with loaded category data."""
    import plotly.graph_objects as go
    
    location = loaded_data.get("location", {}) if loaded_data else {}
    lat = location.get("lat", MAP_CONFIG["default_lat"])
    lon = location.get("lon", MAP_CONFIG["default_lon"])
    categories_data = loaded_data.get("categories", {}) if loaded_data else {}
    
    fig = go.Figure()
    total_points = 0
    
    # Add main location marker
    fig.add_trace(go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=dict(size=18, color="red", symbol="circle"),
        text=["📍 Selected Location"],
        hoverinfo="text",
        name="Location"
    ))
    
    # Category styles
    cat_styles = {
        "earthquakes": {"color": "#FF6B35", "icon": "🌍"},
        "wildfires": {"color": "#FF4500", "icon": "🔥"},
        "air_quality": {"color": "#4CAF50", "icon": "💨"},
        "weather": {"color": "#2196F3", "icon": "⛅"},
        "water": {"color": "#00BCD4", "icon": "💧"},
        "marine": {"color": "#3F51B5", "icon": "🌊"},
        "radiation": {"color": "#9C27B0", "icon": "☢️"},
        "biodiversity": {"color": "#8BC34A", "icon": "🦋"},
        "climate": {"color": "#FF9800", "icon": "🌡️"},
        "soil": {"color": "#795548", "icon": "🌱"}
    }
    
    # Plot data points for each category
    for cat_id, data in categories_data.items():
        if not data or "error" in data:
            continue
            
        style = cat_styles.get(cat_id, {"color": "gray", "icon": "📍"})
        lats, lons, texts = [], [], []
        
        # Handle different data structures
        if cat_id == "earthquakes":
            for f in data.get("features", [])[:30]:
                coords = f.get("geometry", {}).get("coordinates", [])
                props = f.get("properties", {})
                if len(coords) >= 2:
                    lons.append(coords[0])
                    lats.append(coords[1])
                    texts.append(f"{style['icon']} M{props.get('mag', '?')} - {props.get('place', 'Unknown')[:30]}")
        
        elif cat_id == "wildfires":
            for inc in data.get("incidents", [])[:30]:
                if inc.get("latitude") and inc.get("longitude"):
                    lats.append(inc["latitude"])
                    lons.append(inc["longitude"])
                    texts.append(f"{style['icon']} {inc.get('title', 'Fire')[:35]}")
        
        elif cat_id == "radiation":
            for m in data.get("measurements", [])[:30]:
                if m.get("latitude") and m.get("longitude"):
                    lats.append(m["latitude"])
                    lons.append(m["longitude"])
                    texts.append(f"{style['icon']} {m.get('value', '?')} {m.get('unit', 'cpm')}")
        
        elif cat_id == "biodiversity":
            for r in data.get("results", [])[:30]:
                dlat = r.get("decimalLatitude")
                dlon = r.get("decimalLongitude")
                if dlat and dlon:
                    lats.append(dlat)
                    lons.append(dlon)
                    texts.append(f"{style['icon']} {r.get('species', 'Unknown')[:25]}")
        
        elif cat_id == "marine":
            for s in data.get("stations", [])[:20]:
                slat = s.get("latitude", s.get("lat"))
                slon = s.get("longitude", s.get("lon"))
                if slat and slon:
                    lats.append(float(slat))
                    lons.append(float(slon))
                    texts.append(f"{style['icon']} {s.get('name', 'Buoy')[:20]}")
        
        # Add trace if we have points
        if lats and lons:
            total_points += len(lats)
            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode="markers",
                marker=dict(size=10, color=style["color"], opacity=0.8),
                text=texts,
                hoverinfo="text",
                name=f"{style['icon']} {cat_id.replace('_', ' ').title()}"
            ))
    
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=lat, lon=lon),
            zoom=6
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    count_text = f"{total_points} data points" if total_points > 0 else "No data loaded"
    
    return fig, count_text


# ==================== CATEGORY GRAPHS CALLBACK ====================

@callback(
    Output("category-graphs-container", "children"),
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_category_graphs(loaded_data):
    """Generate individualized graphs for each selected category."""
    if not loaded_data:
        return html.P("Select categories in the sidebar to view data visualizations.", 
                     className="text-muted text-center py-4")
    
    categories_data = loaded_data.get("categories", {})
    
    if not categories_data:
        return html.P("No categories selected. Check the sidebar to enable data sources.", 
                     className="text-muted text-center py-4")
    
    # Create a graph card for each category
    graph_cards = []
    
    for cat_id, data in categories_data.items():
        if not data or "error" in data:
            continue
        
        # Get category info
        cat_info = next((c for c in DATA_CATEGORIES if c["id"] == cat_id), None)
        if not cat_info:
            continue
        
        try:
            fig = get_graph_for_category(cat_id, data)
            
            graph_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Span(f"{cat_info['icon']} {cat_info['name']}", className="fw-bold"),
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=fig, config={"displayModeBar": False})
                        ])
                    ], className="h-100")
                ], md=6, lg=4, className="mb-3")
            )
        except Exception as e:
            graph_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(f"{cat_info['icon']} {cat_info['name']}"),
                        dbc.CardBody([
                            dbc.Alert(f"Error: {str(e)[:50]}", color="warning")
                        ])
                    ])
                ], md=6, lg=4, className="mb-3")
            )
    
    if not graph_cards:
        return html.P("No data available for selected categories.", 
                     className="text-muted text-center py-4")
    
    return dbc.Row(graph_cards)


# ==================== INTERSECTION GRAPH CALLBACK ====================

@callback(
    Output("intersection-graph-container", "children"),
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_intersection_graph(loaded_data):
    """Show intersection/correlation graphs when compatible categories are selected."""
    if not loaded_data:
        return html.Div()
    
    categories_data = loaded_data.get("categories", {})
    selected_cats = list(categories_data.keys())
    
    # Define meaningful intersections
    intersections = [
        ({"air_quality", "weather"}, "Air Quality & Weather Correlation"),
        ({"earthquakes", "wildfires"}, "Seismic & Fire Activity"),
        ({"weather", "marine"}, "Atmospheric & Ocean Conditions"),
    ]
    
    for cat_pair, title in intersections:
        if cat_pair.issubset(set(selected_cats)):
            cats = list(cat_pair)
            fig = create_intersection_graph(categories_data, cats[0], cats[1])
            
            if fig:
                return dbc.Card([
                    dbc.CardHeader([
                        html.H5(f"🔗 {title}", className="mb-0"),
                        html.Small("Cross-dataset correlation", className="text-muted")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig, config={"displayModeBar": False})
                    ])
                ], className="mb-4")
    
    return html.Div()


# ==================== STATS AND STATUS CALLBACKS ====================

@callback(
    Output("dashboard-stats-row", "children"),
    [Input("reload-all-data-btn", "n_clicks"),
     Input("loaded-category-data", "data")],
    prevent_initial_call=False
)
def update_dashboard_stats(n_clicks, loaded_data):
    """Update the dashboard statistics cards."""
    try:
        hub_info = get_hub_info()
        
        # Count loaded data points
        data_points = 0
        if loaded_data:
            for cat_data in loaded_data.get("categories", {}).values():
                if isinstance(cat_data, dict):
                    data_points += len(cat_data.get("features", []))
                    data_points += len(cat_data.get("incidents", []))
                    data_points += len(cat_data.get("measurements", []))
                    data_points += len(cat_data.get("results", []))
                    data_points += len(cat_data.get("stations", []))
        
        stats = {
            "total_sources": hub_info.get("total_sources", 24),
            "active_alerts": 0,
            "data_points": str(data_points) if data_points else "0",
            "last_update": datetime.now().strftime("%H:%M:%S")
        }
        
        return create_stats_cards(stats)
    except Exception as e:
        return create_stats_cards({
            "total_sources": "Error",
            "active_alerts": "Error",
            "data_points": "Error",
            "last_update": str(e)[:20]
        })


@callback(
    [Output("quick-check-status", "children"),
     Output("aqi-gauge-container", "children"),
     Output("weather-summary-container", "children"),
     Output("loading-indicator", "children")],
    [Input("quick-check-btn", "n_clicks"),
     Input("search-btn", "n_clicks"),
     Input("initial-load-trigger", "n_intervals")],
    [State("quick-check-lat", "value"),
     State("quick-check-lon", "value"),
     State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=False
)
def update_quick_check(quick_clicks, search_clicks, n_intervals, quick_lat, quick_lon, sidebar_lat, sidebar_lon):
    """Update quick check results when location changes or on initial load."""
    triggered = ctx.triggered_id
    
    if triggered == "search-btn":
        lat = sidebar_lat or 37.7749
        lon = sidebar_lon or -122.4194
    else:
        lat = quick_lat or 37.7749
        lon = quick_lon or -122.4194
    
    try:
        result = quick_check(lat, lon)
        
        # Status badge
        status_map = {
            "normal": ("✅ Normal Conditions", "success"),
            "alert": ("🚨 Alert - Check Details", "danger"),
            "caution": ("⚠️ Caution - Minor Issues", "warning"),
            "partial_data": ("ℹ️ Partial Data Available", "info"),
            "unknown": ("❓ Status Unknown", "secondary")
        }
        overall_status = result.get("overall_status", "unknown")
        status_text, status_color = status_map.get(overall_status, ("Unknown", "secondary"))
        status_badge = dbc.Alert(status_text, color=status_color, className="mb-0 py-2")
        
        # AQI gauge
        air_quality = result.get("air_quality", {})
        aqi_value = air_quality.get("us_aqi", 0) if air_quality else 0
        aqi_status = air_quality.get("status", "Unknown") if air_quality else "Unknown"
        aqi_label = aqi_status.replace("_", " ").title()
        aqi_gauge = dcc.Graph(
            figure=create_aqi_gauge(aqi_value, f"Air Quality Index\n{aqi_label}"),
            config={"displayModeBar": False}
        )
        
        # Weather summary
        weather = result.get("weather", {})
        temp = weather.get("temperature_c", "N/A")
        wind = weather.get("wind_speed_kmh", "N/A")
        weather_status = weather.get("status", "unknown")
        
        weather_summary = html.Div([
            html.H6("Weather"),
            html.P([html.Strong("Temperature: "), f"{temp}°C" if temp != "N/A" else "N/A"]),
            html.P([html.Strong("Wind: "), f"{wind} km/h" if wind != "N/A" else "N/A"]),
            html.P([html.Strong("Conditions: "), weather_status.replace("_", " ").title()])
        ])
        
        loading_text = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
        
        return status_badge, aqi_gauge, weather_summary, loading_text
        
    except Exception as e:
        error_alert = dbc.Alert(f"Error: {str(e)[:50]}", color="danger", className="mb-0 py-2")
        return error_alert, html.P("Unable to load AQI"), html.P("Unable to load weather"), "Error loading data"


@callback(
    Output("categories-summary-container", "children"),
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_categories_summary(loaded_data):
    """Update the data categories summary."""
    try:
        hub_info = get_hub_info()
        sources_by_cat = hub_info.get("sources_by_category", {})
        total = hub_info.get("total_sources", 0)
        
        # Get loaded categories
        loaded_cats = set(loaded_data.get("categories", {}).keys()) if loaded_data else set()
        
        badges = []
        for cat in DATA_CATEGORIES:
            cat_id = cat["id"]
            cat_sources = sources_by_cat.get(cat_id, [])
            count = len(cat_sources) if isinstance(cat_sources, list) else 0
            
            # Highlight loaded categories
            is_loaded = cat_id in loaded_cats
            color = "success" if is_loaded else ("primary" if count > 0 else "secondary")
            
            badges.append(
                dbc.Badge(
                    f"{cat['icon']} {cat['name']}: {count}",
                    color=color,
                    className="me-2 mb-2 p-2"
                )
            )
        
        return html.Div([
            html.P(f"Total: {total} data sources across 10 categories", className="text-muted"),
            html.P(f"Loaded: {len(loaded_cats)} categories", className="text-muted small"),
            html.Div(badges)
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error loading categories: {str(e)[:50]}", color="danger")


@callback(
    Output("data-sources-status-container", "children"),
    [Input("reload-all-data-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_data_sources_status(n_clicks):
    """Update the data sources status panel."""
    try:
        sources = get_sources()
        source_list = sources.get("sources", [])
        
        if not source_list:
            return html.P("No data sources available", className="text-muted")
        
        rows = []
        for source in source_list[:10]:
            rows.append(html.Tr([
                html.Td(source.get("name", "Unknown")),
                html.Td(source.get("category", "N/A")),
                html.Td(
                    dbc.Badge("Free", color="success") if not source.get("requires_key")
                    else dbc.Badge("API Key", color="warning")
                ),
                html.Td(source.get("update_frequency", "N/A"))
            ]))
        
        return dbc.Table([
            html.Thead(html.Tr([
                html.Th("Source"),
                html.Th("Category"),
                html.Th("Access"),
                html.Th("Update Freq")
            ])),
            html.Tbody(rows)
        ], striped=True, hover=True, responsive=True, size="sm")
        
    except Exception as e:
        return dbc.Alert(f"Error loading sources: {str(e)[:50]}", color="danger")


# ==================== SYNC SIDEBAR TO QUICK CHECK ====================

@callback(
    [Output("quick-check-lat", "value", allow_duplicate=True),
     Output("quick-check-lon", "value", allow_duplicate=True)],
    Input("search-btn", "n_clicks"),
    [State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=True
)
def sync_sidebar_search_to_quickcheck(n_clicks, lat, lon):
    """When sidebar search is clicked, sync coordinates to quick check panel."""
    if lat is not None and lon is not None:
        return lat, lon
    return no_update, no_update
