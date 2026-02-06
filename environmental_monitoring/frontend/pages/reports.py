"""
Reports Page - Generate and export comprehensive reports.
"""
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta
import json
import io
import base64

from api_client import get_location_data, analyze_location
from components.charts import (
    create_time_series_chart,
    create_aqi_gauge,
    create_histogram
)
from components.layout import create_report_panel
from data_processing import DataProcessor
from config import REPORT_TYPES, EXPORT_FORMATS, DATA_CATEGORIES


def create_reports_layout() -> html.Div:
    """Create the reports generation page layout."""
    return html.Div([
        # Page Header
        html.Div([
            html.H3("📋 Reports", className="mb-2"),
            html.P("Generate comprehensive environmental reports and export data", 
                   className="text-muted")
        ], className="mb-4"),
        
        # Report Configuration
        create_report_panel(),
        
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
                html.Div(id="report-preview-container", children=[
                    html.Div([
                        html.I(className="fas fa-file-alt fa-5x text-muted mb-3"),
                        html.P("Configure your report options above and click 'Generate Report' to see a preview", 
                               className="text-muted")
                    ], className="text-center py-5")
                ])
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
        ], id="schedule-modal", is_open=False)
    ])


@callback(
    Output("report-preview-container", "children"),
    Input("generate-report-btn", "n_clicks"),
    [State("report-type-selector", "value"),
     State("export-format-selector", "value"),
     State("report-sections-checklist", "value"),
     State("report-title-input", "value"),
     State("report-author-input", "value")],
    prevent_initial_call=True
)
def generate_report_preview(n_clicks, report_type, export_format, sections, title, author):
    """Generate a preview of the report."""
    if not sections:
        return dbc.Alert("Please select at least one section to include", color="warning")
    
    title = title or "Environmental Report"
    author = author or "Environmental Monitoring System"
    
    # Build report preview
    preview_sections = []
    
    # Header
    preview_sections.append(html.Div([
        html.H2(title, className="text-center mb-2"),
        html.P(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", 
               className="text-center text-muted"),
        html.P(f"Author: {author}", className="text-center text-muted"),
        html.Hr()
    ]))
    
    if "summary" in sections:
        preview_sections.append(html.Div([
            html.H4("Executive Summary"),
            html.P("""
                This report provides a comprehensive overview of environmental conditions 
                for the selected time period and location. Key findings indicate that 
                air quality has remained within acceptable limits, with minor fluctuations 
                observed during peak traffic hours.
            """),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("42", className="text-success"),
                            html.P("Avg. AQI", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("18°C", className="text-primary"),
                            html.P("Avg. Temp", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("65%", className="text-info"),
                            html.P("Avg. Humidity", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("2", className="text-warning"),
                            html.P("Alerts", className="text-muted mb-0")
                        ])
                    ], className="text-center")
                ], md=3)
            ], className="mb-4")
        ]))
    
    if "charts" in sections:
        # Generate sample chart
        import numpy as np
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=168, freq="h")
        df = pd.DataFrame({
            "AQI": np.abs(np.cumsum(np.random.randn(168)) + 42),
            "Temperature": np.cumsum(np.random.randn(168)) / 5 + 18
        }, index=dates)
        
        fig = create_time_series_chart(
            df, 
            columns=["AQI"],
            title="Air Quality Index - 7 Day Trend",
            y_title="AQI",
            show_range_slider=False,
            show_range_buttons=False,
            height=300
        )
        
        preview_sections.append(html.Div([
            html.H4("Charts & Visualizations"),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
            html.Hr()
        ]))
    
    if "statistics" in sections:
        preview_sections.append(html.Div([
            html.H4("Statistical Summary"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Parameter"),
                    html.Th("Mean"),
                    html.Th("Median"),
                    html.Th("Min"),
                    html.Th("Max"),
                    html.Th("Std Dev")
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td("PM2.5 (μg/m³)"),
                        html.Td("12.4"),
                        html.Td("11.8"),
                        html.Td("4.2"),
                        html.Td("28.6"),
                        html.Td("5.3")
                    ]),
                    html.Tr([
                        html.Td("Temperature (°C)"),
                        html.Td("18.2"),
                        html.Td("17.9"),
                        html.Td("12.1"),
                        html.Td("24.8"),
                        html.Td("3.1")
                    ]),
                    html.Tr([
                        html.Td("Humidity (%)"),
                        html.Td("65.4"),
                        html.Td("66.0"),
                        html.Td("42.0"),
                        html.Td("89.0"),
                        html.Td("11.2")
                    ])
                ])
            ], striped=True, bordered=True, responsive=True, size="sm"),
            html.Hr()
        ]))
    
    if "trends" in sections:
        preview_sections.append(html.Div([
            html.H4("Trend Analysis"),
            html.Ul([
                html.Li("Air quality shows a slight improving trend (slope: -0.3 AQI/day)"),
                html.Li("Temperature trending upward as expected for the season"),
                html.Li("No significant change in humidity levels"),
                html.Li("Weekend periods show 15% better air quality than weekdays")
            ]),
            html.Hr()
        ]))
    
    if "recommendations" in sections:
        preview_sections.append(html.Div([
            html.H4("Recommendations"),
            dbc.Alert([
                html.Strong("✅ Good Air Quality Days: "),
                "Continue normal outdoor activities"
            ], color="success"),
            dbc.Alert([
                html.Strong("⚠️ Peak Hour Advisory: "),
                "Consider limiting strenuous outdoor activities during 7-9 AM and 5-7 PM"
            ], color="warning"),
            dbc.Alert([
                html.Strong("ℹ️ Monitoring: "),
                "Continue regular monitoring of PM2.5 levels during construction season"
            ], color="info")
        ]))
    
    return html.Div([
        dbc.Card([
            dbc.CardBody(preview_sections, style={"maxHeight": "600px", "overflow": "auto"})
        ], className="border shadow-sm"),
        html.Div([
            dbc.Badge(f"Format: {export_format.upper()}", color="primary", className="me-2"),
            dbc.Badge(f"Type: {report_type.title()}", color="secondary", className="me-2"),
            dbc.Badge(f"Sections: {len(sections)}", color="info")
        ], className="mt-3 text-center")
    ])


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
     State("report-title-input", "value")],
    prevent_initial_call=True
)
def download_report(n_clicks, export_format, title):
    """Generate and download the report."""
    title = title or "Environmental_Report"
    filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
    
    if export_format == "csv":
        # Generate sample CSV data
        df = pd.DataFrame({
            "timestamp": pd.date_range(start=datetime.now() - timedelta(days=7), periods=168, freq="h"),
            "aqi": [42 + i % 20 for i in range(168)],
            "temperature": [18 + (i % 10) / 2 for i in range(168)],
            "humidity": [65 + i % 15 for i in range(168)]
        })
        return dcc.send_data_frame(df.to_csv, f"{filename}.csv", index=False)
    
    elif export_format == "json":
        # Generate sample JSON data
        data = {
            "report_title": title,
            "generated": datetime.now().isoformat(),
            "summary": {
                "avg_aqi": 42,
                "avg_temperature": 18.2,
                "avg_humidity": 65.4
            },
            "data_points": 168
        }
        return dict(content=json.dumps(data, indent=2), filename=f"{filename}.json")
    
    else:
        # For PDF and other formats, return a placeholder
        return dict(
            content="Report generation for this format requires additional processing.",
            filename=f"{filename}.txt"
        )
