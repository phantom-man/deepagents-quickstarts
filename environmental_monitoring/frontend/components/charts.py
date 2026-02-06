"""
Chart Components for Environmental Monitoring Dashboard

Reusable Plotly chart components for various data visualizations.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

from config import THEME, AQI_COLORS


def create_time_series_chart(
    df: pd.DataFrame,
    columns: List[str],
    title: str = "Time Series",
    y_title: str = "Value",
    show_range_slider: bool = True,
    show_range_buttons: bool = True,
    height: int = 400
) -> go.Figure:
    """Create an interactive time series chart."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for i, col in enumerate(columns):
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index if isinstance(df.index, pd.DatetimeIndex) else df.index,
                y=df[col],
                mode="lines",
                name=col,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f"<b>{col}</b><br>%{{x}}<br>Value: %{{y:.2f}}<extra></extra>"
            ))
    
    # Range buttons
    range_buttons = []
    if show_range_buttons:
        range_buttons = [
            dict(count=1, label="1H", step="hour", stepmode="backward"),
            dict(count=6, label="6H", step="hour", stepmode="backward"),
            dict(count=1, label="1D", step="day", stepmode="backward"),
            dict(count=7, label="1W", step="day", stepmode="backward"),
            dict(count=1, label="1M", step="month", stepmode="backward"),
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(step="all", label="All")
        ]
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis=dict(
            title="Time",
            rangeslider=dict(visible=show_range_slider),
            rangeselector=dict(buttons=range_buttons) if range_buttons else None,
            type="date"
        ),
        yaxis=dict(title=y_title),
        height=height,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=30, t=80, b=60)
    )
    
    return fig


