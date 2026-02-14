"""
Reports Page - Generate and export comprehensive reports.
"""
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta
import json
import io
import base64
import time

from api_client import get_location_data, analyze_location, get_category_data, get_categories_parallel
from components.progress_box import create_progress_box, make_entry, render_entries
from components.charts import (
    create_time_series_chart,
    create_aqi_gauge,
    create_histogram
)
from components.layout import create_report_panel
from data_processing import DataProcessor
from config import REPORT_TYPES, EXPORT_FORMATS, DATA_CATEGORIES, TIME_RANGES, MAP_CONFIG
import numpy as np


def create_reports_layout() -> html.Div:
    """Create the reports generation page layout."""
    return html.Div([
        # Page Header
        html.Div([
            html.H3("📋 Reports", className="mb-2"),
            html.P("Generate comprehensive environmental reports and export data", 
                   className="text-muted")
        ], className="mb-4"),
        
        # Time Range Selector for Reports - Simple Dropdown
        dbc.Card([
            dbc.CardHeader(html.H5("⏱️ Report Time Range", className="mb-0")),
            dbc.CardBody([
                dcc.Dropdown(
                    id="report-time-range",
                    options=[
                        {"label": tr["label"], "value": tr["value"]}
                        for tr in TIME_RANGES if tr["value"] != "custom"
                    ],
                    value="7D",
                    clearable=False,
                    style={"width": "200px"},
                    className="d-inline-block"
                ),
                html.Span(id="report-time-display", className="text-muted ms-3")
            ])
        ], className="mb-4"),
        
        # Report Configuration
        create_report_panel(),

        # Data Source Selector for Reports
        dbc.Card([
            dbc.CardHeader(html.H5("📊 Data Sources", className="mb-0")),
            dbc.CardBody([
                dcc.Dropdown(
                    id="report-category-selector",
                    options=[
                        {"label": f"{cat['icon']} {cat['name']}", "value": cat["id"]}
                        for cat in DATA_CATEGORIES
                    ],
                    value=[cat["id"] for cat in DATA_CATEGORIES],
                    multi=True,
                    placeholder="Select data sources for the report...",
                ),
                html.Small(
                    "Choose which environmental categories to include in the report.",
                    className="text-muted mt-1 d-block",
                ),
            ]),
        ], className="mb-4"),
        
        # Report Templates
        dbc.Card([
            dbc.CardHeader(html.H5("📄 Report Templates", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-chart-line fa-3x text-primary mb-3")
                                ], className="text-center"),
                                html.H6("Executive Summary", className="text-center"),
                                html.P("High-level overview with key metrics and trends", 
                                       className="text-muted small text-center"),
                                dbc.Button("Use Template", id="template-summary-btn", 
                                          color="outline-primary", size="sm", className="w-100")
                            ])
                        ], className="h-100")
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-table fa-3x text-success mb-3")
                                ], className="text-center"),
                                html.H6("Detailed Analysis", className="text-center"),
                                html.P("Comprehensive data tables and statistical analysis", 
                                       className="text-muted small text-center"),
                                dbc.Button("Use Template", id="template-detailed-btn", 
                                          color="outline-success", size="sm", className="w-100")
                            ])
                        ], className="h-100")
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-balance-scale fa-3x text-warning mb-3")
                                ], className="text-center"),
                                html.H6("Compliance Report", className="text-center"),
                                html.P("Regulatory compliance status and exceedances", 
                                       className="text-muted small text-center"),
                                dbc.Button("Use Template", id="template-compliance-btn", 
                                          color="outline-warning", size="sm", className="w-100")
                            ])
                        ], className="h-100")
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-heartbeat fa-3x text-danger mb-3")
                                ], className="text-center"),
                                html.H6("Health Advisory", className="text-center"),
                                html.P("Public health recommendations and alerts", 
                                       className="text-muted small text-center"),
                                dbc.Button("Use Template", id="template-health-btn", 
                                          color="outline-danger", size="sm", className="w-100")
                            ])
                        ], className="h-100")
                    ], md=3)
                ])
            ])
        ], className="mb-4"),
        
        # Scheduled Reports
        dbc.Card([
            dbc.CardHeader([
                html.H5("⏰ Scheduled Reports", className="mb-0"),
                dbc.Button([
                    html.I(className="fas fa-plus me-2"),
                    "New Schedule"
                ], id="new-schedule-btn", color="primary", size="sm")
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Report Name"),
                        html.Th("Type"),
                        html.Th("Frequency"),
                        html.Th("Next Run"),
                        html.Th("Recipients"),
                        html.Th("Actions")
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td("Daily Air Quality Summary"),
                            html.Td(dbc.Badge("Summary", color="primary")),
                            html.Td("Daily @ 8:00 AM"),
                            html.Td("Tomorrow 8:00 AM"),
                            html.Td("team@example.com"),
                            html.Td([
                                dbc.Button(html.I(className="fas fa-edit"), color="link", size="sm"),
                                dbc.Button(html.I(className="fas fa-trash"), color="link", size="sm", className="text-danger")
                            ])
                        ]),
                        html.Tr([
                            html.Td("Weekly Environmental Review"),
                            html.Td(dbc.Badge("Detailed", color="success")),
                            html.Td("Weekly (Monday)"),
                            html.Td("Feb 10, 2026"),
                            html.Td("management@example.com"),
                            html.Td([
                                dbc.Button(html.I(className="fas fa-edit"), color="link", size="sm"),
                                dbc.Button(html.I(className="fas fa-trash"), color="link", size="sm", className="text-danger")
                            ])
                        ])
                    ])
                ], striped=True, hover=True, responsive=True, size="sm")
            ])
        ], className="mb-4"),
        
        # Report Preview
        dbc.Card([
            dbc.CardHeader([
                html.H5("👁️ Report Preview", className="mb-0"),
                dbc.ButtonGroup([
                    dbc.Button([html.I(className="fas fa-print")], id="print-report-btn", 
                              color="outline-secondary", size="sm"),
                    dbc.Button([html.I(className="fas fa-download")], id="download-report-btn", 
                              color="outline-primary", size="sm")
                ])
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dcc.Loading(
                    id="loading-report-preview",
                    type="default",
                    overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                    children=html.Div(id="report-preview-container", children=[
                        html.Div([
                            html.I(className="fas fa-file-alt fa-5x text-muted mb-3"),
                            html.P("Configure your report options above and click 'Generate Report' to see a preview", 
                                   className="text-muted")
                        ], className="text-center py-5")
                    ]),
                )
            ])
        ], className="mb-4"),
        
        # Export History
        dbc.Card([
            dbc.CardHeader(html.H5("📥 Recent Exports", className="mb-0")),
            dbc.CardBody([
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Report"),
                        html.Th("Format"),
                        html.Th("Size"),
                        html.Th("Generated"),
                        html.Th("Download")
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td("Air Quality Report - San Francisco"),
                            html.Td(dbc.Badge("PDF", color="danger")),
                            html.Td("2.4 MB"),
                            html.Td("5 minutes ago"),
                            html.Td(dbc.Button(html.I(className="fas fa-download"), color="link", size="sm"))
                        ]),
                        html.Tr([
                            html.Td("Environmental Data Export"),
                            html.Td(dbc.Badge("CSV", color="success")),
                            html.Td("1.8 MB"),
                            html.Td("2 hours ago"),
                            html.Td(dbc.Button(html.I(className="fas fa-download"), color="link", size="sm"))
                        ]),
                        html.Tr([
                            html.Td("Weekly Summary Charts"),
                            html.Td(dbc.Badge("PNG", color="info")),
                            html.Td("856 KB"),
                            html.Td("Yesterday"),
                            html.Td(dbc.Button(html.I(className="fas fa-download"), color="link", size="sm"))
                        ])
                    ])
                ], striped=True, hover=True, responsive=True, size="sm")
            ])
        ]),
        
        # Hidden stores
        dcc.Store(id="report-config-store"),
        dcc.Download(id="report-download"),
        
        # Schedule Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Schedule New Report")),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Report Name"),
                            dbc.Input(id="schedule-name", placeholder="Enter report name")
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Report Type"),
                            dcc.Dropdown(
                                id="schedule-type",
                                options=[{"label": rt["name"], "value": rt["id"]} for rt in REPORT_TYPES],
                                value="summary"
                            )
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Frequency"),
                            dcc.Dropdown(
                                id="schedule-frequency",
                                options=[
                                    {"label": "Daily", "value": "daily"},
                                    {"label": "Weekly", "value": "weekly"},
                                    {"label": "Monthly", "value": "monthly"}
                                ],
                                value="daily"
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Time"),
                            dbc.Input(id="schedule-time", type="time", value="08:00")
                        ], md=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Recipients (comma-separated)"),
                            dbc.Input(id="schedule-recipients", placeholder="email@example.com")
                        ])
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-schedule-btn", color="secondary"),
                dbc.Button("Create Schedule", id="create-schedule-btn", color="primary")
            ])
        ], id="schedule-modal", is_open=False),

        # ── Activity Log ──
        create_progress_box("reports", [
            "progress-reports-gen",
        ]),
    ])


# ==================== TIME RANGE CALLBACK ====================

@callback(
    Output("report-time-display", "children"),
    Input("report-time-range", "value"),
    prevent_initial_call=False
)
def handle_report_time_dropdown(selected_value):
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
    [Output("report-preview-container", "children"),
     Output("progress-reports-gen", "data")],
    [Input("generate-report-btn", "n_clicks"),
     Input("report-type-selector", "value")],
    [State("export-format-selector", "value"),
     State("report-sections-checklist", "value"),
     State("report-title-input", "value"),
     State("report-author-input", "value"),
     State("report-time-range", "value"),
     State("report-category-selector", "value"),
     State("latitude-input", "value"),
     State("longitude-input", "value"),
     State("linked-datasets-store", "data")],
    prevent_initial_call=False
)
def generate_report_preview(
    n_clicks, report_type, export_format, sections, title, author,
    time_range, categories, lat, lon, linked_datasets,
):
    """Generate a preview of the report using REAL API data.
    
    Triggers on Generate button click AND report-type-selector changes
    (which happen when template buttons are used).
    """
    _t0 = time.time()
    if not sections:
        sections = ["summary", "charts", "statistics"]

    title = title or "Environmental Report"
    author = author or "Environmental Monitoring System"
    lat = lat or MAP_CONFIG["default_lat"]
    lon = lon or MAP_CONFIG["default_lon"]
    categories = categories or ["air_quality", "weather"]

    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365,
    }
    time_labels = {
        "1H": "Last 1 Hour", "6H": "Last 6 Hours", "24H": "Last 24 Hours",
        "7D": "Last 7 Days", "30D": "Last 30 Days", "90D": "Last 90 Days", "1Y": "Last Year",
    }
    days = time_to_days.get(time_range, 7)
    time_label = time_labels.get(time_range, "Last 7 Days")

    # ---- Fetch real data from API (parallel) ----
    all_data = {}
    api_results = get_categories_parallel(categories, lat, lon)
    for cat_id in categories:
        try:
            resp = api_results.get(cat_id, {})
            sources = resp.get("data") or resp.get("sources") or []
            combined: dict = {}
            for src in sources:
                if isinstance(src, dict):
                    src_data = src.get("data", src)
                    if isinstance(src_data, dict):
                        for k, v in src_data.items():
                            if k not in combined:
                                combined[k] = v
                            elif isinstance(v, list) and isinstance(combined[k], list):
                                combined[k].extend(v)
            if combined:
                all_data[cat_id] = combined
        except Exception:
            pass

    preview_sections = []

    # ---- Header ----
    report_type_display = (report_type or "summary").title()
    preview_sections.append(html.Div([
        html.H2(title, className="text-center mb-2"),
        # Report type - bold and boxed
        html.Div([
            html.Span(
                report_type_display,
                style={
                    "fontWeight": "700",
                    "fontSize": "1.1rem",
                    "border": "2px solid #2E86AB",
                    "borderRadius": "6px",
                    "padding": "4px 16px",
                    "color": "#2E86AB",
                    "display": "inline-block",
                }
            )
        ], className="text-center mb-2"),
        html.P(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}",
               className="text-center text-muted"),
        html.P(f"Author: {author} | Location: ({lat:.4f}, {lon:.4f})",
               className="text-center text-muted"),
        html.Hr(),
    ]))

    # ---- Executive Summary (real data) ----
    if "summary" in sections:
        cards = []
        # AQI from air quality
        aq = all_data.get("air_quality", {})
        aq_vals = _extract_vals("air_quality", aq)
        if aq_vals:
            avg_aqi = sum(aq_vals) / len(aq_vals)
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{avg_aqi:.0f}", className="text-success"),
                html.P("Avg AQI", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Temperature from weather
        wx = all_data.get("weather", {})
        current = wx.get("current_weather", {})
        if current:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{current.get('temperature', '?')}°C", className="text-primary"),
                html.P("Current Temp", className="text-muted mb-0"),
            ]), className="text-center"), md=3))
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{current.get('windspeed', '?')} km/h", className="text-info"),
                html.P("Wind Speed", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Earthquakes count
        eq = all_data.get("earthquakes", {})
        features = eq.get("features", [])
        if features:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(str(len(features)), className="text-warning"),
                html.P("Earthquakes", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Water stations count
        wt = all_data.get("water", {})
        time_series = wt.get("value", {}).get("timeSeries", [])
        if time_series:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(str(len(time_series)), className="text-info"),
                html.P("Water Stations", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Biodiversity observations
        bio = all_data.get("biodiversity", {})
        bio_results = bio.get("results", [])
        if bio_results:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(str(len(bio_results)), className="text-success"),
                html.P("Species Obs.", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Climate data
        cl = all_data.get("climate", {})
        cl_daily = cl.get("daily", {})
        if cl_daily and cl_daily.get("temperature_2m_max"):
            t_max = cl_daily["temperature_2m_max"]
            avg_max = sum(float(v) for v in t_max if v is not None) / len(t_max) if t_max else 0
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{avg_max:.1f}°C", className="text-danger"),
                html.P("Avg Max Temp", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Marine data — wave height
        mr = all_data.get("marine", {})
        mr_current = mr.get("current") or {}
        if isinstance(mr_current, dict) and mr_current.get("wave_height") is not None:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{mr_current['wave_height']:.1f}m", className="text-info"),
                html.P("Wave Height", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Radiation — peak UV index
        rd = all_data.get("radiation", {})
        rd_hourly = (rd.get("hourly") or {}).get("uv_index", [])
        rd_clean = [float(v) for v in rd_hourly if v is not None] if isinstance(rd_hourly, list) else []
        if rd_clean:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(f"{max(rd_clean):.1f}", className="text-warning"),
                html.P("Peak UV Index", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Wildfires — active fires count
        wf = all_data.get("wildfires", {})
        wf_features = wf.get("features", wf.get("incidents", []))
        if isinstance(wf_features, list) and wf_features:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3(str(len(wf_features)), className="text-danger"),
                html.P("Active Fires", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        # Soil — top property
        sl = all_data.get("soil", {})
        sl_layers = (sl.get("properties") or {}).get("layers", [])
        if isinstance(sl_layers, list) and sl_layers:
            first_layer = sl_layers[0]
            if isinstance(first_layer, dict):
                sl_name = first_layer.get("name", "Soil")
                sl_depths = first_layer.get("depths", [])
                if sl_depths and isinstance(sl_depths, list):
                    sl_mean = (sl_depths[0].get("values") or {}).get("mean")
                    if sl_mean is not None:
                        cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                            html.H3(f"{float(sl_mean):.1f}", className="text-dark"),
                            html.P(f"Soil: {sl_name}", className="text-muted mb-0"),
                        ]), className="text-center"), md=3))

        if not cards:
            cards.append(dbc.Col(dbc.Card(dbc.CardBody([
                html.H3("—", className="text-muted"),
                html.P("No data", className="text-muted mb-0"),
            ]), className="text-center"), md=3))

        preview_sections.append(html.Div([
            html.H4("Executive Summary"),
            html.P(f"Report covering {len(all_data)} data source(s) for the {time_label.lower()} period."),
            dbc.Row(cards, className="mb-4"),
        ]))

    # ---- Data Tables (real) ----
    if "tables" in sections:
        tables = []
        for cat_id, cdata in all_data.items():
            rows = _extract_table_rows(cat_id, cdata)
            if rows:
                headers = list(rows[0].keys())
                tables.append(html.Div([
                    html.H5(cat_id.replace("_", " ").title()),
                    dbc.Table([
                        html.Thead(html.Tr([html.Th(h) for h in headers])),
                        html.Tbody([
                            html.Tr([html.Td(str(r.get(h, ""))[:40]) for h in headers])
                            for r in rows[:10]
                        ]),
                    ], striped=True, bordered=True, responsive=True, size="sm"),
                ]))
        if tables:
            preview_sections.append(html.Div([html.H4("Data Tables")] + tables + [html.Hr()]))

    # ---- Charts (real data) ----
    if "charts" in sections:
        chart_elems = []
        # Weather temperature chart
        wx = all_data.get("weather", {})
        hourly = wx.get("hourly", {})
        temps = hourly.get("temperature_2m", [])[:48]
        times = hourly.get("time", [])[:48]
        if temps and times:
            try:
                idx = pd.to_datetime(times)
                df = pd.DataFrame({"Temperature": [float(t) for t in temps]}, index=idx)
                fig = create_time_series_chart(
                    df, columns=["Temperature"],
                    title=f"Temperature — {time_label}",
                    y_title="°C", show_range_slider=False,
                    show_range_buttons=False, height=350,
                )
                chart_elems.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))
            except Exception:
                pass

        # Earthquake magnitude scatter
        eq = all_data.get("earthquakes", {})
        features = eq.get("features", [])
        if features:
            try:
                mags = [f.get("properties", {}).get("mag", 0) or 0 for f in features[:25]]
                places = [str(f.get("properties", {}).get("place", ""))[:25] for f in features[:25]]
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=places, y=mags, marker_color="#C73E1D",
                    text=[f"M{m:.1f}" for m in mags], textposition="outside",
                ))
                fig.update_layout(
                    title="Recent Earthquakes by Magnitude",
                    yaxis_title="Magnitude", height=350,
                    margin=dict(l=50, r=30, t=50, b=100),
                    xaxis_tickangle=-45,
                )
                chart_elems.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))
            except Exception:
                pass

        # Climate temperature range
        cl = all_data.get("climate", {})
        daily = cl.get("daily", {})
        if daily and daily.get("time"):
            try:
                c_times = daily["time"][:30]
                t_max = daily.get("temperature_2m_max", [])[:30]
                t_min = daily.get("temperature_2m_min", [])[:30]
                if t_max:
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    if t_min:
                        fig.add_trace(go.Scatter(x=c_times, y=t_min, mode="lines", name="Min", line=dict(color="#2E86AB")))
                    fig.add_trace(go.Scatter(x=c_times, y=t_max, mode="lines", name="Max",
                                             line=dict(color="#C73E1D"), fill="tonexty" if t_min else None))
                    fig.update_layout(title="Climate Temperature Range", yaxis_title="°C", height=350,
                                      margin=dict(l=50, r=30, t=50, b=50))
                    chart_elems.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))
            except Exception:
                pass

        # Air quality bar chart
        aq = all_data.get("air_quality", {})
        aq_vals = _extract_vals("air_quality", aq)
        if aq_vals:
            try:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Bar(y=list(range(len(aq_vals))), x=aq_vals[:20], orientation="h",
                                     marker_color="#2E86AB"))
                fig.update_layout(title="Air Quality Values", xaxis_title="Value", height=300,
                                  margin=dict(l=50, r=30, t=50, b=50))
                chart_elems.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))
            except Exception:
                pass

        if chart_elems:
            preview_sections.append(html.Div([html.H4("Charts & Visualizations")] + chart_elems + [html.Hr()]))
        else:
            preview_sections.append(html.Div([
                html.H4("Charts & Visualizations"),
                dbc.Alert("No chart data available for the selected categories.", color="info"),
                html.Hr(),
            ]))

    # ---- Statistics (real) ----
    if "statistics" in sections:
        stat_rows = []
        for cat_id, cdata in all_data.items():
            vals = _extract_vals(cat_id, cdata)
            if vals:
                arr = np.array(vals, dtype=float)
                stat_rows.append(html.Tr([
                    html.Td(cat_id.replace("_", " ").title()),
                    html.Td(f"{np.mean(arr):.2f}"),
                    html.Td(f"{np.median(arr):.2f}"),
                    html.Td(f"{np.min(arr):.2f}"),
                    html.Td(f"{np.max(arr):.2f}"),
                    html.Td(f"{np.std(arr):.2f}"),
                    html.Td(f"{len(vals)}"),
                ]))
        if stat_rows:
            preview_sections.append(html.Div([
                html.H4("Statistical Summary"),
                dbc.Table([
                    html.Thead(html.Tr([html.Th(h) for h in ["Category", "Mean", "Median", "Min", "Max", "Std Dev", "N"]])),
                    html.Tbody(stat_rows),
                ], striped=True, bordered=True, responsive=True, size="sm"),
                html.Hr(),
            ]))
        else:
            preview_sections.append(html.Div([
                html.H4("Statistical Summary"),
                dbc.Alert("Insufficient numeric data for statistical analysis.", color="info"),
                html.Hr(),
            ]))

    # ---- Trend Analysis (real data) ----
    if "trends" in sections:
        trend_elems = []
        for cat_id, cdata in all_data.items():
            vals = _extract_vals(cat_id, cdata)
            if len(vals) >= 3:
                arr = np.array(vals, dtype=float)
                # Simple trend: compare first half mean vs second half mean
                mid = len(arr) // 2
                first_half = np.mean(arr[:mid])
                second_half = np.mean(arr[mid:])
                change_pct = ((second_half - first_half) / first_half * 100) if first_half != 0 else 0
                if abs(change_pct) > 10:
                    direction = "increasing" if change_pct > 0 else "decreasing"
                    color = "danger" if change_pct > 0 and cat_id in ("air_quality", "radiation", "wildfires") else "warning" if change_pct > 0 else "success"
                    trend_elems.append(dbc.Alert(
                        f"{cat_id.replace('_', ' ').title()}: {direction} trend ({change_pct:+.1f}%) — "
                        f"early avg {first_half:.1f} vs recent avg {second_half:.1f}",
                        color=color,
                    ))
                else:
                    trend_elems.append(dbc.Alert(
                        f"{cat_id.replace('_', ' ').title()}: stable ({change_pct:+.1f}% change)",
                        color="info",
                    ))
        if trend_elems:
            preview_sections.append(html.Div([html.H4("Trend Analysis")] + trend_elems + [html.Hr()]))
        else:
            preview_sections.append(html.Div([
                html.H4("Trend Analysis"),
                dbc.Alert("Not enough data points for trend analysis. Try a longer time range.", color="info"),
                html.Hr(),
            ]))

    # ---- Anomaly Report (real data) ----
    if "anomalies" in sections:
        anomaly_elems = []
        for cat_id, cdata in all_data.items():
            vals = _extract_vals(cat_id, cdata)
            if len(vals) >= 5:
                arr = np.array(vals, dtype=float)
                mean = np.mean(arr)
                std = np.std(arr)
                if std > 0:
                    # Flag values > 2 standard deviations from mean
                    anomalies_found = []
                    for i, v in enumerate(vals):
                        z_score = abs(v - mean) / std
                        if z_score > 2.0:
                            anomalies_found.append({"index": i, "value": v, "z_score": z_score})
                    if anomalies_found:
                        for a in anomalies_found[:5]:
                            anomaly_elems.append(dbc.Alert(
                                f"{cat_id.replace('_', ' ').title()} — "
                                f"Anomaly detected: value {a['value']:.2f} "
                                f"(z-score: {a['z_score']:.1f}, mean: {mean:.2f}, std: {std:.2f})",
                                color="warning",
                            ))
        if anomaly_elems:
            preview_sections.append(html.Div([html.H4("Anomaly Report")] + anomaly_elems + [html.Hr()]))
        else:
            preview_sections.append(html.Div([
                html.H4("Anomaly Report"),
                dbc.Alert("No anomalies detected — all values within normal range (2 sigma).", color="success"),
                html.Hr(),
            ]))

    # ---- Compliance (report_type aware) ----
    if report_type == "compliance" and "recommendations" in sections:
        preview_sections.append(html.Div([
            html.H4("Compliance Summary"),
            _build_compliance_section(all_data),
            html.Hr(),
        ]))

    # ---- Health advisory ----
    if report_type in ("health", "health_advisory") and "recommendations" in sections:
        preview_sections.append(html.Div([
            html.H4("Health Advisory"),
            _build_health_section(all_data),
            html.Hr(),
        ]))

    # ---- Generic recommendations ----
    if "recommendations" in sections and report_type not in ("compliance", "health"):
        preview_sections.append(html.Div([
            html.H4("Recommendations"),
            dbc.Alert("Review the data above and consult local guidelines.", color="info"),
        ]))

    _elapsed = int((time.time() - _t0) * 1000)
    _prog = [
        make_entry("info", f"Generating {(report_type or 'summary').title()} report for ({lat:.2f}, {lon:.2f})"),
        make_entry("complete", f"Fetched {len(all_data)} data sources, {len(sections)} sections", duration_ms=_elapsed),
        make_entry("separator", ""),
        make_entry("success", "Report generated"),
    ]

    return html.Div([
        dbc.Card([
            dbc.CardBody(preview_sections, style={"maxHeight": "700px", "overflow": "auto"})
        ], className="border shadow-sm"),
        html.Div([
            dbc.Badge(f"Format: {(export_format or 'csv').upper()}", color="primary", className="me-2"),
            html.Span(
                f"Type: {(report_type or 'summary').title()}",
                style={
                    "fontWeight": "700",
                    "border": "2px solid #6c757d",
                    "borderRadius": "4px",
                    "padding": "2px 10px",
                    "fontSize": "0.85rem",
                    "marginRight": "8px",
                }
            ),
            dbc.Badge(f"Sections: {len(sections)}", color="info"),
            dbc.Badge(f"Sources: {len(all_data)}", color="success", className="ms-2"),
        ], className="mt-3 text-center"),
    ]), _prog


