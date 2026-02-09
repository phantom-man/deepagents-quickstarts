"""
Layout Components for Environmental Monitoring Dashboard
"""
from datetime import datetime, timedelta
from typing import Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from config import (
    DASHBOARD_TITLE, DASHBOARD_SUBTITLE, DATA_CATEGORIES,
    TIME_RANGES, ANALYSIS_TYPES, REPORT_TYPES, EXPORT_FORMATS
)


def create_header() -> dbc.Navbar:
    """Create the dashboard header/navbar."""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.A(
                        dbc.Row([
                            dbc.Col(html.I(className="fas fa-leaf fa-2x", style={"color": "#28A745"})),
                            dbc.Col(dbc.NavbarBrand(DASHBOARD_TITLE, className="ms-2")),
                        ], align="center", className="g-0"),
                        href="/",
                        style={"textDecoration": "none"}
                    )
                ], width="auto"),
                dbc.Col([
                    html.Span(DASHBOARD_SUBTITLE, className="text-muted d-none d-md-block")
                ], width="auto", className="ms-3"),
            ], align="center"),
            dbc.Row([
                dbc.Col([
                    dbc.NavItem(dbc.NavLink("Dashboard", href="/", active="exact")),
                    dbc.NavItem(dbc.NavLink("Explore", href="/explore", active="exact")),
                    dbc.NavItem(dbc.NavLink("Analyze", href="/analyze", active="exact")),
                    dbc.NavItem(dbc.NavLink("Reports", href="/reports", active="exact")),
                ], width="auto"),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-sync-alt me-2"), "Refresh"],
                        id="refresh-button",
                        color="outline-primary",
                        size="sm",
                        className="me-2"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-cog")],
                        id="settings-button",
                        color="outline-secondary",
                        size="sm"
                    )
                ], width="auto")
            ], align="center", className="g-0 ms-auto")
        ], fluid=True),
        color="light",
        dark=False,
        className="mb-4 shadow-sm"
    )


def create_sidebar() -> dbc.Col:
    """Create the left sidebar with filters and navigation."""
    return dbc.Col([
        html.Div([
            # Location Search
            html.H6("📍 Location", className="mb-3"),
            dbc.InputGroup([
                dbc.Input(id="location-search", placeholder="Search location..."),
                dbc.Button(html.I(className="fas fa-search"), id="search-btn", color="primary")
            ], className="mb-3"),
            
            # Coordinates
            dbc.Row([
                dbc.Col([
                    dbc.Label("Latitude", className="small"),
                    dbc.Input(id="latitude-input", type="number", value=37.7749, step=0.0001)
                ]),
                dbc.Col([
                    dbc.Label("Longitude", className="small"),
                    dbc.Input(id="longitude-input", type="number", value=-122.4194, step=0.0001)
                ])
            ], className="mb-3"),
            
            html.Hr(),
            
            # Time Range Selection - Simple Dropdown
            html.H6("📅 Time Range", className="mb-3"),
            dcc.Dropdown(
                id="global-time-range",
                options=[
                    {"label": tr["label"], "value": tr["value"]}
                    for tr in TIME_RANGES if tr["value"] != "custom"
                ],
                value="7D",
                clearable=False,
                className="mb-3"
            ),
            # Store for sharing time range across pages
            dcc.Store(id="selected-time-range", data="7D"),
            
            html.Hr(),
            
            # Data Categories
            html.H6("📊 Data Categories", className="mb-3"),
            dbc.Checklist(
                id="category-checklist",
                options=[
                    {"label": f"{cat['icon']} {cat['name']}", "value": cat["id"]}
                    for cat in DATA_CATEGORIES
                ],
                value=["air_quality", "weather", "earthquakes", "radiation", "climate", "soil"],
                className="category-checklist"
            ),
            
            html.Hr(),
            
            # Quick Actions
            html.H6("⚡ Quick Actions", className="mb-3"),
            dbc.ButtonGroup([
                dbc.Button([html.I(className="fas fa-download me-1"), "Export"], 
                          id="quick-export-btn", color="outline-success", size="sm"),
                dbc.Button([html.I(className="fas fa-share-alt me-1"), "Share"], 
                          id="quick-share-btn", color="outline-info", size="sm"),
            ], className="w-100"),
            
        ], className="sidebar-content p-3 bg-light rounded")
    ], width=2, className="sidebar")


def create_data_source_selector() -> html.Div:
    """Create the data source selection panel."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H5("🌐 Data Sources", className="mb-0"),
                dbc.Button(
                    html.I(className="fas fa-info-circle"),
                    id="data-source-info-btn",
                    color="link",
                    size="sm"
                )
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Category Filter"),
                        dcc.Dropdown(
                            id="source-category-filter",
                            options=[{"label": cat["name"], "value": cat["id"]} for cat in DATA_CATEGORIES],
                            placeholder="All Categories",
                            clearable=True
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Select Sources"),
                        dcc.Dropdown(
                            id="source-selector",
                            multi=True,
                            placeholder="Select data sources..."
                        )
                    ], md=8)
                ]),
                html.Div(id="source-status-badges", className="mt-3")
            ])
        ], className="mb-4")
    ])


def create_time_range_selector() -> html.Div:
    """Create the time range selection panel with range slider."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H5("📅 Time Range", className="mb-0")),
            dbc.CardBody([
                # Quick select buttons
                dbc.ButtonGroup([
                    dbc.Button(tr["label"], id={"type": "time-btn", "index": tr["value"]}, 
                              color="outline-primary", size="sm", className="me-1")
                    for tr in TIME_RANGES
                ], className="mb-3 flex-wrap"),
                
                # Date range picker
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Start"),
                        dcc.DatePickerSingle(
                            id="range-start-date",
                            date=datetime.now() - timedelta(days=7),
                            display_format="YYYY-MM-DD"
                        )
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Start Time"),
                        dbc.Input(id="range-start-time", type="time", value="00:00")
                    ], md=2),
                    dbc.Col([
                        dbc.Label("End"),
                        dcc.DatePickerSingle(
                            id="range-end-date",
                            date=datetime.now(),
                            display_format="YYYY-MM-DD"
                        )
                    ], md=3),
                    dbc.Col([
                        dbc.Label("End Time"),
                        dbc.Input(id="range-end-time", type="time", value="23:59")
                    ], md=2),
                    dbc.Col([
                        dbc.Label(" ", className="d-block"),
                        dbc.Button("Apply", id="apply-time-range-btn", color="primary")
                    ], md=2)
                ]),
                
                # Range slider
                html.Div([
                    dcc.RangeSlider(
                        id="time-range-slider",
                        min=0,
                        max=100,
                        value=[0, 100],
                        marks={i: f"{i}%" for i in range(0, 101, 25)},
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], className="mt-3")
            ])
        ], className="mb-4")
    ])


def create_analysis_panel() -> html.Div:
    """Create the analysis configuration panel."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H5("🔬 Analysis Configuration", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Analysis Type"),
                        dcc.Dropdown(
                            id="analysis-type-selector",
                            options=[{"label": at["name"], "value": at["id"]} for at in ANALYSIS_TYPES],
                            value="time_series",
                            clearable=False
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Aggregation"),
                        dcc.Dropdown(
                            id="aggregation-selector",
                            options=[
                                {"label": "None (Raw)", "value": "none"},
                                {"label": "Hourly", "value": "1H"},
                                {"label": "Daily", "value": "1D"},
                                {"label": "Weekly", "value": "1W"},
                                {"label": "Monthly", "value": "1M"}
                            ],
                            value="1H",
                            clearable=False
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Statistic"),
                        dcc.Dropdown(
                            id="statistic-selector",
                            options=[
                                {"label": "Mean", "value": "mean"},
                                {"label": "Median", "value": "median"},
                                {"label": "Sum", "value": "sum"},
                                {"label": "Min", "value": "min"},
                                {"label": "Max", "value": "max"}
                            ],
                            value="mean",
                            clearable=False
                        )
                    ], md=4)
                ], className="mb-3"),
                
                # Analysis-specific options
                html.Div(id="analysis-options-container")
            ])
        ], className="mb-4")
    ])


def create_cross_domain_panel() -> html.Div:
    """Create the cross-domain data linking panel."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H5("🔗 Cross-Domain Analysis", className="mb-0"),
                dbc.Badge("Advanced", color="warning", className="ms-2")
            ], className="d-flex align-items-center"),
            dbc.CardBody([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Link data across different environmental domains to discover correlations and insights."
                ], color="info", className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Primary Dataset"),
                        dcc.Dropdown(id="primary-dataset-selector", placeholder="Select primary dataset...")
                    ], md=5),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-link fa-2x text-muted")
                        ], className="text-center mt-4")
                    ], md=2),
                    dbc.Col([
                        dbc.Label("Secondary Dataset"),
                        dcc.Dropdown(id="secondary-dataset-selector", placeholder="Select secondary dataset...")
                    ], md=5)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Join Key"),
                        dcc.Dropdown(
                            id="join-key-selector",
                            options=[
                                {"label": "Timestamp", "value": "timestamp"},
                                {"label": "Location", "value": "location"},
                                {"label": "Both", "value": "both"}
                            ],
                            value="timestamp"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Time Tolerance"),
                        dbc.InputGroup([
                            dbc.Input(id="time-tolerance-input", type="number", value=1),
                            dbc.Select(
                                id="time-tolerance-unit",
                                options=[
                                    {"label": "Minutes", "value": "min"},
                                    {"label": "Hours", "value": "hour"},
                                    {"label": "Days", "value": "day"}
                                ],
                                value="hour"
                            )
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Label(" ", className="d-block"),
                        dbc.Button([
                            html.I(className="fas fa-code-branch me-2"),
                            "Link Datasets"
                        ], id="link-datasets-btn", color="success", className="w-100")
                    ], md=4)
                ])
            ])
        ], className="mb-4")
    ])


def create_report_panel() -> html.Div:
    """Create the report generation panel."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader(html.H5("📋 Report Generation", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Report Type"),
                        dcc.Dropdown(
                            id="report-type-selector",
                            options=[{"label": rt["name"], "value": rt["id"]} for rt in REPORT_TYPES],
                            value="summary"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Export Format"),
                        dcc.Dropdown(
                            id="export-format-selector",
                            options=[{"label": ef["name"], "value": ef["id"]} for ef in EXPORT_FORMATS],
                            value="pdf"
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label(" ", className="d-block"),
                        dbc.Button([
                            html.I(className="fas fa-file-export me-2"),
                            "Generate Report"
                        ], id="generate-report-btn", color="primary", className="w-100")
                    ], md=4)
                ], className="mb-3"),
                
                # Report options
                dbc.Accordion([
                    dbc.AccordionItem([
                        dbc.Checklist(
                            id="report-sections-checklist",
                            options=[
                                {"label": "Executive Summary", "value": "summary"},
                                {"label": "Data Tables", "value": "tables"},
                                {"label": "Charts & Visualizations", "value": "charts"},
                                {"label": "Statistical Analysis", "value": "statistics"},
                                {"label": "Trend Analysis", "value": "trends"},
                                {"label": "Anomaly Report", "value": "anomalies"},
                                {"label": "Recommendations", "value": "recommendations"}
                            ],
                            value=["summary", "charts", "statistics"]
                        )
                    ], title="Report Sections"),
                    dbc.AccordionItem([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Report Title"),
                                dbc.Input(id="report-title-input", placeholder="Environmental Report")
                            ], md=6),
                            dbc.Col([
                                dbc.Label("Author"),
                                dbc.Input(id="report-author-input", placeholder="Your Name")
                            ], md=6)
                        ]),
                        dbc.Label("Notes", className="mt-2"),
                        dbc.Textarea(id="report-notes-input", rows=3, placeholder="Additional notes...")
                    ], title="Report Metadata")
                ], start_collapsed=True)
            ])
        ], className="mb-4")
    ])


def create_stats_cards(stats: Optional[dict] = None) -> html.Div:
    """Create statistics summary cards."""
    if stats is None:
        stats = {
            "total_sources": 24,
            "active_alerts": 2,
            "data_points": "1.2M",
            "last_update": "2 min ago"
        }
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(stats.get("total_sources", 0), className="card-title text-primary"),
                    html.P("Data Sources", className="card-text text-muted")
                ])
            ], className="text-center h-100")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(stats.get("active_alerts", 0), className="card-title text-danger"),
                    html.P("Active Alerts", className="card-text text-muted")
                ])
            ], className="text-center h-100")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(stats.get("data_points", 0), className="card-title text-success"),
                    html.P("Data Points", className="card-text text-muted")
                ])
            ], className="text-center h-100")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(stats.get("last_update", "N/A"), className="card-title text-info"),
                    html.P("Last Update", className="card-text text-muted")
                ])
            ], className="text-center h-100")
        ], md=3)
    ], className="mb-4")


def create_loading_spinner(id_suffix: str = "") -> html.Div:
    """Create a loading spinner component."""
    return html.Div([
        dbc.Spinner(
            html.Div(id=f"loading-output-{id_suffix}"),
            color="primary",
            type="border",
            size="lg"
        )
    ], className="text-center my-4")


def create_footer() -> html.Footer:
    """Create the dashboard footer."""
    return html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.P([
                        "Environmental Monitoring Dashboard • ",
                        "Powered by ",
                        html.A("24+ Public APIs", href="#", className="text-decoration-none"),
                        " • ",
                        f"© {datetime.now().year}"
                    ], className="text-muted mb-0")
                ], className="text-center")
            ])
        ], fluid=True)
    ], className="bg-light py-3 mt-4 border-top")