def create_correlation_heatmap(
    correlation_matrix: pd.DataFrame,
    title: str = "Correlation Matrix",
    height: int = 500
) -> go.Figure:
    """Create a correlation heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.index,
        colorscale="RdBu_r",
        zmid=0,
        text=np.round(correlation_matrix.values, 2),
        texttemplate="%{text}",
        hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        height=height,
        template="plotly_white",
        xaxis=dict(tickangle=45),
        margin=dict(l=100, r=30, t=80, b=100)
    )
    
    return fig


def create_aqi_gauge(
    aqi_value: int,
    title: str = "Air Quality Index",
    height: int = 250
) -> go.Figure:
    """Create an AQI gauge chart."""
    # Determine color based on AQI
    if aqi_value <= 50:
        color = AQI_COLORS["good"]
        category = "Good"
    elif aqi_value <= 100:
        color = AQI_COLORS["moderate"]
        category = "Moderate"
    elif aqi_value <= 150:
        color = AQI_COLORS["unhealthy_sensitive"]
        category = "Unhealthy for Sensitive Groups"
    elif aqi_value <= 200:
        color = AQI_COLORS["unhealthy"]
        category = "Unhealthy"
    elif aqi_value <= 300:
        color = AQI_COLORS["very_unhealthy"]
        category = "Very Unhealthy"
    else:
        color = AQI_COLORS["hazardous"]
        category = "Hazardous"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi_value,
        title=dict(text=f"{title}<br><span style='font-size:0.8em;color:gray'>{category}</span>"),
        gauge=dict(
            axis=dict(range=[0, 500], tickwidth=1),
            bar=dict(color=color),
            bgcolor="white",
            steps=[
                dict(range=[0, 50], color=AQI_COLORS["good"]),
                dict(range=[50, 100], color=AQI_COLORS["moderate"]),
                dict(range=[100, 150], color=AQI_COLORS["unhealthy_sensitive"]),
                dict(range=[150, 200], color=AQI_COLORS["unhealthy"]),
                dict(range=[200, 300], color=AQI_COLORS["very_unhealthy"]),
                dict(range=[300, 500], color=AQI_COLORS["hazardous"])
            ],
            threshold=dict(line=dict(color="black", width=4), thickness=0.75, value=aqi_value)
        )
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def create_map_scatter(
    data: List[Dict],
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    hover_cols: Optional[List[str]] = None,
    title: str = "Environmental Map",
    height: int = 500
) -> go.Figure:
    """Create a scatter map."""
    df = pd.DataFrame(data) if isinstance(data, list) else data
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.scatter_geo(
        df,
        lat=lat_col,
        lon=lon_col,
        color=color_col,
        size=size_col,
        hover_data=hover_cols,
        title=title
    )
    
    fig.update_layout(
        height=height,
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showocean=True,
            oceancolor="rgb(204, 224, 255)",
            showlakes=True,
            lakecolor="rgb(204, 224, 255)",
            showcountries=True,
            countrycolor="rgb(204, 204, 204)"
        ),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig


def create_mapbox_scatter(
    data: List[Dict],
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    hover_cols: Optional[List[str]] = None,
    title: str = "Environmental Map",
    center_lat: float = 37.7749,
    center_lon: float = -122.4194,
    zoom: int = 10,
    height: int = 500
) -> go.Figure:
    """Create a mapbox scatter plot."""
    df = pd.DataFrame(data) if isinstance(data, list) else data
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.scatter_mapbox(
        df,
        lat=lat_col,
        lon=lon_col,
        color=color_col,
        size=size_col,
        hover_data=hover_cols,
        title=title,
        zoom=zoom,
        center={"lat": center_lat, "lon": center_lon}
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        height=height,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig


def create_histogram(
    data: pd.Series,
    title: str = "Distribution",
    x_title: str = "Value",
    nbins: int = 50,
    show_normal: bool = True,
    height: int = 350
) -> go.Figure:
    """Create a histogram with optional normal distribution overlay."""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=data.dropna(),
        nbinsx=nbins,
        name="Distribution",
        marker_color=THEME["primary"],
        opacity=0.7
    ))
    
    if show_normal and len(data.dropna()) > 10:
        # Add normal distribution curve
        mean = data.mean()
        std = data.std()
        x_range = np.linspace(data.min(), data.max(), 100)
        normal_curve = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mean) / std) ** 2)
        # Scale to histogram
        normal_curve = normal_curve * len(data) * (data.max() - data.min()) / nbins
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=normal_curve,
            mode="lines",
            name="Normal Distribution",
            line=dict(color=THEME["danger"], width=2, dash="dash")
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis=dict(title=x_title),
        yaxis=dict(title="Frequency"),
        height=height,
        template="plotly_white",
        bargap=0.1,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_box_plot(
    df: pd.DataFrame,
    columns: List[str],
    title: str = "Distribution Comparison",
    height: int = 400
) -> go.Figure:
    """Create a box plot for comparing distributions."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for i, col in enumerate(columns):
        if col in df.columns:
            fig.add_trace(go.Box(
                y=df[col].dropna(),
                name=col,
                marker_color=colors[i % len(colors)],
                boxmean="sd"
            ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        yaxis=dict(title="Value"),
        height=height,
        template="plotly_white",
        showlegend=True
    )
    
    return fig


def create_multi_axis_chart(
    df: pd.DataFrame,
    left_columns: List[str],
    right_columns: List[str],
    title: str = "Multi-Axis Comparison",
    left_title: str = "Left Axis",
    right_title: str = "Right Axis",
    height: int = 400
) -> go.Figure:
    """Create a dual-axis time series chart."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    left_colors = px.colors.qualitative.Set1
    right_colors = px.colors.qualitative.Set2
    
    # Left axis traces
    for i, col in enumerate(left_columns):
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    name=col,
                    line=dict(color=left_colors[i % len(left_colors)], width=2)
                ),
                secondary_y=False
            )
    
    # Right axis traces
    for i, col in enumerate(right_columns):
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    name=col,
                    line=dict(color=right_colors[i % len(right_colors)], width=2, dash="dash")
                ),
                secondary_y=True
            )
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        height=height,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text=left_title, secondary_y=False)
    fig.update_yaxes(title_text=right_title, secondary_y=True)
    
    return fig


def create_anomaly_chart(
    df: pd.DataFrame,
    column: str,
    anomaly_mask: pd.Series,
    title: str = "Anomaly Detection",
    height: int = 400
) -> go.Figure:
    """Create a time series chart with anomalies highlighted."""
    fig = go.Figure()
    
    # Normal points
    fig.add_trace(go.Scatter(
        x=df.index[~anomaly_mask],
        y=df[column][~anomaly_mask],
        mode="lines",
        name="Normal",
        line=dict(color=THEME["primary"], width=2)
    ))
    
    # Anomaly points
    if anomaly_mask.sum() > 0:
        fig.add_trace(go.Scatter(
            x=df.index[anomaly_mask],
            y=df[column][anomaly_mask],
            mode="markers",
            name="Anomaly",
            marker=dict(color=THEME["danger"], size=10, symbol="x")
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis=dict(title="Time", rangeslider=dict(visible=True)),
        yaxis=dict(title=column),
        height=height,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_trend_chart(
    df: pd.DataFrame,
    column: str,
    trend_data: Dict,
    title: str = "Trend Analysis",
    height: int = 400
) -> go.Figure:
    """Create a chart with trend line overlay."""
    fig = go.Figure()
    
    # Data
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[column],
        mode="lines",
        name="Actual",
        line=dict(color=THEME["primary"], width=2)
    ))
    
    # Trend line
    if trend_data.get("slope") is not None:
        x_numeric = np.arange(len(df))
        trend_line = trend_data["intercept"] + trend_data["slope"] * x_numeric
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=trend_line,
            mode="lines",
            name=f'Trend (R²={trend_data.get("r_squared", 0):.3f})',
            line=dict(color=THEME["danger"], width=2, dash="dash")
        ))
    
    # Trend direction annotation
    direction = trend_data.get("trend_direction", "stable")
    arrow = "↗" if direction == "increasing" else "↘" if direction == "decreasing" else "→"
    
    fig.add_annotation(
        x=1, y=1,
        xref="paper", yref="paper",
        text=f"Trend: {arrow} {direction.title()}",
        showarrow=False,
        font=dict(size=14),
        bgcolor="white",
        bordercolor="gray",
        borderwidth=1,
        borderpad=4
    )
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis=dict(title="Time", rangeslider=dict(visible=True)),
        yaxis=dict(title=column),
        height=height,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_summary_cards(stats: Dict[str, Any]) -> go.Figure:
    """Create a summary card visualization."""
    fig = make_subplots(
        rows=2, cols=4,
        specs=[[{"type": "indicator"}] * 4] * 2,
        vertical_spacing=0.3,
        horizontal_spacing=0.1
    )
    
    indicators = [
        ("Mean", stats.get("mean", 0), None),
        ("Median", stats.get("median", 0), None),
        ("Std Dev", stats.get("std", 0), None),
        ("Count", stats.get("count", 0), None),
        ("Min", stats.get("min", 0), None),
        ("Max", stats.get("max", 0), None),
        ("P90", stats.get("p90", 0), None),
        ("IQR", stats.get("iqr", 0), None),
    ]
    
    for i, (title, value, reference) in enumerate(indicators):
        row = i // 4 + 1
        col = i % 4 + 1
        
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=value,
                title={"text": title},
                number={"font": {"size": 24}, "valueformat": ".2f"}
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig
