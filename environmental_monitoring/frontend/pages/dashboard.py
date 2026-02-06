"""
Dashboard Page - Main overview with key metrics and visualizations.
"""
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime

from api_client import get_hub_info, get_sources, quick_check, get_health
from components.charts import (
    create_aqi_gauge,
    create_time_series_chart,
    create_mapbox_scatter
)
from components.layout import create_stats_cards
from config import DATA_CATEGORIES, MAP_CONFIG


def create_dashboard_layout() -> html.Div:
    """Create the main dashboard page layout."""
    return html.Div([
        # Stats Cards Row
        html.Div(id="dashboard-stats-row"),
        
        # Quick Check Panel
        dbc.Card([
            dbc.CardHeader([
                html.H5("⚡ Quick Environmental Check", className="mb-0"),
                dbc.Button(
                    [html.I(className="fas fa-sync-alt me-2"), "Refresh"],
                    id="quick-check-refresh-btn",
                    color="outline-primary",
                    size="sm"
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
                        dbc.Button("Check Location", id="quick-check-btn", color="primary")
                    ], md=2),
                    dbc.Col([
                        html.Div(id="quick-check-status", className="mt-4")
                    ], md=4)
                ])
            ])
        ], className="mb-4"),
        
        # Main Content Row
        dbc.Row([
            # Map Column
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("🗺️ Environmental Map", className="mb-0")),
                    dbc.CardBody([
                        dcc.Graph(id="dashboard-map", style={"height": "400px"})
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
        
        # Charts Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("📈 Recent Trends", className="mb-0")),
                    dbc.CardBody([
                        dcc.Graph(id="dashboard-trends-chart", style={"height": "350px"})
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("📊 Data Categories", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="categories-summary-container")
                    ])
                ])
            ], md=6)
        ], className="mb-4"),
        
        # Data Sources Status
        dbc.Card([
            dbc.CardHeader([
                html.H5("🌐 Data Sources Status", className="mb-0"),
                dbc.Button(
                    "View All Sources",
                    href="/explore",
                    color="link",
                    size="sm"
                )
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                html.Div(id="data-sources-status-container")
            ])
        ])
    ])


@callback(
    Output("dashboard-stats-row", "children"),
    Input("quick-check-refresh-btn", "n_clicks"),
    prevent_initial_call=False
)
def update_dashboard_stats(n_clicks):
    """Update the dashboard statistics cards."""
    try:
        hub_info = get_hub_info()
        health = get_health()
        
        stats = {
            "total_sources": hub_info.get("total_sources", 24),
            "active_alerts": 0,  # Would come from alerts API
            "data_points": "Real-time",
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
     Output("weather-summary-container", "children")],
    Input("quick-check-btn", "n_clicks"),
    [State("quick-check-lat", "value"),
     State("quick-check-lon", "value")],
    prevent_initial_call=False
)
def update_quick_check(n_clicks, lat, lon):
    """Update quick check results."""
    if lat is None or lon is None:
        lat, lon = 37.7749, -122.4194
    
    try:
        result = quick_check(lat, lon)
        
        # Status badge
        status = result.get("quick_status", "Unknown")
        status_color = "success" if "✅" in status else "warning" if "⚠️" in status else "info"
        status_badge = dbc.Alert(status, color=status_color, className="mb-0 py-2")
        
        # AQI gauge (placeholder - would need actual AQI data)
        aqi_gauge = dcc.Graph(
            figure=create_aqi_gauge(42, "Air Quality Index"),
            config={"displayModeBar": False}
        )
        
        # Weather summary
        weather = result.get("summary", {}).get("weather", {})
        weather_summary = html.Div([
            html.H6("Weather"),
            html.P([
                html.Strong("Temperature: "),
                f"{weather.get('temperature_c', 'N/A')}°C"
            ]),
            html.P([
                html.Strong("Wind: "),
                f"{weather.get('windspeed_kmh', 'N/A')} km/h"
            ]),
            html.P([
                html.Strong("Direction: "),
                f"{weather.get('winddirection', 'N/A')}°"
            ])
        ])
        
        return status_badge, aqi_gauge, weather_summary
        
    except Exception as e:
        error_alert = dbc.Alert(f"Error: {str(e)[:50]}", color="danger", className="mb-0 py-2")
        return error_alert, html.P("Unable to load AQI"), html.P("Unable to load weather")


@callback(
    Output("dashboard-map", "figure"),
    Input("quick-check-btn", "n_clicks"),
    [State("quick-check-lat", "value"),
     State("quick-check-lon", "value")],
    prevent_initial_call=False
)
def update_dashboard_map(n_clicks, lat, lon):
    """Update the dashboard map."""
    if lat is None or lon is None:
        lat, lon = MAP_CONFIG["default_lat"], MAP_CONFIG["default_lon"]
    
    # Create a simple map centered on location
    import plotly.graph_objects as go
    
    fig = go.Figure(go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=dict(size=14, color="red"),
        text=["Selected Location"],
        hoverinfo="text"
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=lat, lon=lon),
            zoom=10
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    
    return fig


@callback(
    Output("categories-summary-container", "children"),
    Input("quick-check-refresh-btn", "n_clicks"),
    prevent_initial_call=False
)
def update_categories_summary(n_clicks):
    """Update the data categories summary."""
    try:
        sources = get_sources()
        total = sources.get("total", 0)
        
        # Create category badges
        badges = []
        for cat in DATA_CATEGORIES:
            cat_sources = get_sources(cat["id"])
            count = cat_sources.get("total", 0) if not cat_sources.get("error") else 0
            badges.append(
                dbc.Badge(
                    f"{cat['icon']} {cat['name']}: {count}",
                    color="primary" if count > 0 else "secondary",
                    className="me-2 mb-2 p-2"
                )
            )
        
        return html.Div([
            html.P(f"Total: {total} data sources across 10 categories", className="text-muted"),
            html.Div(badges)
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error loading categories: {str(e)[:50]}", color="danger")


@callback(
    Output("data-sources-status-container", "children"),
    Input("quick-check-refresh-btn", "n_clicks"),
    prevent_initial_call=False
)
def update_data_sources_status(n_clicks):
    """Update the data sources status panel."""
    try:
        sources = get_sources()
        source_list = sources.get("sources", [])
        
        if not source_list:
            return html.P("No data sources available", className="text-muted")
        
        # Create a table of sources
        rows = []
        for source in source_list[:10]:  # Show first 10
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
