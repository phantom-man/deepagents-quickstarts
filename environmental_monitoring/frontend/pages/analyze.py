"""
Analyze Page - Advanced analytics, cross-domain analysis, and insights.
"""
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time

from api_client import (
    get_location_data, analyze_location, get_category_data, proxy_request,
    get_categories_parallel,
)
from components.progress_box import create_progress_box, make_entry, render_entries
from components.charts import (
    create_time_series_chart,
    create_correlation_heatmap,
    create_anomaly_chart,
    create_trend_chart,
    create_histogram,
    create_box_plot,
    create_multi_axis_chart,
    create_summary_cards
)
from components.layout import (
    create_analysis_panel,
    create_cross_domain_panel
)
from data_processing import DataProcessor
from config import DATA_CATEGORIES, ANALYSIS_TYPES, STAT_METHODS, TIME_RANGES, API_BASE_URL


# ==================== DATA EXTRACTION HELPERS ====================

def _extract_numeric_values(raw_data: dict) -> list:
    """Recursively extract numeric values from nested API response."""
    values = []
    if not isinstance(raw_data, dict):
        return values

    # Try known structures
    # Earthquakes (USGS GeoJSON)
    for f in raw_data.get("features", []):
        if not isinstance(f, dict):
            continue
        mag = (f.get("properties") or {}).get("mag")
        if mag is not None:
            try:
                values.append(float(mag))
            except (ValueError, TypeError):
                pass

    # Air quality — Open-Meteo current{}
    current_aq = raw_data.get("current") or {}
    if isinstance(current_aq, dict):
        for aq_key in ("us_aqi", "pm2_5", "pm10", "carbon_monoxide",
                        "nitrogen_dioxide", "sulphur_dioxide", "ozone"):
            v = current_aq.get(aq_key)
            if v is not None:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass

    # Air quality — legacy measurements/results
    for m in raw_data.get("measurements", raw_data.get("results", [])):
        if isinstance(m, dict):
            v = m.get("value")
            if v is not None:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass

    # Hourly data (weather, air quality, marine, radiation)
    hourly = raw_data.get("hourly") or {}
    if isinstance(hourly, dict):
        for hourly_key in ("temperature_2m", "us_aqi", "pm2_5", "pm10",
                           "wave_height", "sea_surface_temperature",
                           "uv_index", "direct_radiation", "shortwave_radiation",
                           "relative_humidity_2m", "wind_speed_10m", "precipitation"):
            for v in hourly.get(hourly_key, []):
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        pass

    # Climate daily
    daily = raw_data.get("daily") or {}
    if isinstance(daily, dict):
        for daily_key in ("temperature_2m_max", "temperature_2m_min", "precipitation_sum"):
            for v in daily.get(daily_key, []):
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        pass

    # Water
    for ts in (raw_data.get("value") or {}).get("timeSeries", []):
        try:
            v = float(ts.get("values", [{}])[0].get("value", [{}])[0].get("value", 0))
            if v:
                values.append(v)
        except (IndexError, TypeError, ValueError):
            pass

    # Soil (SoilGrids properties.layers)
    soil_props = raw_data.get("properties") or {}
    if isinstance(soil_props, dict):
        for layer in soil_props.get("layers", []):
            if isinstance(layer, dict):
                for depth in layer.get("depths", []):
                    if isinstance(depth, dict):
                        mean_val = (depth.get("values") or {}).get("mean")
                        if mean_val is not None:
                            try:
                                values.append(float(mean_val))
                            except (ValueError, TypeError):
                                pass

    # Biodiversity
    for r in raw_data.get("results", []):
        if isinstance(r, dict):
            for num_key in ("count", "individualCount", "occurrences"):
                v = r.get(num_key)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        pass

    # Wildfires (NIFC GeoJSON features with attributes)
    for f in raw_data.get("features", []):
        if not isinstance(f, dict):
            continue
        props = f.get("properties") or f.get("attributes") or {}
        if isinstance(props, dict):
            for fire_key in ("GISAcres", "poly_GISAcres", "irwin_DailyAcres",
                             "PercentContained", "irwin_PercentContained"):
                v = props.get(fire_key)
                if v is not None:
                    try:
                        values.append(float(str(v).replace(",", "")))
                    except (ValueError, TypeError):
                        pass

    # Nested data from analyze_location (data -> category -> sources)
    for cat_key, cat_val in (raw_data.get("data") or {}).items():
        if isinstance(cat_val, list):
            for source in cat_val:
                if isinstance(source, dict):
                    inner = source.get("data") or {}
                    if isinstance(inner, dict):
                        values.extend(_extract_numeric_values(inner))

    return values