def _extract_table_rows(cat_id: str, data: dict) -> list:
    """Extract tabular rows from API data for a category."""
    rows = []
    if cat_id == "earthquakes":
        for f in data.get("features", [])[:10]:
            p = f.get("properties", {})
            rows.append({"Magnitude": p.get("mag", ""), "Place": str(p.get("place", ""))[:30], "Time": str(p.get("time", ""))})
    elif cat_id == "air_quality":
        # Try Open-Meteo current{} format
        current_aq = data.get("current") or {}
        if isinstance(current_aq, dict):
            for key in ("us_aqi", "pm2_5", "pm10", "ozone", "carbon_monoxide",
                         "nitrogen_dioxide", "sulphur_dioxide"):
                val = current_aq.get(key)
                if val is not None:
                    rows.append({"Parameter": key.replace("_", " ").title(), "Value": val, "Unit": ""})
        # Try OpenAQ locations format (results[] with parameters[])
        if not rows:
            for loc in data.get("results", [])[:10]:
                if isinstance(loc, dict):
                    for p in loc.get("parameters", []):
                        if isinstance(p, dict):
                            rows.append({
                                "Parameter": p.get("parameter", ""),
                                "Value": p.get("lastValue", p.get("average", "")),
                                "Unit": p.get("unit", ""),
                                "Station": str(loc.get("name", loc.get("location", "")))[:25],
                            })
                    # Legacy measurement format
                    if loc.get("parameter") and loc.get("value") is not None:
                        rows.append({"Parameter": loc["parameter"], "Value": loc["value"], "Unit": loc.get("unit", "")})
        # Try measurements format
        if not rows:
            for m in data.get("measurements", [])[:10]:
                if isinstance(m, dict):
                    rows.append({"Parameter": m.get("parameter", ""), "Value": m.get("value", ""), "Unit": m.get("unit", "")})
        # Try Open-Meteo flat keys
        if not rows:
            for key in ("us_aqi", "pm2_5", "pm10", "ozone", "carbon_monoxide", "nitrogen_dioxide"):
                val = data.get(key)
                if val is not None:
                    if isinstance(val, list):
                        val = val[0] if val else None
                    if val is not None:
                        rows.append({"Parameter": key.replace("_", " ").title(), "Value": val, "Unit": ""})
    elif cat_id == "weather":
        current = data.get("current_weather", {})
        if current:
            rows.append({"Metric": "Temperature", "Value": current.get("temperature", ""), "Unit": "C"})
            rows.append({"Metric": "Wind Speed", "Value": current.get("windspeed", ""), "Unit": "km/h"})
            rows.append({"Metric": "Wind Direction", "Value": current.get("winddirection", ""), "Unit": "deg"})
            rows.append({"Metric": "Weather Code", "Value": current.get("weathercode", ""), "Unit": ""})
    elif cat_id == "radiation":
        # Try Open-Meteo UV hourly format
        hourly_rad = data.get("hourly") or {}
        if isinstance(hourly_rad, dict) and hourly_rad.get("time"):
            times = hourly_rad.get("time", [])[:10]
            uv = hourly_rad.get("uv_index", [])
            direct = hourly_rad.get("direct_radiation", [])
            shortwave = hourly_rad.get("shortwave_radiation", [])
            for i, t in enumerate(times):
                row = {"Time": t}
                if i < len(uv) and uv[i] is not None:
                    row["UV Index"] = uv[i]
                if i < len(direct) and direct[i] is not None:
                    row["Direct (W/m²)"] = direct[i]
                if i < len(shortwave) and shortwave[i] is not None:
                    row["Shortwave (W/m²)"] = shortwave[i]
                rows.append(row)
        # Legacy measurements format
        if not rows:
            for m in data.get("measurements", [])[:10]:
                if isinstance(m, dict):
                    loc = m.get("location", m.get("city", ""))
                    rows.append({"Location": loc, "Value": m.get("value", ""), "Unit": m.get("unit", "cpm")})
    elif cat_id == "wildfires":
        for i in data.get("incidents", [])[:10]:
            if isinstance(i, dict):
                acres_raw = i.get("acres_burned", i.get("acres", ""))
                try:
                    acres = f"{float(str(acres_raw).replace(',', '')):,.0f}" if acres_raw else ""
                except (ValueError, TypeError):
                    acres = str(acres_raw)
                rows.append({"Name": str(i.get("title", ""))[:25], "Acres": acres, "Contained": f"{i.get('percent_contained', 0)}%"})
        # Try GeoJSON features
        if not rows:
            for f in data.get("features", [])[:10]:
                props = f.get("properties", f.get("attributes", {})) if isinstance(f, dict) else {}
                if isinstance(props, dict) and props:
                    name = props.get("IncidentName", props.get("poly_IncidentName", "Fire"))
                    acres = props.get("GISAcres", props.get("irwin_DailyAcres", ""))
                    rows.append({"Name": str(name)[:25], "Acres": str(acres), "Contained": ""})
    elif cat_id == "water":
        for ts in data.get("value", {}).get("timeSeries", [])[:10]:
            if isinstance(ts, dict):
                site = ts.get("sourceInfo", {}).get("siteName", "Unknown")
                var_name = ts.get("variable", {}).get("variableName", "Flow")
                try:
                    val = float(ts.get("values", [{}])[0].get("value", [{}])[0].get("value", 0))
                    rows.append({"Station": str(site)[:25], "Parameter": var_name, "Value": f"{val:,.1f}"})
                except (IndexError, TypeError, ValueError):
                    pass
    elif cat_id == "climate":
        daily = data.get("daily", {})
        if isinstance(daily, dict) and daily.get("time"):
            times = daily["time"][:7]
            t_max = daily.get("temperature_2m_max", [])[:7]
            t_min = daily.get("temperature_2m_min", [])[:7]
            precip = daily.get("precipitation_sum", [])[:7]
            for i, t in enumerate(times):
                row = {"Date": t}
                if i < len(t_max):
                    row["Max Temp (C)"] = t_max[i]
                if i < len(t_min):
                    row["Min Temp (C)"] = t_min[i]
                if i < len(precip):
                    row["Precip (mm)"] = precip[i]
                rows.append(row)
    elif cat_id == "marine":
        # Try Open-Meteo Marine current{} format
        current_marine = data.get("current") or {}
        if isinstance(current_marine, dict):
            for key in ("wave_height", "wave_direction", "wave_period", "sea_surface_temperature"):
                val = current_marine.get(key)
                if val is not None:
                    rows.append({"Metric": key.replace("_", " ").title(), "Value": val, "Unit": ""})
        # Try Open-Meteo Marine hourly format
        if not rows:
            hourly_marine = data.get("hourly") or {}
            if isinstance(hourly_marine, dict) and hourly_marine.get("time"):
                times = hourly_marine.get("time", [])[:10]
                wh = hourly_marine.get("wave_height", [])
                sst = hourly_marine.get("sea_surface_temperature", [])
                for i, t in enumerate(times):
                    row = {"Time": t}
                    if i < len(wh) and wh[i] is not None:
                        row["Wave Height (m)"] = wh[i]
                    if i < len(sst) and sst[i] is not None:
                        row["SST (°C)"] = sst[i]
                    rows.append(row)
        # Legacy stations format
        if not rows:
            for s in data.get("stations", [])[:10]:
                if isinstance(s, dict):
                    rows.append({
                        "Station": str(s.get("name", "Station"))[:25],
                        "Water Level": s.get("water_level", "N/A"),
                        "Wave Height": s.get("wave_height", "N/A"),
                    })
        if not rows:
            for obs in data.get("observations", [])[:10]:
                if isinstance(obs, dict):
                    rows.append({
                        "Station": str(obs.get("station", obs.get("stationId", "")))[:25],
                        "Wave Height": obs.get("waveHeight", obs.get("wvht", "N/A")),
                        "Wind Speed": obs.get("windSpeed", obs.get("wspd", "N/A")),
                    })
    elif cat_id == "biodiversity":
        for r in data.get("results", [])[:10]:
            if isinstance(r, dict):
                rows.append({
                    "Species": r.get("species", r.get("scientificName", "Unknown"))[:30],
                    "Country": r.get("country", ""),
                    "Year": r.get("year", ""),
                })
    elif cat_id == "soil":
        layers = data.get("properties", {}).get("layers", [])
        if isinstance(layers, list):
            for layer in layers[:10]:
                if isinstance(layer, dict):
                    name = layer.get("name", "Unknown")
                    unit = layer.get("unit_measure", {}).get("mapped_units", "")
                    depths = layer.get("depths", [])
                    mean_val = ""
                    if depths and isinstance(depths, list):
                        mean_val = depths[0].get("values", {}).get("mean", "")
                    rows.append({"Property": name, "Value": mean_val, "Unit": unit})
        if not rows:
            # Generic flat data
            for k, v in data.items():
                if k.startswith("_") or not isinstance(v, (int, float, str)):
                    continue
                rows.append({"Property": k.replace("_", " ").title(), "Value": str(v)})
                if len(rows) >= 10:
                    break
    return rows


