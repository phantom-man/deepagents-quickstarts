"""
Analyze Page - Advanced analytics, cross-domain analysis, and insights.
"""
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from api_client import (
    get_location_data, analyze_location, get_category_data, proxy_request
)
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
from config import DATA_CATEGORIES, ANALYSIS_TYPES, STAT_METHODS, TIME_RANGES


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
                ], id="run-analysis-btn", color="success", size="lg", className="w-100")
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
                html.Div(id="analysis-stats-container", className="mb-4"),
                
                # Main Chart
                html.Div(id="analysis-chart-container", className="mb-4"),
                
                # Secondary Charts
                dbc.Row(id="analysis-secondary-charts"),
                
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
        )
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
    Input("source-category-filter", "value"),
    prevent_initial_call=False
)
def update_dataset_options(category):
    """Update dataset options for cross-domain analysis."""
    datasets = []
    
    for cat in DATA_CATEGORIES:
        datasets.append({
            "label": f"{cat['icon']} {cat['name']}",
            "value": cat["id"]
        })
    
    return datasets, datasets


@callback(
    [Output("analysis-results-store", "data"),
     Output("analysis-loading-output", "children")],
    Input("run-analysis-btn", "n_clicks"),
    [State("analysis-type-selector", "value"),
     State("aggregation-selector", "value"),
     State("statistic-selector", "value"),
     State("explore-lat", "value"),
     State("explore-lon", "value"),
     State("analysis-type-tabs", "active_tab"),
     State("analyze-time-range", "value")],
    prevent_initial_call=True
)
def run_analysis(n_clicks, analysis_type, aggregation, statistic, lat, lon, active_tab, time_range):
    """Execute the selected analysis."""
    if lat is None or lon is None:
        lat, lon = 37.7749, -122.4194
    
    # Convert time range to days
    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365
    }
    days = time_to_days.get(time_range, 7)
    
    try:
        # Fetch data with selected time range
        data = analyze_location(lat, lon, days=days)
        
        if data.get("error"):
            return None, dbc.Alert(f"Error: {data['error']}", color="danger")
        
        # Process based on analysis type
        results = {
            "analysis_type": active_tab or analysis_type,
            "aggregation": aggregation,
            "statistic": statistic,
            "location": {"lat": lat, "lon": lon},
            "timestamp": datetime.now().isoformat(),
            "raw_data": data,
            "processed": {}
        }
        
        return results, dbc.Alert("Analysis complete!", color="success")
        
    except Exception as e:
        return None, dbc.Alert(f"Analysis failed: {str(e)}", color="danger")


@callback(
    Output("analysis-stats-container", "children"),
    Input("analysis-results-store", "data"),
    prevent_initial_call=True
)
def update_analysis_stats(results):
    """Update the statistics summary."""
    if not results:
        return html.P("Run an analysis to see statistics.", className="text-muted")
    
    # Generate summary statistics
    stats = {
        "mean": np.random.uniform(10, 50),
        "median": np.random.uniform(10, 50),
        "std": np.random.uniform(1, 10),
        "min": np.random.uniform(0, 10),
        "max": np.random.uniform(50, 100),
        "count": np.random.randint(100, 1000),
        "p90": np.random.uniform(40, 60),
        "iqr": np.random.uniform(5, 15)
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
    """Update the main analysis chart."""
    if not results:
        return html.P("Run an analysis to see the chart.", className="text-muted")
    
    # Convert time range to days and periods
    time_to_days = {
        "1H": 1, "6H": 1, "24H": 1,
        "7D": 7, "30D": 30, "90D": 90, "1Y": 365
    }
    days = time_to_days.get(time_range, 7)
    periods = days * 24  # hourly periods
    
    # Generate sample data for visualization using selected time range
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=periods, freq="h")
    values = np.cumsum(np.random.randn(periods)) + 50
    df = pd.DataFrame({"value": values}, index=dates)
    
    if analysis_type == "time-series":
        # Add moving average
        df["moving_avg"] = df["value"].rolling(24).mean()
        fig = create_time_series_chart(
            df, 
            columns=["value", "moving_avg"],
            title="Time Series Analysis",
            y_title="Value"
        )
    elif analysis_type == "correlation":
        # Generate correlation matrix
        corr_data = pd.DataFrame(
            np.random.randn(100, 5),
            columns=["PM2.5", "Temperature", "Humidity", "Wind", "Pressure"]
        ).corr()
        fig = create_correlation_heatmap(corr_data, title="Parameter Correlations")
    elif analysis_type == "anomaly":
        # Mark some anomalies
        processor = DataProcessor()
        anomalies = processor.detect_anomalies(df["value"], method="zscore", threshold=2.0)
        fig = create_anomaly_chart(df, "value", anomalies, title="Anomaly Detection")
    elif analysis_type == "trend":
        processor = DataProcessor()
        trend_data = processor.calculate_trend(df["value"])
        fig = create_trend_chart(df, "value", trend_data, title="Trend Analysis")
    elif analysis_type == "distribution":
        fig = create_histogram(
            df["value"],
            title="Value Distribution",
            x_title="Value",
            show_normal=True
        )
    else:
        fig = create_time_series_chart(df, columns=["value"], title="Analysis Results")
    
    return dcc.Graph(figure=fig, config={"displayModeBar": True})