def _build_dataframe(raw_data: dict, time_range: str = "7D") -> pd.DataFrame:
    """Build a time-indexed DataFrame from real API data."""
    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365,
    }
    days = time_to_days.get(time_range, 7)

    # Try weather hourly first (best time series)
    hourly = raw_data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    if times and temps:
        n = min(len(times), len(temps))
        try:
            idx = pd.to_datetime(times[:n])
            return pd.DataFrame({"value": [float(t) for t in temps[:n]]}, index=idx)
        except Exception:
            pass

    # Try climate daily
    daily = raw_data.get("daily", {})
    dt = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    if dt and t_max:
        n = min(len(dt), len(t_max))
        try:
            idx = pd.to_datetime(dt[:n])
            return pd.DataFrame({"value": [float(v) for v in t_max[:n]]}, index=idx)
        except Exception:
            pass

    # Try nested categories from analyze_location
    for cat_key, cat_val in raw_data.get("data", {}).items():
        if isinstance(cat_val, list):
            for source in cat_val:
                if isinstance(source, dict):
                    inner = source.get("data", {})
                    if isinstance(inner, dict):
                        df = _build_dataframe(inner, time_range)
                        if not df.empty:
                            return df

    # Fallback: extract all numeric values and give them a synthetic index
    values = _extract_numeric_values(raw_data)
    if values:
        idx = pd.date_range(
            end=datetime.now(), periods=len(values), freq="h"
        )
        return pd.DataFrame({"value": values}, index=idx)

    return pd.DataFrame()


def _build_multi_column_df(raw_data: dict) -> pd.DataFrame:
    """Build a multi-column DataFrame from different data categories."""
    columns = {}

    # Weather temps
    hourly = raw_data.get("hourly", {})
    temps = hourly.get("temperature_2m", [])
    if temps:
        columns["Temperature"] = [float(v) for v in temps]

    humidity = hourly.get("relative_humidity_2m", hourly.get("relativehumidity_2m", []))
    if humidity:
        columns["Humidity"] = [float(v) for v in humidity]

    precip = hourly.get("precipitation", [])
    if precip:
        columns["Precipitation"] = [float(v) for v in precip]

    wind = hourly.get("windspeed_10m", hourly.get("wind_speed_10m", []))
    if wind:
        columns["Wind Speed"] = [float(v) for v in wind]

    # From nested categories
    for cat_key, cat_val in raw_data.get("data", {}).items():
        if isinstance(cat_val, list):
            for source in cat_val:
                inner = source.get("data", {}) if isinstance(source, dict) else {}
                if isinstance(inner, dict):
                    h2 = inner.get("hourly", {})
                    for k, label in [
                        ("temperature_2m", f"Temp ({cat_key})"),
                        ("relative_humidity_2m", f"Humidity ({cat_key})"),
                    ]:
                        vals = h2.get(k, [])
                        if vals and label not in columns:
                            columns[label] = [float(v) for v in vals]

    if not columns:
        return pd.DataFrame()

    # Trim to same length
    min_len = min(len(v) for v in columns.values())
    return pd.DataFrame({k: v[:min_len] for k, v in columns.items()})


def create_analyze_layout() -> html.Div:
    """Create the advanced analytics page layout."""
    return html.Div([
        # Page Header
        html.Div([
            html.H3("🔬 Advanced Analytics", className="mb-2"),
            html.P("Statistical analysis, anomaly detection, trend forecasting, and cross-domain insights", 
                   className="text-muted")
        ], className="mb-4"),
        
        # Time Range Selector for Analysis - Simple Dropdown
        dbc.Card([
            dbc.CardHeader(html.H5("⏱️ Analysis Time Range", className="mb-0")),
            dbc.CardBody([
                dcc.Dropdown(
                    id="analyze-time-range",
                    options=[
                        {"label": tr["label"], "value": tr["value"]}
                        for tr in TIME_RANGES if tr["value"] != "custom"
                    ],
                    value="7D",
                    clearable=False,
                    style={"width": "200px"},
                    className="d-inline-block"
                ),
                html.Span(id="analyze-time-display", className="text-muted ms-3")
            ])
        ], className="mb-4"),
        
        # Analysis Configuration
        create_analysis_panel(),
        
        # Cross-Domain Analysis
        create_cross_domain_panel(),
        
        # Analysis Type Selector with Options
        dbc.Card([
            dbc.CardHeader(html.H5("📊 Analysis Type", className="mb-0")),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab([
                        html.Div([
                            html.H6("Time Series Analysis", className="mt-3"),
                            html.P("Analyze temporal patterns, trends, and seasonality.", className="text-muted"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Moving Average Window"),
                                    dbc.Input(id="ts-ma-window", type="number", value=24, min=1, max=168)
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Smoothing Method"),
                                    dcc.Dropdown(
                                        id="ts-smooth-method",
                                        options=[
                                            {"label": "Simple Moving Average", "value": "simple"},
                                            {"label": "Exponential Moving Average", "value": "exponential"},
                                            {"label": "Savitzky-Golay Filter", "value": "savgol"}
                                        ],
                                        value="simple"
                                    )
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Show Components"),
                                    dbc.Checklist(
                                        id="ts-components",
                                        options=[
                                            {"label": "Trend", "value": "trend"},
                                            {"label": "Seasonal", "value": "seasonal"},
                                            {"label": "Residual", "value": "residual"}
                                        ],
                                        value=["trend"],
                                        inline=True
                                    )
                                ], md=6)
                            ])
                        ])
                    ], label="📈 Time Series", tab_id="time-series"),
                    
                    dbc.Tab([
                        html.Div([
                            html.H6("Correlation Analysis", className="mt-3"),
                            html.P("Find relationships between different environmental parameters.", className="text-muted"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Correlation Method"),
                                    dcc.Dropdown(
                                        id="corr-method",
                                        options=[
                                            {"label": "Pearson", "value": "pearson"},
                                            {"label": "Spearman", "value": "spearman"},
                                            {"label": "Kendall", "value": "kendall"}
                                        ],
                                        value="pearson"
                                    )
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Minimum Correlation"),
                                    dbc.Input(id="corr-threshold", type="number", value=0.5, min=0, max=1, step=0.1)
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Show Significance"),
                                    dbc.Switch(id="corr-significance", value=True)
                                ], md=4)
                            ])
                        ])
                    ], label="🔗 Correlation", tab_id="correlation"),
                    
                    dbc.Tab([
                        html.Div([
                            html.H6("Anomaly Detection", className="mt-3"),
                            html.P("Identify unusual patterns and outliers in the data.", className="text-muted"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Detection Method"),
                                    dcc.Dropdown(
                                        id="anomaly-method",
                                        options=[
                                            {"label": "Z-Score", "value": "zscore"},
                                            {"label": "IQR", "value": "iqr"},
                                            {"label": "Rolling Statistics", "value": "rolling"},
                                            {"label": "Isolation Forest", "value": "iforest"}
                                        ],
                                        value="zscore"
                                    )
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Threshold"),
                                    dbc.Input(id="anomaly-threshold", type="number", value=3.0, min=1, max=5, step=0.5)
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Window Size"),
                                    dbc.Input(id="anomaly-window", type="number", value=24, min=1)
                                ], md=4)
                            ])
                        ])
                    ], label="⚠️ Anomaly", tab_id="anomaly"),
                    
                    dbc.Tab([
                        html.Div([
                            html.H6("Trend Analysis", className="mt-3"),
                            html.P("Analyze long-term trends and make forecasts.", className="text-muted"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Trend Method"),
                                    dcc.Dropdown(
                                        id="trend-method",
                                        options=[
                                            {"label": "Linear Regression", "value": "linear"},
                                            {"label": "Mann-Kendall", "value": "mannkendall"},
                                            {"label": "Sen's Slope", "value": "sens"}
                                        ],
                                        value="linear"
                                    )
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Forecast Periods"),
                                    dbc.Input(id="trend-forecast", type="number", value=24, min=0, max=168)
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Confidence Interval"),
                                    dcc.Dropdown(
                                        id="trend-confidence",
                                        options=[
                                            {"label": "90%", "value": 0.90},
                                            {"label": "95%", "value": 0.95},
                                            {"label": "99%", "value": 0.99}
                                        ],
                                        value=0.95
                                    )
                                ], md=4)
                            ])
                        ])
                    ], label="📉 Trend", tab_id="trend"),
                    
                    dbc.Tab([
                        html.Div([
                            html.H6("Distribution Analysis", className="mt-3"),
                            html.P("Analyze statistical distributions and compare datasets.", className="text-muted"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Number of Bins"),
                                    dbc.Input(id="dist-bins", type="number", value=50, min=10, max=200)
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Show Normal Fit"),
                                    dbc.Switch(id="dist-normal", value=True)
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Normality Test"),
                                    dcc.Dropdown(
                                        id="dist-test",
                                        options=[
                                            {"label": "Shapiro-Wilk", "value": "shapiro"},
                                            {"label": "D'Agostino-Pearson", "value": "dagostino"},
                                            {"label": "Kolmogorov-Smirnov", "value": "ks"}
                                        ],
                                        value="shapiro"
                                    )
                                ], md=4)
                            ])
                        ])
                    ], label="📊 Distribution", tab_id="distribution")
                ], id="analysis-type-tabs", active_tab="time-series")
            ])
        ], className="mb-4"),
        
        # Run Analysis Button
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-play me-2"),
                    "Run Analysis"
                ], id="run-analysis-btn", color="success", size="lg", className="w-100",
                   disabled=False)
            ], md=4, className="offset-md-4")
        ], className="mb-4"),
        
        # Results Section
        dbc.Card([
            dbc.CardHeader([
                html.H5("📋 Analysis Results", className="mb-0"),
                dbc.ButtonGroup([
                    dbc.Button([html.I(className="fas fa-download")], id="export-results-btn", 
                              color="outline-secondary", size="sm"),
                    dbc.Button([html.I(className="fas fa-expand")], id="fullscreen-results-btn", 
                              color="outline-secondary", size="sm")
                ])
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                # Statistics Summary
                dcc.Loading(
                    type="default",
                    children=html.Div(id="analysis-stats-container", className="mb-4"),
                ),
                
                # Main Chart
                dcc.Loading(
                    type="circle",
                    overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                    children=html.Div(id="analysis-chart-container", className="mb-4"),
                ),
                
                # Secondary Charts
                dcc.Loading(
                    type="default",
                    children=dbc.Row(id="analysis-secondary-charts"),
                ),
                
                # Insights
                html.Div(id="analysis-insights-container")
            ])
        ]),
        
        # Hidden stores
        dcc.Store(id="analysis-data-store"),
        dcc.Store(id="analysis-results-store"),
        
        # Loading
        dcc.Loading(
            id="analysis-loading",
            type="circle",
            children=html.Div(id="analysis-loading-output")
        ),

        # ── Activity Log ──
        create_progress_box("analyze", [
            "progress-analyze-run",
        ]),
    ])