def _extract_vals(cat_id: str, data: dict) -> list:
    """Extract numeric values from category data for statistical analysis."""
    vals = []
    if cat_id == "earthquakes":
        for f in data.get("features", []):
            m = f.get("properties", {}).get("mag")
            if m is not None:
                try:
                    vals.append(float(m))
                except (ValueError, TypeError):
                    pass
    elif cat_id == "air_quality":
        # Try Open-Meteo current{} values
        current_aq = data.get("current") or {}
        if isinstance(current_aq, dict):
            for key in ("us_aqi", "pm2_5", "pm10", "ozone"):
                v = current_aq.get(key)
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
        # Try Open-Meteo flat values
        if not vals:
            for key in ("us_aqi", "pm2_5", "pm10", "ozone"):
                raw = data.get(key)
                if isinstance(raw, list):
                    for v in raw:
                        if v is not None:
                            try:
                                vals.append(float(v))
                            except (ValueError, TypeError):
                                pass
                elif raw is not None:
                    try:
                        vals.append(float(raw))
                    except (ValueError, TypeError):
                        pass
                if vals:
                    break
        # Try hourly sub-dict
        if not vals:
            hourly = data.get("hourly", {})
            if isinstance(hourly, dict):
                for key in ("us_aqi", "pm2_5", "pm10"):
                    raw = hourly.get(key, [])
                    if isinstance(raw, list):
                        for v in raw:
                            if v is not None:
                                try:
                                    vals.append(float(v))
                                except (ValueError, TypeError):
                                    pass
                    if vals:
                        break
        # Try OpenAQ locations format
        if not vals:
            for loc in data.get("results", []):
                if isinstance(loc, dict):
                    for p in loc.get("parameters", []):
                        if isinstance(p, dict):
                            v = p.get("lastValue") or p.get("average")
                            if v is not None:
                                try:
                                    vals.append(float(v))
                                except (ValueError, TypeError):
                                    pass
                    if loc.get("value") is not None:
                        try:
                            vals.append(float(loc["value"]))
                        except (ValueError, TypeError):
                            pass
        # Legacy measurements
        if not vals:
            for m in data.get("measurements", []):
                v = m.get("value") if isinstance(m, dict) else None
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
    elif cat_id == "weather":
        for v in data.get("hourly", {}).get("temperature_2m", []):
            try:
                vals.append(float(v))
            except (ValueError, TypeError):
                pass
    elif cat_id == "radiation":
        # Try Open-Meteo UV hourly format
        hourly_rad = data.get("hourly") or {}
        if isinstance(hourly_rad, dict):
            for key in ("uv_index", "direct_radiation", "shortwave_radiation"):
                raw = hourly_rad.get(key, [])
                if isinstance(raw, list):
                    for v in raw:
                        if v is not None:
                            try:
                                vals.append(float(v))
                            except (ValueError, TypeError):
                                pass
                if vals:
                    break
        # Legacy measurements format
        if not vals:
            for m in data.get("measurements", []):
                v = m.get("value") if isinstance(m, dict) else None
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
    elif cat_id == "water":
        for ts in data.get("value", {}).get("timeSeries", []):
            try:
                vals.append(float(ts.get("values", [{}])[0].get("value", [{}])[0].get("value", 0)))
            except (IndexError, TypeError, ValueError):
                pass
    elif cat_id == "climate":
        for v in data.get("daily", {}).get("temperature_2m_max", []):
            try:
                vals.append(float(v))
            except (ValueError, TypeError):
                pass
    elif cat_id == "marine":
        # Try Open-Meteo Marine hourly format
        hourly_marine = data.get("hourly") or {}
        if isinstance(hourly_marine, dict):
            for key in ("wave_height", "wave_period", "sea_surface_temperature"):
                raw = hourly_marine.get(key, [])
                if isinstance(raw, list):
                    for v in raw:
                        if v is not None:
                            try:
                                vals.append(float(v))
                            except (ValueError, TypeError):
                                pass
                if vals:
                    break
        # Try Open-Meteo Marine current{} format
        if not vals:
            current_marine = data.get("current") or {}
            if isinstance(current_marine, dict):
                for key in ("wave_height", "wave_period", "sea_surface_temperature"):
                    v = current_marine.get(key)
                    if v is not None:
                        try:
                            vals.append(float(v))
                        except (ValueError, TypeError):
                            pass
        # Legacy stations format
        if not vals:
            for s in data.get("stations", []):
                if isinstance(s, dict):
                    v = s.get("water_level", s.get("wave_height"))
                    if v is not None:
                        try:
                            vals.append(float(v))
                        except (ValueError, TypeError):
                            pass
        if not vals:
            for obs in data.get("observations", []):
                if isinstance(obs, dict):
                    for key in ("waveHeight", "wvht", "waterLevel", "water_level"):
                        v = obs.get(key)
                        if v is not None:
                            try:
                                vals.append(float(v))
                                break
                            except (ValueError, TypeError):
                                pass
    elif cat_id == "biodiversity":
        # Count observations per species
        species_counts: dict = {}
        for r in data.get("results", []):
            if isinstance(r, dict):
                sp = r.get("species", r.get("scientificName", "Unknown"))
                species_counts[sp] = species_counts.get(sp, 0) + 1
        vals = list(species_counts.values())
    elif cat_id == "wildfires":
        for i in data.get("incidents", []):
            if isinstance(i, dict):
                acres = i.get("acres_burned", i.get("acres", 0))
                try:
                    vals.append(float(str(acres).replace(",", "")) if acres else 0)
                except (ValueError, TypeError):
                    pass
        if not vals:
            for f in data.get("features", []):
                props = f.get("properties", f.get("attributes", {})) if isinstance(f, dict) else {}
                if isinstance(props, dict):
                    acres = props.get("GISAcres", props.get("irwin_DailyAcres"))
                    if acres is not None:
                        try:
                            vals.append(float(str(acres).replace(",", "")))
                        except (ValueError, TypeError):
                            pass
    elif cat_id == "soil":
        for layer in data.get("properties", {}).get("layers", []):
            if isinstance(layer, dict):
                depths = layer.get("depths", [])
                if depths and isinstance(depths, list):
                    mean_val = depths[0].get("values", {}).get("mean")
                    if mean_val is not None:
                        try:
                            vals.append(float(mean_val))
                        except (ValueError, TypeError):
                            pass
    return vals


