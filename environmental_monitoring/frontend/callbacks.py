"""
Global Callbacks for Environmental Monitoring Dashboard

Contains callbacks for sidebar controls, global navigation, and shared functionality.
"""
from dash import html, dcc, callback, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import httpx

from api_client import (
    get_location_data, get_sources, get_categories, get_category_data,
    quick_check, get_air_quality, get_water_quality, get_weather, get_marine_data
)
from config import DATA_CATEGORIES, TIME_RANGES


# ==================== Geocoding Utility ====================

def geocode_location(query: str) -> dict:
    """
    Geocode a location string to coordinates using Nominatim (free, no API key).
    
    Args:
        query: Location name (city, address, etc.)
    
    Returns:
        dict with lat, lon, display_name or error
    """
    try:
        # Use Nominatim (OpenStreetMap) - free geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "EnvironmentalMonitoringDashboard/1.0"
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = results[0]
                return {
                    "success": True,
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "display_name": result["display_name"],
                    "type": result.get("type", "place")
                }
            else:
                return {
                    "success": False,
                    "error": f"No results found for '{query}'"
                }
                
    except httpx.TimeoutException:
        return {"success": False, "error": "Geocoding request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Geocoding error: {str(e)}"}


# ==================== Sidebar Location Search ====================

@callback(
    [Output("latitude-input", "value"),
     Output("longitude-input", "value"),
     Output("location-search", "value")],
    Input("search-btn", "n_clicks"),
    State("location-search", "value"),
    prevent_initial_call=True
)
def search_location(n_clicks, search_query):
    """Search for a location and update coordinates."""
    if not search_query or not search_query.strip():
        return no_update, no_update, no_update
    
    result = geocode_location(search_query.strip())
    
    if result.get("success"):
        # Return coordinates and clear search (keep display name as placeholder effect)
        return result["lat"], result["lon"], ""
    else:
        # Keep existing values on error
        return no_update, no_update, no_update


# ==================== Sidebar Time Range Buttons ====================

@callback(
    [Output("custom-date-div", "style"),
     Output("start-date", "date"),
     Output("end-date", "date")],
    [Input("time-1H", "n_clicks"),
     Input("time-6H", "n_clicks"),
     Input("time-24H", "n_clicks"),
     Input("time-7D", "n_clicks"),
     Input("time-30D", "n_clicks"),
     Input("time-90D", "n_clicks"),
     Input("time-1Y", "n_clicks"),
     Input("time-custom", "n_clicks")],
    prevent_initial_call=True
)
def handle_time_range_buttons(*args):
    """Handle time range button clicks in the sidebar."""
    if not ctx.triggered:
        return no_update, no_update, no_update
    
    triggered_id = ctx.triggered_id
    now = datetime.now()
    
    time_deltas = {
        "time-1H": timedelta(hours=1),
        "time-6H": timedelta(hours=6),
        "time-24H": timedelta(days=1),
        "time-7D": timedelta(days=7),
        "time-30D": timedelta(days=30),
        "time-90D": timedelta(days=90),
        "time-1Y": timedelta(days=365),
    }
    
    if triggered_id == "time-custom":
        # Show custom date picker
        return {"display": "block"}, no_update, no_update
    elif triggered_id in time_deltas:
        # Set dates based on selection
        start = now - time_deltas[triggered_id]
        return {"display": "none"}, start.date(), now.date()
    
    return no_update, no_update, no_update


# ==================== Settings Modal ====================

@callback(
    Output("settings-modal", "is_open"),
    [Input("settings-button", "n_clicks"),
     Input("settings-save-btn", "n_clicks"),
     Input("settings-cancel-btn", "n_clicks")],
    State("settings-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_settings_modal(open_clicks, save_clicks, cancel_clicks, is_open):
    """Toggle the settings modal."""
    triggered = ctx.triggered_id
    
    if triggered == "settings-button":
        return True
    elif triggered in ["settings-save-btn", "settings-cancel-btn"]:
        return False
    return is_open


# ==================== Quick Actions ====================

@callback(
    Output("export-toast", "is_open"),
    Input("quick-export-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_quick_export(n_clicks):
    """Handle quick export button click."""
    if n_clicks:
        # Show toast notification - actual export would need more implementation
        return True
    return False


@callback(
    Output("share-toast", "is_open"),
    Input("quick-share-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_quick_share(n_clicks):
    """Handle quick share button click."""
    if n_clicks:
        return True
    return False


# ==================== Global Data Refresh ====================

@callback(
    Output("global-data-store", "data"),
    [Input("refresh-button", "n_clicks"),
     Input("refresh-interval", "n_intervals")],
    [State("latitude-input", "value"),
     State("longitude-input", "value"),
     State("category-checklist", "value")],
    prevent_initial_call=True
)
def refresh_global_data(n_clicks, n_intervals, lat, lon, categories):
    """Refresh global data store with current filters."""
    if lat is None:
        lat = 37.7749
    if lon is None:
        lon = -122.4194
    
    try:
        # Fetch data for selected categories
        data = get_location_data(lat, lon, radius_km=50, categories=categories)
        
        return {
            "location": {"lat": lat, "lon": lon},
            "categories": categories,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ==================== Coordinate Sync Between Pages ====================

@callback(
    [Output("quick-check-lat", "value", allow_duplicate=True),
     Output("quick-check-lon", "value", allow_duplicate=True)],
    [Input("latitude-input", "value"),
     Input("longitude-input", "value")],
    prevent_initial_call=True
)
def sync_sidebar_to_dashboard(lat, lon):
    """Sync sidebar coordinates to dashboard quick check."""
    return lat, lon


@callback(
    [Output("explore-lat", "value", allow_duplicate=True),
     Output("explore-lon", "value", allow_duplicate=True)],
    [Input("latitude-input", "value"),
     Input("longitude-input", "value")],
    prevent_initial_call=True
)
def sync_sidebar_to_explore(lat, lon):
    """Sync sidebar coordinates to explore page."""
    return lat, lon


# ==================== Category Quick Fetch ====================

@callback(
    Output("category-data-toast", "children"),
    Input("category-checklist", "value"),
    prevent_initial_call=True
)
def on_category_change(selected_categories):
    """Show feedback when categories are changed."""
    if selected_categories:
        count = len(selected_categories)
        return f"{count} categor{'y' if count == 1 else 'ies'} selected"
    return "No categories selected"