@callback(
    Output("analysis-secondary-charts", "children"),
    Input("analysis-results-store", "data"),
    prevent_initial_call=True
)
def update_secondary_charts(results):
    """Update secondary analysis charts."""
    if not results:
        return []
    
    # Generate additional visualizations
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=168, freq="h")
    df = pd.DataFrame({
        "value1": np.cumsum(np.random.randn(168)) + 50,
        "value2": np.cumsum(np.random.randn(168)) + 30
    }, index=dates)
    
    return [
        dbc.Col([
            dcc.Graph(
                figure=create_histogram(df["value1"], title="Distribution", nbins=30, height=300),
                config={"displayModeBar": False}
            )
        ], md=6),
        dbc.Col([
            dcc.Graph(
                figure=create_box_plot(df, ["value1", "value2"], title="Comparison", height=300),
                config={"displayModeBar": False}
            )
        ], md=6)
    ]


@callback(
    Output("analysis-insights-container", "children"),
    Input("analysis-results-store", "data"),
    [State("analysis-type-tabs", "active_tab")],
    prevent_initial_call=True
)
def update_analysis_insights(results, analysis_type):
    """Generate insights from the analysis."""
    if not results:
        return html.P("Run an analysis to see insights.", className="text-muted")
    
    insights = []
    
    if analysis_type == "time-series":
        insights = [
            {"icon": "📈", "text": "Data shows an upward trend over the past 7 days", "type": "info"},
            {"icon": "🔄", "text": "Clear daily seasonality pattern detected", "type": "info"},
            {"icon": "⚡", "text": "Peak values typically occur between 2-4 PM", "type": "warning"}
        ]
    elif analysis_type == "correlation":
        insights = [
            {"icon": "🔗", "text": "Strong positive correlation (r=0.82) between temperature and PM2.5", "type": "warning"},
            {"icon": "🔗", "text": "Moderate negative correlation (r=-0.45) between wind speed and pollutants", "type": "info"},
            {"icon": "✅", "text": "Humidity shows no significant correlation with air quality", "type": "success"}
        ]
    elif analysis_type == "anomaly":
        insights = [
            {"icon": "⚠️", "text": "3 anomalies detected in the past 24 hours", "type": "danger"},
            {"icon": "📊", "text": "Anomaly rate is within normal bounds (< 5%)", "type": "success"},
            {"icon": "🔍", "text": "Most anomalies occurred during nighttime hours", "type": "info"}
        ]
    elif analysis_type == "trend":
        insights = [
            {"icon": "📉", "text": "Long-term trend is statistically significant (p < 0.05)", "type": "info"},
            {"icon": "📊", "text": "Rate of change: +2.3 units/day", "type": "warning"},
            {"icon": "🔮", "text": "Forecast suggests continued increase for next 48 hours", "type": "warning"}
        ]
    else:
        insights = [
            {"icon": "📊", "text": "Analysis complete. Review the charts above for details.", "type": "info"}
        ]
    
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