@callback(
    Output("analyze-time-display", "children"),
    Input("analyze-time-range", "value"),
    prevent_initial_call=False
)
def handle_analyze_time_dropdown(selected_value):
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
    Output("analysis-options-container", "children"),
    Input("analysis-type-selector", "value"),
    prevent_initial_call=False
)
def update_analysis_options(analysis_type):
    """Update analysis-specific options based on selected type."""
    options = []
    
    if analysis_type == "time_series":
        options = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("Decomposition Period"),
                    dbc.Input(id="decomp-period", type="number", value=24, min=2)
                ], md=4)
            ])
        ]
    elif analysis_type == "correlation":
        options = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("Lag Analysis"),
                    dbc.Input(id="corr-lag", type="number", value=0, min=0, max=48)
                ], md=4)
            ])
        ]
    elif analysis_type == "forecasting":
        options = [
            dbc.Row([
                dbc.Col([
                    dbc.Label("Forecast Horizon"),
                    dbc.Input(id="forecast-horizon", type="number", value=24, min=1)
                ], md=4),
                dbc.Col([
                    dbc.Label("Model"),
                    dcc.Dropdown(
                        id="forecast-model",
                        options=[
                            {"label": "ARIMA", "value": "arima"},
                            {"label": "Exponential Smoothing", "value": "ets"},
                            {"label": "Prophet", "value": "prophet"}
                        ],
                        value="ets"
                    )
                ], md=4)
            ])
        ]
    
    return html.Div(options) if options else html.P("No additional options for this analysis type.", 
                                                      className="text-muted small")