def _build_compliance_section(all_data: dict):
    """Build compliance alerts from real data."""
    alerts = []
    aq = all_data.get("air_quality", {})
    aq_vals = _extract_vals("air_quality", aq)
    for val in aq_vals[:5]:
        if val > 100:
            alerts.append(dbc.Alert(f"[EXCEEDANCE] AQ value = {val:.1f} (threshold 100)", color="danger"))

    # Check earthquake magnitudes
    eq = all_data.get("earthquakes", {})
    for f in eq.get("features", [])[:5]:
        mag = f.get("properties", {}).get("mag")
        if mag is not None and float(mag) >= 4.0:
            place = f.get("properties", {}).get("place", "Unknown")
            alerts.append(dbc.Alert(f"[SEISMIC] M{mag} earthquake near {place}", color="warning"))

    if not alerts:
        alerts.append(dbc.Alert("All parameters within compliance limits.", color="success"))
    return html.Div(alerts)


def _build_health_section(all_data: dict):
    """Build health advisory from real data."""
    items = []
    aq_vals = _extract_vals("air_quality", all_data.get("air_quality", {}))
    if aq_vals:
        avg = sum(aq_vals) / len(aq_vals)
        if avg > 150:
            items.append(dbc.Alert("Air quality is unhealthy. Limit outdoor activity.", color="danger"))
        elif avg > 100:
            items.append(dbc.Alert("Air quality is moderate. Sensitive groups should limit exposure.", color="warning"))
        else:
            items.append(dbc.Alert("Air quality is good. No restrictions.", color="success"))

    # Weather-based health advisory
    wx = all_data.get("weather", {})
    current = wx.get("current_weather", {})
    if current:
        temp = current.get("temperature")
        if temp is not None:
            temp_f = float(temp)
            if temp_f > 35:
                items.append(dbc.Alert(f"Extreme heat warning: {temp_f}°C. Stay hydrated and avoid prolonged sun exposure.", color="danger"))
            elif temp_f < -10:
                items.append(dbc.Alert(f"Extreme cold warning: {temp_f}°C. Risk of hypothermia.", color="danger"))

    if not items:
        items.append(dbc.Alert("Insufficient data for health advisory.", color="info"))
    return html.Div(items)