@callback(
    Output("primary-dataset-selector", "options"),
    Output("secondary-dataset-selector", "options"),
    Input("analyze-time-range", "value"),
    prevent_initial_call=False,
)
def update_dataset_options(_time_range):
    """Populate cross-domain dataset dropdowns on page load.

    Previously depended on ``source-category-filter`` which only existed on
    the *explore* page, so the dropdowns were always empty on *analyze*.
    Now fires unconditionally using a component guaranteed to be on this page.
    """
    datasets = [
        {"label": f"{cat['icon']} {cat['name']}", "value": cat["id"]}
        for cat in DATA_CATEGORIES
    ]
    return datasets, datasets


@callback(
    [Output("analysis-results-store", "data"),
     Output("analysis-loading-output", "children"),
     Output("progress-analyze-run", "data")],
    [Input("run-analysis-btn", "n_clicks"),
     Input("category-checklist", "value")],
    [State("analysis-type-selector", "value"),
     State("aggregation-selector", "value"),
     State("statistic-selector", "value"),
        State("latitude-input", "value"),
        State("longitude-input", "value"),
     State("analysis-type-tabs", "active_tab"),
     State("analyze-time-range", "value")],
    prevent_initial_call=False
)
def run_analysis(n_clicks, categories, analysis_type, aggregation, statistic, lat, lon, active_tab, time_range):
    """Execute the selected analysis. Auto-triggers on page load."""
    _t0 = time.time()
    if lat is None or lon is None:
        lat, lon = 37.7749, -122.4194
    
    # Convert time range to days
    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365
    }
    days = time_to_days.get(time_range, 7)
    
    try:
        # Fetch raw category data in parallel
        combined_raw = {}
        selected_cats = categories if categories else [
            c["id"] for c in DATA_CATEGORIES
        ]
        api_results = get_categories_parallel(selected_cats, lat, lon)
        for cat_id in selected_cats:
            try:
                cat_data = api_results.get(cat_id, {})
                if cat_data and not cat_data.get("error"):
                    sources = cat_data.get("data") or cat_data.get("sources") or []
                    for src in sources:
                        if isinstance(src, dict) and src.get("success"):
                            inner = src.get("data", {})
                            if isinstance(inner, dict):
                                for key in ("hourly", "daily", "features",
                                             "measurements", "results",
                                             "properties", "value"):
                                    if key in inner and key not in combined_raw:
                                        combined_raw[key] = inner[key]
                            combined_raw.setdefault("data", {}).setdefault(
                                cat_id, []
                            ).append(src)
            except Exception:
                pass

        # Also fetch analysis insights
        data = analyze_location(lat, lon, days=days)
        if data and not data.get("error"):
            combined_raw["analysis"] = data

        # Process based on analysis type
        results = {
            "analysis_type": active_tab or analysis_type,
            "aggregation": aggregation,
            "statistic": statistic,
            "location": {"lat": lat, "lon": lon},
            "timestamp": datetime.now().isoformat(),
            "raw_data": combined_raw,
            "processed": {}
        }
        
        _elapsed = int((time.time() - _t0) * 1000)
        _cat_count = len(selected_cats)
        _data_keys = len(combined_raw)
        _prog = [
            make_entry("info", f"Running {active_tab or analysis_type} analysis at ({lat:.2f}, {lon:.2f})"),
            make_entry("complete", f"Fetched {_cat_count} categories, {_data_keys} data streams", duration_ms=_elapsed),
            make_entry("separator", ""),
            make_entry("success", "Analysis complete"),
        ]
        return results, dbc.Alert("Analysis complete!", color="success"), _prog
        
    except Exception as e:
        return None, dbc.Alert(f"Analysis failed: {str(e)}", color="danger"), [
            make_entry("error", f"Analysis failed: {str(e)[:60]}"),
        ]


@callback(
    Output("analysis-stats-container", "children"),
    Input("analysis-results-store", "data"),
    prevent_initial_call=True
)
def update_analysis_stats(results):
    """Update the statistics summary from real API data."""
    if not results:
        return html.P("Run an analysis to see statistics.", className="text-muted")

    raw_data = results.get("raw_data", {})
    values = _extract_numeric_values(raw_data)

    if not values:
        api_links = [
            html.Li(html.A(
                f"{cat['icon']} {cat['name']}",
                href=f"{API_BASE_URL}/api/v1/hub/category/{cat['id']}?lat=37.7749&lon=-122.4194",
                target="_blank"
            ))
            for cat in DATA_CATEGORIES
        ]
        return html.Div([
            dbc.Alert(
                "No numeric data available for this location. Try different coordinates.",
                color="warning",
            ),
            html.P("View raw API data:", className="fw-bold mt-2"),
            html.Ul(api_links, style={"fontSize": "0.85rem"}),
        ])

    arr = np.array(values, dtype=float)
    stats = {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": len(arr),
        "p90": float(np.percentile(arr, 90)),
        "iqr": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
    }

    return dcc.Graph(
        figure=create_summary_cards(stats),
        config={"displayModeBar": False}
    )


@callback(
    Output("analysis-chart-container", "children"),
    Input("analysis-results-store", "data"),
    [State("analysis-type-tabs", "active_tab"),
     State("analyze-time-range", "value")],
    prevent_initial_call=True
)
def update_analysis_chart(results, analysis_type, time_range):
    """Update the main analysis chart using real API data."""
    if not results:
        return html.P("Run an analysis to see the chart.", className="text-muted")

    raw_data = results.get("raw_data", {})
    df = _build_dataframe(raw_data, time_range)

    if df.empty or "value" not in df.columns:
        return dbc.Alert(
            "No chartable data returned from the API. Try selecting different categories.",
            color="warning",
        )

    if analysis_type == "time-series":
        df["moving_avg"] = df["value"].rolling(min(24, max(2, len(df) // 4)), min_periods=1).mean()
        fig = create_time_series_chart(
            df,
            columns=["value", "moving_avg"],
            title="Time Series Analysis (Real Data)",
            y_title="Value",
        )
    elif analysis_type == "correlation":
        # Build multi-column DF from raw_data categories
        corr_df = _build_multi_column_df(raw_data)
        if corr_df.shape[1] >= 2:
            fig = create_correlation_heatmap(corr_df.corr(), title="Parameter Correlations (Real Data)")
        else:
            fig = create_time_series_chart(df, columns=["value"], title="Insufficient data for correlation")
    elif analysis_type == "anomaly":
        processor = DataProcessor()
        anomalies = processor.detect_anomalies(df["value"], method="zscore", threshold=2.0)
        fig = create_anomaly_chart(df, "value", anomalies, title="Anomaly Detection (Real Data)")
    elif analysis_type == "trend":
        processor = DataProcessor()
        trend_data = processor.calculate_trend(df["value"])
        fig = create_trend_chart(df, "value", trend_data, title="Trend Analysis (Real Data)")
    elif analysis_type == "distribution":
        fig = create_histogram(
            df["value"],
            title="Value Distribution (Real Data)",
            x_title="Value",
            show_normal=True,
        )
    else:
        fig = create_time_series_chart(df, columns=["value"], title="Analysis Results (Real Data)")

    return dcc.Graph(figure=fig, config={"displayModeBar": True})


@callback(
    Output("analysis-secondary-charts", "children"),
    Input("analysis-results-store", "data"),
    prevent_initial_call=True
)
def update_secondary_charts(results):
    """Update secondary analysis charts using real data."""
    if not results:
        return []

    raw_data = results.get("raw_data", {})
    values = _extract_numeric_values(raw_data)
    if not values:
        return []

    arr = np.array(values, dtype=float)
    df = pd.DataFrame({"value": arr})

    charts = []
    try:
        charts.append(
            dbc.Col([
                dcc.Graph(
                    figure=create_histogram(
                        df["value"], title="Distribution (Real Data)", nbins=min(30, len(arr)), height=350
                    ),
                    config={"displayModeBar": False},
                )
            ], md=6)
        )
    except Exception:
        pass

    # Build multi-column DF if possible for box plot
    multi_df = _build_multi_column_df(raw_data)
    if multi_df.shape[1] >= 2:
        cols = list(multi_df.columns)[:4]
        try:
            charts.append(
                dbc.Col([
                    dcc.Graph(
                        figure=create_box_plot(multi_df, cols, title="Category Comparison", height=350),
                        config={"displayModeBar": False},
                    )
                ], md=6)
            )
        except Exception:
            pass

    return charts


@callback(
    Output("analysis-insights-container", "children"),
    Input("analysis-results-store", "data"),
    [State("analysis-type-tabs", "active_tab")],
    prevent_initial_call=True
)
def update_analysis_insights(results, analysis_type):
    """Generate real insights from the analysis data."""
    if not results:
        return html.P("Run an analysis to see insights.", className="text-muted")

    raw_data = results.get("raw_data", {})
    location = results.get("location", {})
    values = _extract_numeric_values(raw_data)
    insights = []

    if values:
        arr = np.array(values, dtype=float)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        n = len(arr)

        insights.append({
            "icon": "📊",
            "text": f"Analysed {n} data points. Mean = {mean_val:.2f}, Std Dev = {std_val:.2f}",
            "type": "info",
        })

        # Detect outliers via IQR
        q1, q3 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
        iqr = q3 - q1
        outliers = int(np.sum((arr < q1 - 1.5 * iqr) | (arr > q3 + 1.5 * iqr)))
        pct = outliers / n * 100 if n else 0
        color = "danger" if pct > 10 else "warning" if pct > 5 else "success"
        insights.append({
            "icon": "⚠️" if outliers else "✅",
            "text": f"{outliers} outliers detected ({pct:.1f}% of data)",
            "type": color,
        })

        # Simple trend (first half vs second half)
        if n >= 10:
            first_half = np.mean(arr[: n // 2])
            second_half = np.mean(arr[n // 2 :])
            change = second_half - first_half
            direction = "upward" if change > 0 else "downward"
            insights.append({
                "icon": "📈" if change > 0 else "📉",
                "text": f"General {direction} trend ({change:+.2f} change between first and second half)",
                "type": "warning" if abs(change) > std_val else "info",
            })

        # Range insight
        data_range = float(np.max(arr) - np.min(arr))
        insights.append({
            "icon": "📏",
            "text": f"Data range: {float(np.min(arr)):.2f} to {float(np.max(arr)):.2f} (spread {data_range:.2f})",
            "type": "info",
        })
    else:
        insights.append({
            "icon": "ℹ️",
            "text": "No numeric data returned from the API for this location.",
            "type": "warning",
        })

    lat = location.get("lat", "?")
    lon = location.get("lon", "?")
    insights.append({
        "icon": "📍",
        "text": f"Location: ({lat}, {lon})",
        "type": "secondary",
    })

    return dbc.Card([
        dbc.CardHeader(html.H6("💡 Key Insights", className="mb-0")),
        dbc.CardBody([
            html.Div([
                dbc.Alert([
                    html.Span(insight["icon"], className="me-2"),
                    insight["text"]
                ], color=insight["type"], className="mb-2")
                for insight in insights
            ])
        ])
    ])


# ==================== CROSS-DOMAIN LINK CALLBACK ====================

@callback(
    [Output("linked-datasets-store", "data"),
     Output("link-datasets-toast", "is_open"),
     Output("link-datasets-toast", "children"),
     Output("link-datasets-toast", "icon")],
    Input("link-datasets-btn", "n_clicks"),
    [State("primary-dataset-selector", "value"),
     State("secondary-dataset-selector", "value"),
     State("join-key-selector", "value"),
     State("time-tolerance-input", "value"),
     State("time-tolerance-unit", "value")],
    prevent_initial_call=True
)
def link_datasets(n_clicks, primary, secondary, join_key, tolerance, tolerance_unit):
    """Link two datasets for cross-domain analysis and notify the user."""
    if not primary or not secondary:
        return (
            None, True,
            "Please select both a primary and secondary dataset before linking.",
            "warning"
        )

    if primary == secondary:
        return (
            None, True,
            "Primary and secondary datasets must be different.",
            "warning"
        )

    # Look up display names
    cat_lookup = {c["id"]: c["name"] for c in DATA_CATEGORIES}
    primary_name = cat_lookup.get(primary, primary)
    secondary_name = cat_lookup.get(secondary, secondary)

    linked_data = {
        "primary": primary,
        "secondary": secondary,
        "primary_name": primary_name,
        "secondary_name": secondary_name,
        "join_key": join_key or "timestamp",
        "tolerance": tolerance or 1,
        "tolerance_unit": tolerance_unit or "hour",
        "linked_at": datetime.now().isoformat(),
    }

    msg = (
        f"Successfully linked {primary_name} + {secondary_name} "
        f"(join: {join_key or 'timestamp'}, tolerance: {tolerance or 1} {tolerance_unit or 'hour'}). "
        f"View the linked report on the Reports page."
    )

    return linked_data, True, msg, "success"


# ==================== PROGRESS BOX CALLBACKS ====================

@callback(
    Output("progress-entries-analyze", "children"),
    Input("progress-analyze-run", "data"),
    prevent_initial_call=False,
)
def render_analyze_progress(run_prog):
    """Render the analyze page activity log."""
    entries = []
    if run_prog:
        if isinstance(run_prog, list):
            entries.extend(run_prog)
        else:
            entries.append(run_prog)
    else:
        entries.append(make_entry("loading", "Waiting for analysis to start..."))
    return render_entries(entries)


@callback(
    [Output("progress-body-analyze", "is_open"),
     Output("progress-icon-analyze", "className")],
    Input("progress-toggle-analyze", "n_clicks"),
    State("progress-body-analyze", "is_open"),
    prevent_initial_call=True,
)
def toggle_analyze_progress(n, is_open):
    """Toggle the analyze progress box."""
    new_state = not is_open
    return new_state, "fas fa-chevron-up" if new_state else "fas fa-chevron-down"