@callback(
    Output("schedule-modal", "is_open"),
    [Input("new-schedule-btn", "n_clicks"),
     Input("cancel-schedule-btn", "n_clicks"),
     Input("create-schedule-btn", "n_clicks")],
    State("schedule-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_schedule_modal(open_clicks, cancel_clicks, create_clicks, is_open):
    """Toggle the schedule modal."""
    return not is_open


@callback(
    Output("report-download", "data"),
    Input("download-report-btn", "n_clicks"),
    [State("export-format-selector", "value"),
     State("report-title-input", "value"),
     State("report-time-range", "value"),
     State("report-category-selector", "value"),
     State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=True
)
def download_report(n_clicks, export_format, title, time_range, categories, lat, lon):
    """Generate and download the report from real API data."""
    title = title or "Environmental_Report"
    filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
    lat = lat or MAP_CONFIG["default_lat"]
    lon = lon or MAP_CONFIG["default_lon"]
    categories = categories or ["air_quality", "weather"]

    # Fetch real data
    all_rows = []
    raw_export = {}
    for cat_id in categories:
        try:
            resp = get_category_data(cat_id, lat=lat, lon=lon)
            raw_export[cat_id] = resp
            sources = resp.get("data") or resp.get("sources") or []
            for src in sources:
                if isinstance(src, dict):
                    src_data = src.get("data", src)
                    if isinstance(src_data, dict):
                        rows = _extract_table_rows(cat_id, src_data)
                        for r in rows:
                            r["category"] = cat_id
                            all_rows.append(r)
        except Exception:
            pass

    if export_format == "csv":
        if all_rows:
            df = pd.DataFrame(all_rows)
        else:
            df = pd.DataFrame({"info": ["No data available"]})
        return dcc.send_data_frame(df.to_csv, f"{filename}.csv", index=False)

    elif export_format == "json":
        data = {
            "report_title": title,
            "generated": datetime.now().isoformat(),
            "location": {"lat": lat, "lon": lon},
            "time_range": time_range,
            "categories": {k: v for k, v in raw_export.items()},
        }
        return dict(content=json.dumps(data, indent=2, default=str), filename=f"{filename}.json")

    else:
        return dict(
            content="Report generation for this format requires additional processing.",
            filename=f"{filename}.txt",
        )


# ==================== TEMPLATE BUTTONS ====================

@callback(
    [Output("report-type-selector", "value"),
     Output("report-sections-checklist", "value"),
     Output("report-category-selector", "value")],
    [Input("template-summary-btn", "n_clicks"),
     Input("template-detailed-btn", "n_clicks"),
     Input("template-compliance-btn", "n_clicks"),
     Input("template-health-btn", "n_clicks")],
    prevent_initial_call=True,
)
def apply_report_template(summary_clicks, detailed_clicks, compliance_clicks, health_clicks):
    """Set the report type, sections, and categories when a template button is clicked."""
    triggered = ctx.triggered_id
    type_mapping = {
        "template-summary-btn": "summary",
        "template-detailed-btn": "detailed",
        "template-compliance-btn": "compliance",
        "template-health-btn": "health",
    }
    sections_mapping = {
        "template-summary-btn": ["summary", "charts", "statistics"],
        "template-detailed-btn": ["summary", "tables", "charts", "statistics", "trends", "anomalies"],
        "template-compliance-btn": ["summary", "tables", "statistics", "recommendations"],
        "template-health-btn": ["summary", "charts", "recommendations"],
    }
    categories_mapping = {
        "template-summary-btn": [cat["id"] for cat in DATA_CATEGORIES],
        "template-detailed-btn": [cat["id"] for cat in DATA_CATEGORIES],
        "template-compliance-btn": ["air_quality", "water", "radiation", "soil"],
        "template-health-btn": ["air_quality", "water", "weather", "radiation"],
    }
    report_type = type_mapping.get(triggered, "summary")
    sections = sections_mapping.get(triggered, ["summary", "charts", "statistics"])
    categories = categories_mapping.get(triggered, [cat["id"] for cat in DATA_CATEGORIES])
    return report_type, sections, categories


# ==================== PROGRESS BOX CALLBACKS ====================

@callback(
    Output("progress-entries-reports", "children"),
    Input("progress-reports-gen", "data"),
    prevent_initial_call=False,
)
def render_reports_progress(gen_prog):
    """Render the reports page activity log."""
    entries = []
    if gen_prog:
        if isinstance(gen_prog, list):
            entries.extend(gen_prog)
        else:
            entries.append(gen_prog)
    else:
        entries.append(make_entry("loading", "Waiting for report generation..."))
    return render_entries(entries)


@callback(
    [Output("progress-body-reports", "is_open"),
     Output("progress-icon-reports", "className")],
    Input("progress-toggle-reports", "n_clicks"),
    State("progress-body-reports", "is_open"),
    prevent_initial_call=True,
)
def toggle_reports_progress(n, is_open):
    """Toggle the reports progress box."""
    new_state = not is_open
    return new_state, "fas fa-chevron-up" if new_state else "fas fa-chevron-down"