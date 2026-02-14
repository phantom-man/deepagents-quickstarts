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
from typing import Dict, Any, List, Optional
import logging
import time

import plotly.graph_objects as go

from components.progress_box import create_progress_box, make_entry, render_entries

from api_client import (
    get_hub_info, get_sources, quick_check, get_health, get_category_data,
    get_categories_parallel,
)
from config import DATA_CATEGORIES, MAP_CONFIG, TIME_RANGES, API_BASE_URL
from data_commons_client import (
    get_dc_category_data,
    get_dc_summary_for_category,
    CATEGORY_VARIABLES,
)

logger = logging.getLogger(__name__)


# ==================== HELPER FUNCTIONS ====================

def create_stats_cards(stats: Dict[str, Any]) -> List:
    """Create statistics cards for the dashboard."""
    return [
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(stats.get("total_sources", 0)), className="text-primary mb-0"),
                    html.Small("Data Sources", className="text-muted")
                ])
            ], className="h-100 text-center")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(stats.get("active_alerts", 0)), className="text-warning mb-0"),
                    html.Small("Active Alerts", className="text-muted")
                ])
            ], className="h-100 text-center")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(stats.get("data_points", 0)), className="text-success mb-0"),
                    html.Small("Data Points", className="text-muted")
                ])
            ], className="h-100 text-center")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(str(stats.get("last_update", "N/A")), className="text-info mb-0"),
                    html.Small("Last Update", className="text-muted")
                ])
            ], className="h-100 text-center")
        ], md=3)
    ]


def create_aqi_gauge(value: float, label: str) -> dict:
    """Create an AQI gauge figure."""
    import plotly.graph_objects as go
    
    # AQI color scale
    if value <= 50:
        color = "#00E400"  # Good
    elif value <= 100:
        color = "#FFFF00"  # Moderate
    elif value <= 150:
        color = "#FF7E00"  # Unhealthy for Sensitive Groups
    elif value <= 200:
        color = "#FF0000"  # Unhealthy
    elif value <= 300:
        color = "#8F3F97"  # Very Unhealthy
    else:
        color = "#7E0023"  # Hazardous
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': label, 'font': {'size': 12}},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "#E8F5E9"},
                {'range': [50, 100], 'color': "#FFF9C4"},
                {'range': [100, 150], 'color': "#FFE0B2"},
                {'range': [150, 200], 'color': "#FFCDD2"},
                {'range': [200, 300], 'color': "#E1BEE7"}
            ],
        }
    ))
    
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def get_graph_for_category(cat_id: str, data: Dict[str, Any], dc_data: Optional[Dict[str, Any]] = None, time_range: str = "7D") -> Any:
    """Generate a category-specific visualization based on best practices.

    Design principles (Tufte / Few):
    - Use the right chart type for each data type (gauges for thresholds,
      line+fill for time series, horizontal bar for ranked lists).
    - Height >= 350px so labels and data are readable.
    - Remove chart-junk; maximise data-ink ratio.
    - Show context: reference lines for safety thresholds, annotations.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    GRAPH_HEIGHT = 370
    MARGIN = dict(l=50, r=30, t=50, b=50)

    # ------------------------------------------------------------------
    # Data Commons time-series  (precedence when time range is long)
    # ------------------------------------------------------------------
    dc_ts = (dc_data or {}).get("time_series", {})
    use_dc = bool(dc_ts) and time_range in ("90D", "1Y", "custom")

    if use_dc and dc_ts:
        fig = go.Figure()
        colors = ["#2E86AB", "#A23B72", "#F18F01", "#28A745", "#C73E1D", "#8F3F97"]
        for idx, (label, series) in enumerate(dc_ts.items()):
            if not series:
                continue
            dates = [pt["date"] for pt in series]
            values = [pt["value"] for pt in series]
            fig.add_trace(go.Scatter(
                x=dates, y=values, mode="lines+markers",
                name=label, line=dict(width=2, color=colors[idx % len(colors)]),
                marker=dict(size=6),
            ))
        dc_vars = (dc_data or {}).get("variables", {})
        annotations = []
        for label, vinfo in list(dc_vars.items())[:4]:
            val = vinfo.get("value")
            unit = vinfo.get("unit", "")
            date = vinfo.get("date", "")
            if val is not None:
                annotations.append(f"{label}: {val} {unit} ({date})")
        if annotations:
            fig.add_annotation(
                text="<br>".join(annotations),
                xref="paper", yref="paper", x=0.98, y=0.98,
                showarrow=False, font=dict(size=11, color="#FFD700"),
                bgcolor="rgba(0,0,0,0.6)", bordercolor="#FFD700",
                xanchor="right", yanchor="top",
            )
        place_type = (dc_data or {}).get("place_type", "")
        place_dcid = (dc_data or {}).get("place_dcid", "")
        fig.update_layout(
            title=f"{cat_id.replace('_', ' ').title()} — Data Commons ({place_type}: {place_dcid})",
            height=GRAPH_HEIGHT, margin=MARGIN, showlegend=True,
            legend=dict(orientation="h", y=-0.15),
        )
        return fig

    # ------------------------------------------------------------------
    # Backend data visualisations — category-specific best-practice charts
    # ------------------------------------------------------------------

    if cat_id == "earthquakes":
        features = data.get("features", [])[:25]
        if not features:
            return _empty_figure("No earthquake data", GRAPH_HEIGHT, MARGIN)
        mags = [f.get("properties", {}).get("mag", 0) or 0 for f in features]
        depths = [(f.get("geometry", {}).get("coordinates", [0, 0, 0]) + [0, 0, 0])[2] for f in features]
        places = [f.get("properties", {}).get("place", "Unknown") for f in features]
        times_raw = [f.get("properties", {}).get("time", 0) for f in features]
        # Convert epoch ms to readable strings
        from datetime import datetime as _dt
        times = []
        for t in times_raw:
            try:
                times.append(_dt.fromtimestamp(t / 1000).strftime("%m/%d %H:%M"))
            except Exception:
                times.append("")
        hover = [f"M{m:.1f} depth {d:.0f}km<br>{p}" for m, d, p in zip(mags, depths, places)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times, y=mags, mode="markers",
            marker=dict(
                size=[max(8, m * 5) for m in mags],
                color=depths,
                colorscale="YlOrRd",
                colorbar=dict(title="Depth (km)", thickness=12, len=0.6),
                opacity=0.8,
                line=dict(width=1, color="#333"),
            ),
            text=hover, hoverinfo="text",
            name="Earthquakes",
        ))
        fig.add_hline(y=4.0, line_dash="dash", line_color="#C73E1D",
                      annotation_text="M4.0 — Moderate", annotation_position="top left")
        fig.update_layout(
            title="Recent Earthquakes (size = magnitude, color = depth)",
            xaxis_title="Time", yaxis_title="Magnitude",
            height=GRAPH_HEIGHT, margin=MARGIN, showlegend=False,
        )
        return fig

    if cat_id == "air_quality":
        # --- Daily AQI Aggregate Format (primary) ---
        # Backend now returns: {daily_aqi: [{date, overall_aqi, category, parameters: {...}}]}
        daily_aqi = data.get("daily_aqi", [])
        if isinstance(daily_aqi, list) and daily_aqi:
            dates = [d.get("date", "") for d in daily_aqi]
            aqi_values = [d.get("overall_aqi", 0) for d in daily_aqi]
            categories = [
                (d.get("category") or {}).get("Name", "Unknown") for d in daily_aqi
            ]

            # Color each bar by AQI level
            def _aqi_color(v):
                if v <= 50:
                    return "#00E400"
                if v <= 100:
                    return "#FFFF00"
                if v <= 150:
                    return "#FF7E00"
                if v <= 200:
                    return "#FF0000"
                if v <= 300:
                    return "#8F3F97"
                return "#7E0023"

            bar_colors = [_aqi_color(v) for v in aqi_values]
            latest_aqi = aqi_values[-1] if aqi_values else 0
            latest_cat = categories[-1] if categories else "N/A"
            period = data.get("period_days", len(daily_aqi))
            area = daily_aqi[-1].get("reporting_area", "") if daily_aqi else ""

            # Build pollutant breakdown for the latest day
            latest_params = (daily_aqi[-1].get("parameters") or {}) if daily_aqi else {}

            fig = make_subplots(
                rows=1, cols=2, column_widths=[0.60, 0.40],
                specs=[[{"type": "xy"}, {"type": "indicator"}]],
            )
            # Daily AQI bar chart
            fig.add_trace(go.Bar(
                x=dates, y=aqi_values,
                marker_color=bar_colors,
                text=[f"{v}" for v in aqi_values], textposition="outside",
                hovertext=[f"{d}<br>AQI: {v}<br>{c}" for d, v, c in zip(dates, aqi_values, categories)],
                hoverinfo="text",
                name="Daily AQI",
            ), row=1, col=1)
            # EPA standard line at 100 (Moderate/USG boundary)
            fig.add_hline(
                y=100, line_dash="dash", line_color="#FF7E00", row=1, col=1,
                annotation_text="Moderate Threshold (100)",
                annotation_position="top left",
            )
            # AQI gauge for latest day
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=float(latest_aqi),
                title={"text": f"Latest AQI<br><span style='font-size:11px'>{latest_cat}</span>"},
                gauge={
                    "axis": {"range": [0, 300]},
                    "bar": {"color": _aqi_color(latest_aqi)},
                    "steps": [
                        {"range": [0, 50], "color": "#E8F5E9"},
                        {"range": [50, 100], "color": "#FFF9C4"},
                        {"range": [100, 150], "color": "#FFE0B2"},
                        {"range": [150, 200], "color": "#FFCDD2"},
                        {"range": [200, 300], "color": "#E1BEE7"},
                    ],
                },
            ), row=1, col=2)
            title_suffix = f" ({area})" if area else ""
            fig.update_layout(
                title=f"Air Quality \u2014 {period}-Day Daily AQI{title_suffix}",
                height=GRAPH_HEIGHT, margin=MARGIN, showlegend=False,
            )
            fig.update_yaxes(title_text="AQI", row=1, col=1)
            return fig

        # --- Fallback: legacy single-observation formats (AirNow current, Open-Meteo current) ---
        param_vals: Dict[str, List[float]] = {}
        aqi_val = None

        # AirNow observations format
        observations = data.get("observations", [])
        if isinstance(observations, list):
            for obs in observations:
                if not isinstance(obs, dict):
                    continue
                param_name = obs.get("ParameterName", "unknown")
                aqi = obs.get("AQI")
                if aqi is not None:
                    try:
                        param_vals.setdefault(param_name, []).append(float(aqi))
                        if aqi_val is None:
                            aqi_val = float(aqi)
                    except (ValueError, TypeError):
                        pass

        # Open-Meteo current format
        current_aq = data.get("current") or {}
        if isinstance(current_aq, dict):
            for aq_key in ("us_aqi", "pm2_5", "pm10", "ozone", "nitrogen_dioxide"):
                raw = current_aq.get(aq_key)
                if raw is not None and aq_key not in param_vals:
                    try:
                        param_vals[aq_key] = [float(raw)]
                        if aq_key == "us_aqi" and aqi_val is None:
                            aqi_val = float(raw)
                    except (ValueError, TypeError):
                        pass

        if not param_vals:
            return _empty_figure("No air quality data available", GRAPH_HEIGHT, MARGIN)

        params = sorted(param_vals.keys())
        avgs = [sum(param_vals[p]) / len(param_vals[p]) for p in params]

        if aqi_val is None:
            for pm_key in ("PM2.5", "pm2_5"):
                if pm_key in param_vals:
                    aqi_val = param_vals[pm_key][0]
                    break

        fig = make_subplots(
            rows=1, cols=2, column_widths=[0.55, 0.45],
            specs=[[{"type": "xy"}, {"type": "indicator"}]],
        )
        colors = ["#00E400" if v <= 50 else "#FFFF00" if v <= 100 else "#FF7E00" if v <= 150 else "#FF0000" for v in avgs]
        fig.add_trace(go.Bar(
            y=params, x=avgs, orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}" for v in avgs], textposition="outside",
            name="Avg Value",
        ), row=1, col=1)
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=float(aqi_val) if aqi_val else 0,
            title={"text": "AQI"},
            gauge={
                "axis": {"range": [0, 300]},
                "bar": {"color": "#2E86AB"},
                "steps": [
                    {"range": [0, 50], "color": "#E8F5E9"},
                    {"range": [50, 100], "color": "#FFF9C4"},
                    {"range": [100, 150], "color": "#FFE0B2"},
                    {"range": [150, 200], "color": "#FFCDD2"},
                    {"range": [200, 300], "color": "#E1BEE7"},
                ],
            },
        ), row=1, col=2)
        fig.update_layout(
            title="Air Quality \u2014 Current Observations",
            height=GRAPH_HEIGHT, margin=MARGIN, showlegend=False,
        )
        return fig

    if cat_id == "weather":
        hourly = data.get("hourly", {})
        current = data.get("current_weather", {})
        if hourly:
            temps = hourly.get("temperature_2m", [])[:48]
            times = hourly.get("time", [])[:48]
            humidity = hourly.get("relative_humidity_2m", hourly.get("relativehumidity_2m", []))[:48]
            precip = hourly.get("precipitation", [])[:48]
            if temps and times:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
                                    vertical_spacing=0.08)
                fig.add_trace(go.Scatter(
                    x=times, y=temps, mode="lines", name="Temperature",
                    line=dict(color="#C73E1D", width=2),
                    fill="tozeroy", fillcolor="rgba(199,62,29,0.1)",
                ), row=1, col=1)
                if humidity:
                    fig.add_trace(go.Scatter(
                        x=times[:len(humidity)], y=humidity, mode="lines", name="Humidity %",
                        line=dict(color="#2E86AB", width=1, dash="dot"),
                        yaxis="y2",
                    ), row=1, col=1)
                if precip:
                    fig.add_trace(go.Bar(
                        x=times[:len(precip)], y=precip, name="Precipitation (mm)",
                        marker_color="#4ECDC4", opacity=0.7,
                    ), row=2, col=1)
                if current:
                    temp_now = current.get("temperature", "?")
                    wind_now = current.get("windspeed", "?")
                    fig.add_annotation(
                        text=f"Now: {temp_now}°C, Wind {wind_now} km/h",
                        xref="paper", yref="paper", x=0.02, y=0.98,
                        showarrow=False, font=dict(size=12, color="#fff"),
                        bgcolor="#2E86AB", bordercolor="#2E86AB",
                        xanchor="left", yanchor="top",
                    )
                fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
                fig.update_yaxes(title_text="Precip (mm)", row=2, col=1)
                fig.update_layout(
                    title="48-Hour Weather Forecast",
                    height=GRAPH_HEIGHT + 50, margin=MARGIN,
                    legend=dict(orientation="h", y=-0.12), showlegend=True,
                )
                return fig
        return _empty_figure("No weather data", GRAPH_HEIGHT, MARGIN)

    if cat_id == "water":
        stations = data.get("value", {}).get("timeSeries", [])[:12]
        if not stations:
            return _empty_figure("No water quality data", GRAPH_HEIGHT, MARGIN)
        names = []
        values = []
        param_names = []
        for s in stations:
            if not isinstance(s, dict):
                continue
            src_info = s.get("sourceInfo") or {}
            site_name = src_info.get("siteName", "Unknown Station") if isinstance(src_info, dict) else "Unknown Station"
            var_info = s.get("variable") or {}
            var_name = var_info.get("variableName", "Flow") if isinstance(var_info, dict) else "Flow"
            try:
                val = float(s.get("values", [{}])[0].get("value", [{}])[0].get("value", 0))
            except (IndexError, TypeError, ValueError):
                val = 0
            names.append(site_name[:25])
            values.append(val)
            param_names.append(var_name[:20])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=names, x=values, orientation="h",
            marker_color="#17A2B8",
            text=[f"{v:,.0f}" for v in values], textposition="outside",
            hovertext=[f"{n}<br>{p}: {v:,.1f}" for n, p, v in zip(names, param_names, values)],
            hoverinfo="text",
        ))
        fig.update_layout(
            title="Water Monitoring Stations — Flow Rates (cfs)",
            xaxis_title="Flow (cubic feet/sec)",
            height=GRAPH_HEIGHT, margin=dict(l=160, r=30, t=50, b=50),
            showlegend=False,
        )
        return fig

    if cat_id == "marine":
        # --- Parse marine data from multiple formats ---
        # Format 1: Open-Meteo Marine -> current{} + hourly{} with wave_height, etc.
        # Format 2: stations[] with water_level/wave_height (legacy)
        # Format 3: observations[] from NOAA NDBC
        # Format 4: US IOOS stations response
        names = []
        levels = []

        # Try Open-Meteo Marine format first (current + hourly time series)
        current_marine = data.get("current") or {}
        hourly_marine = data.get("hourly") or {}
        if isinstance(hourly_marine, dict) and hourly_marine.get("time"):
            times = hourly_marine.get("time", [])[:72]
            wave_h = hourly_marine.get("wave_height", [])[:72]
            wave_p = hourly_marine.get("wave_period", [])[:72]
            sst = hourly_marine.get("sea_surface_temperature", [])[:72]
            if times and (wave_h or sst):
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    row_heights=[0.6, 0.4], vertical_spacing=0.08)
                if wave_h:
                    fig.add_trace(go.Scatter(
                        x=times[:len(wave_h)], y=wave_h, mode="lines", name="Wave Height (m)",
                        line=dict(color="#17A2B8", width=2),
                        fill="tozeroy", fillcolor="rgba(23,162,184,0.1)",
                    ), row=1, col=1)
                if wave_p:
                    fig.add_trace(go.Scatter(
                        x=times[:len(wave_p)], y=wave_p, mode="lines", name="Wave Period (s)",
                        line=dict(color="#A23B72", width=1, dash="dot"),
                    ), row=1, col=1)
                if sst:
                    fig.add_trace(go.Scatter(
                        x=times[:len(sst)], y=sst, mode="lines", name="Sea Surface Temp (°C)",
                        line=dict(color="#C73E1D", width=2),
                        fill="tozeroy", fillcolor="rgba(199,62,29,0.1)",
                    ), row=2, col=1)
                if isinstance(current_marine, dict):
                    wh_now = current_marine.get("wave_height", "?")
                    sst_now = current_marine.get("sea_surface_temperature", "?")
                    fig.add_annotation(
                        text=f"Now: Waves {wh_now}m, SST {sst_now}°C",
                        xref="paper", yref="paper", x=0.02, y=0.98,
                        showarrow=False, font=dict(size=12, color="#fff"),
                        bgcolor="#17A2B8", bordercolor="#17A2B8",
                        xanchor="left", yanchor="top",
                    )
                fig.update_yaxes(title_text="Wave Height (m) / Period (s)", row=1, col=1)
                fig.update_yaxes(title_text="SST (°C)", row=2, col=1)
                fig.update_layout(
                    title="Marine Conditions — Wave Height, Period & Sea Surface Temperature",
                    height=GRAPH_HEIGHT + 50, margin=MARGIN,
                    legend=dict(orientation="h", y=-0.12), showlegend=True,
                )
                return fig
            # Fallback: just current values as bar chart
            if isinstance(current_marine, dict):
                for k, v in current_marine.items():
                    if k in ("time", "interval"):
                        continue
                    try:
                        names.append(k.replace("_", " ").title()[:25])
                        levels.append(float(v))
                    except (ValueError, TypeError):
                        pass

        # Try stations format
        if not names:
            stations = data.get("stations", [])
            if isinstance(stations, list) and stations:
                for s in stations[:12]:
                    if isinstance(s, dict):
                        name = s.get("name", s.get("station_name", "Station"))
                        names.append(str(name)[:25])
                        try:
                            level = float(s.get("water_level", s.get("wave_height", 0)) or 0)
                        except (ValueError, TypeError):
                            level = 0
                        levels.append(level)

        # Try observations format (NOAA NDBC)
        if not names:
            observations = data.get("observations", [])
            if isinstance(observations, list) and observations:
                for obs in observations[:12]:
                    if isinstance(obs, dict):
                        name = obs.get("station", obs.get("stationId", "Buoy"))
                        names.append(str(name)[:25])
                        # Try multiple value fields
                        level = None
                        for key in ("waterLevel", "water_level", "waveHeight", "wave_height",
                                    "wvht", "WVHT", "significantWaveHeight", "tide"):
                            val = obs.get(key)
                            if val is not None:
                                try:
                                    level = float(val)
                                    break
                                except (ValueError, TypeError):
                                    pass
                        if level is None:
                            # Try wind speed or water temp as fallback metric
                            for key in ("windSpeed", "wspd", "WSPD", "waterTemperature", "wtmp", "WTMP"):
                                val = obs.get(key)
                                if val is not None:
                                    try:
                                        level = float(val)
                                        break
                                    except (ValueError, TypeError):
                                        pass
                        levels.append(level if level is not None else 0)

        # Try data list format (US IOOS)
        if not names:
            data_list = data.get("data", [])
            if isinstance(data_list, list) and data_list:
                for item in data_list[:12]:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("station_name", "Station"))
                        names.append(str(name)[:25])
                        val = item.get("value", item.get("water_level", 0))
                        try:
                            levels.append(float(val or 0))
                        except (ValueError, TypeError):
                            levels.append(0)

        # Try to extract from any top-level numeric fields
        if not names:
            numeric_keys = []
            for k, v in data.items():
                if k.startswith("_"):
                    continue
                if isinstance(v, (int, float)):
                    numeric_keys.append((k, float(v)))
                elif isinstance(v, str):
                    try:
                        numeric_keys.append((k, float(v)))
                    except ValueError:
                        pass
            if numeric_keys:
                for k, v in numeric_keys[:12]:
                    names.append(k.replace("_", " ").title()[:25])
                    levels.append(v)

        if not names:
            return _empty_figure("No marine data — buoy stations may be offline", GRAPH_HEIGHT, MARGIN)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=names, x=levels, orientation="h",
            marker_color="#17A2B8",
            text=[f"{v:.2f}" for v in levels], textposition="outside",
        ))
        fig.update_layout(
            title="Marine Stations — Water Level / Wave Height",
            xaxis_title="Level (ft)", height=GRAPH_HEIGHT,
            margin=dict(l=160, r=30, t=50, b=50), showlegend=False,
        )
        return fig

    if cat_id == "radiation":
        # --- Parse radiation data from multiple formats ---
        # Format 1: Open-Meteo UV -> hourly{} with uv_index, direct_radiation, etc.
        # Format 2: Legacy measurements[] with location/value/region
        hourly_rad = data.get("hourly") or {}
        if isinstance(hourly_rad, dict) and hourly_rad.get("time"):
            times = hourly_rad.get("time", [])[:72]
            uv = hourly_rad.get("uv_index", [])[:72]
            direct = hourly_rad.get("direct_radiation", [])[:72]
            diffuse = hourly_rad.get("diffuse_radiation", [])[:72]
            shortwave = hourly_rad.get("shortwave_radiation", [])[:72]
            if times and (uv or direct or shortwave):
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    row_heights=[0.45, 0.55], vertical_spacing=0.08)
                if uv:
                    fig.add_trace(go.Scatter(
                        x=times[:len(uv)], y=uv, mode="lines", name="UV Index",
                        line=dict(color="#8F3F97", width=2),
                        fill="tozeroy", fillcolor="rgba(143,63,151,0.1)",
                    ), row=1, col=1)
                    fig.add_hline(y=6, line_dash="dash", line_color="#F18F01",
                                  annotation_text="UV 6 — High", annotation_position="top left",
                                  row=1, col=1)
                    fig.add_hline(y=11, line_dash="dash", line_color="#C73E1D",
                                  annotation_text="UV 11 — Extreme", annotation_position="top left",
                                  row=1, col=1)
                if shortwave:
                    fig.add_trace(go.Scatter(
                        x=times[:len(shortwave)], y=shortwave, mode="lines", name="Shortwave (W/m²)",
                        line=dict(color="#F18F01", width=1),
                        fill="tozeroy", fillcolor="rgba(241,143,1,0.08)",
                    ), row=2, col=1)
                if direct:
                    fig.add_trace(go.Scatter(
                        x=times[:len(direct)], y=direct, mode="lines", name="Direct (W/m²)",
                        line=dict(color="#C73E1D", width=1, dash="dot"),
                    ), row=2, col=1)
                if diffuse:
                    fig.add_trace(go.Scatter(
                        x=times[:len(diffuse)], y=diffuse, mode="lines", name="Diffuse (W/m²)",
                        line=dict(color="#2E86AB", width=1, dash="dot"),
                    ), row=2, col=1)
                # Peak UV annotation
                if uv:
                    clean_uv = [v for v in uv if v is not None]
                    if clean_uv:
                        peak_uv = max(clean_uv)
                        fig.add_annotation(
                            text=f"Peak UV: {peak_uv:.1f}",
                            xref="paper", yref="paper", x=0.02, y=0.98,
                            showarrow=False, font=dict(size=12, color="#fff"),
                            bgcolor="#8F3F97", bordercolor="#8F3F97",
                            xanchor="left", yanchor="top",
                        )
                fig.update_yaxes(title_text="UV Index", row=1, col=1)
                fig.update_yaxes(title_text="Radiation (W/m²)", row=2, col=1)
                fig.update_layout(
                    title="UV Index & Solar Radiation Forecast",
                    height=GRAPH_HEIGHT + 50, margin=MARGIN,
                    legend=dict(orientation="h", y=-0.12), showlegend=True,
                )
                return fig

        # Legacy format: measurements[] list
        measurements = data.get("measurements", [])[:20]
        if not measurements:
            return _empty_figure("No radiation data", GRAPH_HEIGHT, MARGIN)
        # Build readable location labels from available fields
        locations = []
        values = []
        for m in measurements:
            loc = m.get("location") or m.get("city") or m.get("name") or ""
            region = m.get("region") or m.get("state") or m.get("country") or ""
            if not loc or loc.lower() == "unknown":
                loc = region if region else f"({m.get('latitude', '?')}, {m.get('longitude', '?')})"
            elif region:
                loc = f"{loc}, {region}"
            locations.append(loc[:30])
            values.append(float(m.get("value", 0) or 0))
        fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45],
                            specs=[[{"type": "xy"}, {"type": "indicator"}]])
        # Bar chart
        bar_colors = ["#28A745" if v < 50 else "#F18F01" if v < 100 else "#C73E1D" for v in values]
        fig.add_trace(go.Bar(
            y=locations, x=values, orientation="h",
            marker_color=bar_colors,
            text=[f"{v:.0f}" for v in values], textposition="outside",
        ), row=1, col=1)
        # Gauge
        avg_val = sum(values) / len(values) if values else 0
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=avg_val,
            title={"text": "Avg CPM"},
            gauge={
                "axis": {"range": [0, 200]},
                "bar": {"color": "#8F3F97"},
                "steps": [
                    {"range": [0, 50], "color": "#E8F5E9"},
                    {"range": [50, 100], "color": "#FFF9C4"},
                    {"range": [100, 200], "color": "#FFCDD2"},
                ],
                "threshold": {"line": {"color": "#C73E1D", "width": 2}, "thickness": 0.75, "value": 100},
            },
        ), row=1, col=2)
        fig.update_layout(
            title="Radiation Levels (CPM) by Location",
            height=GRAPH_HEIGHT, margin=dict(l=160, r=30, t=50, b=50), showlegend=False,
        )
        return fig

    if cat_id == "wildfires":
        # --- Parse wildfire data from multiple formats ---
        # Format 1: incidents[] (expected custom format)
        # Format 2: GeoJSON features[] (NIFC ArcGIS)
        # Format 3: NASA FIRMS fire points
        incidents = []

        # Try incidents format
        raw_incidents = data.get("incidents", [])
        if isinstance(raw_incidents, list):
            for i in raw_incidents:
                if isinstance(i, dict):
                    title = i.get("title", i.get("name", "Fire"))
                    # Handle string acres (e.g., "1,234" or "1234.5")
                    acres_raw = i.get("acres_burned", i.get("acres", 0))
                    try:
                        acres = float(str(acres_raw).replace(",", "")) if acres_raw else 0
                    except (ValueError, TypeError):
                        acres = 0
                    cont_raw = i.get("percent_contained", i.get("containment", 0))
                    try:
                        containment = float(str(cont_raw).replace("%", "")) if cont_raw else 0
                    except (ValueError, TypeError):
                        containment = 0
                    incidents.append({"title": str(title), "acres": acres, "containment": containment})

        # Try GeoJSON features format (NIFC)
        if not incidents:
            features = data.get("features", [])
            if isinstance(features, list):
                for f in features:
                    if not isinstance(f, dict):
                        continue
                    props = f.get("properties", f.get("attributes", {}))
                    if not isinstance(props, dict):
                        continue
                    title = props.get("IncidentName", props.get("poly_IncidentName",
                            props.get("irwin_FireDiscoveryDateTime", "Fire")))
                    acres_raw = props.get("GISAcres", props.get("poly_GISAcres",
                                props.get("irwin_DailyAcres", props.get("BurnBndAc", 0))))
                    try:
                        acres = float(str(acres_raw).replace(",", "")) if acres_raw else 0
                    except (ValueError, TypeError):
                        acres = 0
                    cont_raw = props.get("PercentContained", props.get("irwin_PercentContained", 0))
                    try:
                        containment = float(str(cont_raw).replace("%", "")) if cont_raw else 0
                    except (ValueError, TypeError):
                        containment = 0
                    incidents.append({"title": str(title)[:25], "acres": acres, "containment": containment})

        # Try flat fire points (NASA FIRMS)
        if not incidents:
            fire_list = data.get("fires", data.get("data", []))
            if isinstance(fire_list, list):
                for fp in fire_list[:15]:
                    if isinstance(fp, dict):
                        # FIRMS uses brightness/frp instead of acres
                        bright = fp.get("brightness", fp.get("bright_ti4", fp.get("frp", 0)))
                        try:
                            bright_val = float(bright) if bright else 0
                        except (ValueError, TypeError):
                            bright_val = 0
                        incidents.append({
                            "title": f"Fire ({fp.get('latitude', '?')}, {fp.get('longitude', '?')})",
                            "acres": bright_val,
                            "containment": -1,  # FIRMS doesn't provide containment
                        })

        if not incidents:
            return _empty_figure(
                "No active wildfire data — this may be normal for this region",
                GRAPH_HEIGHT, MARGIN,
            )

        incidents = incidents[:15]
        names = [i["title"][:25] for i in incidents]
        acres = [i["acres"] for i in incidents]
        containment = [i["containment"] for i in incidents]

        fig = make_subplots(rows=1, cols=2, column_widths=[0.6, 0.4], shared_yaxes=True)
        fig.add_trace(go.Bar(
            y=names, x=acres, orientation="h",
            marker_color="#F18F01",
            text=[f"{a:,.0f}" for a in acres], textposition="outside",
            name="Acres Burned",
        ), row=1, col=1)

        # Containment: -1 means unknown (FIRMS), >= 0 means known (NIFC)
        has_known_containment = any(c >= 0 for c in containment)
        bar_colors = []
        bar_texts = []
        display_vals = []
        for c in containment:
            if c < 0:
                bar_colors.append("#CCCCCC")
                bar_texts.append("N/A")
                display_vals.append(5)  # small bar to show N/A label
            else:
                bar_colors.append("#28A745" if c >= 50 else "#F18F01")
                bar_texts.append(f"{c:.0f}%")
                display_vals.append(c)

        fig.add_trace(go.Bar(
            y=names, x=display_vals, orientation="h",
            marker_color=bar_colors,
            text=bar_texts, textposition="outside",
            name="Containment %",
        ), row=1, col=2)
        fig.update_xaxes(title_text="Acres / Brightness (FRP)", row=1, col=1)
        containment_title = "Containment %" if has_known_containment else "Containment % (N/A = FIRMS source)"
        fig.update_xaxes(title_text=containment_title, range=[0, 110], row=1, col=2)
        fig.update_layout(
            title="Active Wildfires — Size & Containment",
            height=GRAPH_HEIGHT, margin=dict(l=160, r=30, t=50, b=50),
            showlegend=False,
        )
        return fig

    if cat_id == "biodiversity":
        results = data.get("results", [])[:80]
        if not results:
            return _empty_figure("No biodiversity data", GRAPH_HEIGHT + 120, MARGIN)

        # Build genus -> species hierarchy for treemap
        genus_species: Dict[str, Dict[str, int]] = {}
        for r in results:
            if not isinstance(r, dict):
                continue
            species = r.get("species", r.get("scientificName", "Unknown"))
            genus = r.get("genus", r.get("genericName", ""))
            if not genus:
                parts = str(species).split()
                genus = parts[0] if parts else "Unknown"
            genus_species.setdefault(genus, {})
            genus_species[genus][species] = genus_species[genus].get(species, 0) + 1

        if not genus_species:
            return _empty_figure("No species data", GRAPH_HEIGHT + 120, MARGIN)

        # Build treemap arrays: root -> genus -> species
        ids = ["All Observations"]
        labels = ["All"]
        parents = [""]
        values = [0]
        colors_list = ["#E8F5E9"]

        genus_colors = ["#2E7D32", "#388E3C", "#43A047", "#4CAF50",
                        "#66BB6A", "#81C784", "#A5D6A7", "#1B5E20",
                        "#00695C", "#00796B", "#00897B", "#009688"]

        for g_idx, (genus, sp_dict) in enumerate(
            sorted(genus_species.items(), key=lambda x: -sum(x[1].values()))[:15]
        ):
            genus_total = sum(sp_dict.values())
            genus_id = f"genus-{genus}"
            ids.append(genus_id)
            labels.append(genus)
            parents.append("All Observations")
            values.append(genus_total)
            colors_list.append(genus_colors[g_idx % len(genus_colors)])

            for sp_name, count in sorted(sp_dict.items(), key=lambda x: -x[1])[:10]:
                sp_id = f"{genus_id}-{sp_name}"
                ids.append(sp_id)
                labels.append(sp_name.split()[-1] if " " in sp_name else sp_name)
                parents.append(genus_id)
                values.append(count)
                colors_list.append(genus_colors[g_idx % len(genus_colors)])

        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors_list),
            textinfo="label+value+percent parent",
            hovertemplate="<b>%{label}</b><br>Observations: %{value}<br>%{percentParent:.1%} of parent<extra></extra>",
            maxdepth=3,
        ))
        fig.update_layout(
            title="Biodiversity — Species Observations by Genus (click to drill down)",
            height=GRAPH_HEIGHT + 180,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        return fig

    if cat_id == "climate":
        daily = data.get("daily", {})
        if daily:
            times = daily.get("time", [])[:30]
            t_max = daily.get("temperature_2m_max", [])[:30]
            t_min = daily.get("temperature_2m_min", [])[:30]
            precip = daily.get("precipitation_sum", [])[:30]
            if times and t_max:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    row_heights=[0.65, 0.35], vertical_spacing=0.08)
                if t_min:
                    fig.add_trace(go.Scatter(
                        x=times, y=t_min, mode="lines", name="Min Temp",
                        line=dict(color="#2E86AB", width=1),
                        fill=None,
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=times, y=t_max, mode="lines", name="Max Temp",
                        line=dict(color="#C73E1D", width=1),
                        fill="tonexty", fillcolor="rgba(199,62,29,0.15)",
                    ), row=1, col=1)
                else:
                    fig.add_trace(go.Scatter(
                        x=times, y=t_max, mode="lines", name="Max Temp",
                        line=dict(color="#C73E1D", width=2),
                    ), row=1, col=1)
                if precip:
                    fig.add_trace(go.Bar(
                        x=times[:len(precip)], y=precip, name="Precip (mm)",
                        marker_color="#4ECDC4", opacity=0.7,
                    ), row=2, col=1)
                fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
                fig.update_yaxes(title_text="Precip (mm)", row=2, col=1)
                fig.update_layout(
                    title="Climate — Temperature Range & Precipitation",
                    height=GRAPH_HEIGHT + 50, margin=MARGIN,
                    legend=dict(orientation="h", y=-0.12), showlegend=True,
                )
                return fig
        return _empty_figure("No climate data", GRAPH_HEIGHT, MARGIN)

    if cat_id == "soil":
        # --- Soil Depth-Profile Visualization ---
        # Shows soil properties across depth layers with grouped horizontal bars
        layers = data.get("properties", {}).get("layers", [])
        if not isinstance(layers, list) or not layers:
            return _empty_figure(
                "No soil data — SoilGrids may not cover this location",
                GRAPH_HEIGHT + 80, MARGIN,
            )

        # Parse each layer into depth-series data
        depth_labels = []
        layer_traces = []
        colors = ["#795548", "#A1887F", "#8D6E63", "#6D4C41",
                  "#5D4037", "#4E342E", "#3E2723", "#D7CCC8"]

        for idx, layer in enumerate(layers[:6]):
            if not isinstance(layer, dict):
                continue
            name = layer.get("name", "Unknown")
            unit = layer.get("unit_measure", {}).get("mapped_units", "")
            depths = layer.get("depths", [])
            if not depths:
                continue
            d_labels = []
            d_values = []
            for d in depths:
                if not isinstance(d, dict):
                    continue
                rng = d.get("range", {})
                top = rng.get("top_depth", "?")
                bot = rng.get("bottom_depth", "?")
                label = f"{top}-{bot} cm"
                mean_val = (d.get("values") or {}).get("mean")
                if mean_val is not None:
                    d_labels.append(label)
                    try:
                        d_values.append(float(mean_val))
                    except (ValueError, TypeError):
                        d_values.append(0)
            if d_values:
                if not depth_labels:
                    depth_labels = d_labels
                display_name = f"{name} ({unit})" if unit else name
                layer_traces.append((display_name, d_values, colors[idx % len(colors)]))

        if not layer_traces:
            return _empty_figure(
                "No soil data — SoilGrids may not cover this location",
                GRAPH_HEIGHT + 80, MARGIN,
            )

        fig = go.Figure()
        for trace_name, vals, color in layer_traces:
            fig.add_trace(go.Bar(
                y=depth_labels[:len(vals)],
                x=vals,
                orientation="h",
                name=trace_name,
                marker_color=color,
                text=[f"{v:.0f}" for v in vals],
                textposition="outside",
            ))
        fig.update_layout(
            title="Soil Properties by Depth Layer",
            xaxis_title="Value",
            yaxis_title="Depth Range",
            yaxis=dict(autorange="reversed"),  # deeper = lower on chart
            barmode="group",
            height=GRAPH_HEIGHT + 120,
            margin=dict(l=100, r=40, t=50, b=50),
            legend=dict(orientation="h", y=-0.18, font=dict(size=10)),
            showlegend=True,
        )
        return fig

    # Fallback for unknown categories
    return _empty_figure(f"No visualization for {cat_id}", GRAPH_HEIGHT, MARGIN)


def _empty_figure(message: str, height: int, margin: dict, api_url: str = "") -> Any:
    """Create an empty figure with a centered message and optional API link."""
    import plotly.graph_objects as go
    display_text = message
    if api_url:
        display_text += f'<br><br><a href="{api_url}" target="_blank" style="color:#2E86AB">View raw API data</a>'
    fig = go.Figure()
    fig.add_annotation(
        text=display_text, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color="#6C757D"),
    )
    fig.update_layout(
        height=height, margin=margin,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def create_intersection_graph(summary_data: Dict, cat1: str, cat2: str) -> dict:
    """Create a meaningful cross-domain correlation visualization.

    Uses dual-axis layout with shared time axis to show how two
    environmental domains relate. Falls back to a grouped radar/bar
    comparison if no time-series data is available.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    data1 = summary_data.get(cat1, {})
    data2 = summary_data.get(cat2, {})

    if not data1 and not data2:
        return None

    # Filter to numeric-only entries
    nums1 = {k: v for k, v in data1.items() if isinstance(v, (int, float)) and v is not None}
    nums2 = {k: v for k, v in data2.items() if isinstance(v, (int, float)) and v is not None}

    if not nums1 and not nums2:
        return None

    cat1_label = cat1.replace("_", " ").title()
    cat2_label = cat2.replace("_", " ").title()

    # --- Dual-axis bar comparison ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if nums1:
        fig.add_trace(go.Bar(
            x=list(nums1.keys()),
            y=list(nums1.values()),
            name=cat1_label,
            marker_color="#2E86AB",
            opacity=0.8,
            text=[f"{v:.1f}" for v in nums1.values()],
            textposition="outside",
        ), secondary_y=False)

    if nums2:
        fig.add_trace(go.Bar(
            x=list(nums2.keys()),
            y=list(nums2.values()),
            name=cat2_label,
            marker_color="#A23B72",
            opacity=0.8,
            text=[f"{v:.1f}" for v in nums2.values()],
            textposition="outside",
        ), secondary_y=True)

    fig.update_layout(
        height=300,
        margin=dict(l=50, r=50, t=50, b=60),
        barmode="group",
        legend=dict(orientation="h", y=-0.2),
        title=f"{cat1_label} vs {cat2_label} — Key Metrics",
    )
    fig.update_yaxes(title_text=cat1_label, secondary_y=False)
    fig.update_yaxes(title_text=cat2_label, secondary_y=True)

    return fig


def merge_category_sources(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge a list of source responses into a single combined dict."""
    combined: Dict[str, Any] = {}

    for source in data_list:
        if not isinstance(source, dict):
            continue

        source_data = source.get("data", source)
        if not isinstance(source_data, dict):
            continue

        for key, value in source_data.items():
            if key not in combined:
                combined[key] = value
            elif isinstance(value, list) and isinstance(combined[key], list):
                combined[key].extend(value)
            elif isinstance(value, dict) and isinstance(combined[key], dict):
                combined[key].update(value)

    return combined


def extract_category_summary(category_id: str, combined: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a lightweight summary for intersection graphs."""
    summary: Dict[str, Any] = {}

    if category_id == "air_quality":
        # Try direct AQI values (Open-Meteo format)
        for aqi_key in ("us_aqi", "european_aqi", "aqi", "aqi_value"):
            val = combined.get(aqi_key)
            if val is not None:
                if isinstance(val, list):
                    summary["us_aqi"] = val[0] if val else None
                else:
                    summary["us_aqi"] = val
                break
        # Try hourly AQI
        if summary.get("us_aqi") is None:
            hourly = combined.get("hourly", {})
            if isinstance(hourly, dict):
                for aqi_key in ("us_aqi", "european_aqi"):
                    vals = hourly.get(aqi_key, [])
                    if vals:
                        clean = [v for v in vals if v is not None]
                        if clean:
                            summary["us_aqi"] = clean[0]
                            break

        # Try OpenAQ locations format
        results = combined.get("results", [])
        if isinstance(results, list):
            pm25_values = []
            for loc in results:
                if not isinstance(loc, dict):
                    continue
                for p in loc.get("parameters", []):
                    if isinstance(p, dict) and p.get("parameter") in {"pm25", "PM2.5"}:
                        val = p.get("lastValue") or p.get("average")
                        if val is not None:
                            pm25_values.append(float(val))
                # Legacy measurement format
                if loc.get("parameter") in {"pm25", "PM2.5"} and loc.get("value") is not None:
                    pm25_values.append(float(loc["value"]))
            if pm25_values and summary.get("us_aqi") is None:
                summary["pm25"] = sum(pm25_values) / len(pm25_values)

        # Legacy measurements format
        measurements = combined.get("measurements", [])
        if isinstance(measurements, list) and summary.get("us_aqi") is None and not summary.get("pm25"):
            pm25_values = [
                m.get("value") for m in measurements
                if isinstance(m, dict) and m.get("parameter") in {"pm25", "PM2.5"}
            ]
            if pm25_values:
                summary["pm25"] = sum(float(v) for v in pm25_values if v is not None) / len(pm25_values)

    if category_id == "weather":
        current = combined.get("current_weather", {})
        summary["temperature_c"] = current.get("temperature") or combined.get("temperature_c")
        summary["wind_speed_kmh"] = current.get("windspeed") or combined.get("wind_speed_kmh")

    return summary


# ==================== LAYOUT CREATION ====================

def create_dashboard_layout():
    """Create the main dashboard layout."""
    return html.Div([
        # Initial load trigger
        dcc.Interval(id="initial-load-trigger", interval=500, n_intervals=0, max_intervals=1),
        
        # Data store for loaded category data
        dcc.Store(id="loaded-category-data", data=None),
        
        # Track categories auto-disabled due to no data at location
        dcc.Store(id="auto-disabled-categories", data=[]),
        
        # Page header
        html.H2("Environmental Dashboard", className="mb-4"),
        
        # Filter status bar
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Span(id="filter-location-display", className="badge bg-primary me-2"),
                        html.Span(id="filter-time-display", className="badge bg-secondary me-2"),
                        html.Span(id="filter-categories-display", className="badge bg-info me-2"),
                    ], width="auto"),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-sync-alt me-1"), "Reload All"],
                            id="reload-all-data-btn", color="outline-primary", size="sm",
                        )
                    ], width="auto", className="ms-auto")
                ], align="center")
            ], className="py-2")
        ], className="mb-4"),
        
        # Stats row
        dbc.Row(id="dashboard-stats-row", className="mb-4"),
        
        # Quick check panel
        dbc.Card([
            dbc.CardHeader([
                html.H5("Quick Location Check", className="mb-0 d-inline"),
                dbc.Spinner(
                    html.Span(id="loading-indicator", className="text-muted small"),
                    size="sm",
                    color="primary",
                    spinner_class_name="ms-2",
                ),
            ], className="d-flex justify-content-between align-items-center"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.InputGroupText("Location"),
                            dbc.Input(
                                id="quick-check-lat", 
                                type="number", 
                                placeholder="Latitude", 
                                value=MAP_CONFIG["default_lat"], 
                                step=0.0001
                            ),
                            dbc.Input(
                                id="quick-check-lon", 
                                type="number", 
                                placeholder="Longitude",
                                value=MAP_CONFIG["default_lon"], 
                                step=0.0001
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-check me-1"), "Check"],
                                id="quick-check-btn", color="primary",
                            )
                        ])
                    ], md=6),
                    dbc.Col([
                        html.Div(id="quick-check-status")
                    ], md=6)
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            html.Div(id="aqi-gauge-container"),
                            type="circle",
                            overlay_style={"visibility": "visible", "opacity": 0.5},
                        )
                    ], md=4),
                    dbc.Col([
                        dcc.Loading(
                            html.Div(id="weather-summary-container"),
                            type="circle",
                            overlay_style={"visibility": "visible", "opacity": 0.5},
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Alert([
                            html.H6("Environmental Status", className="alert-heading"),
                            html.P("Select a location to view current conditions.", className="mb-0")
                        ], color="info", id="env-status-alert")
                    ], md=4)
                ])
            ])
        ], className="mb-4"),
        
        # Main content row - Map and Data
        dbc.Row([
            # Map column
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Environmental Data Map", className="mb-0 d-inline"),
                        html.Small(id="map-data-count", className="float-end text-muted")
                    ]),
                    dbc.CardBody([
                        dcc.Loading(
                            html.Div(id="dashboard-map"),
                            type="circle",
                            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                        )
                    ])
                ])
            ], lg=8, className="mb-4"),
            
            # Side panel column
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Active Alerts", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="alerts-panel", children=[
                            html.P("No active alerts", className="text-muted text-center")
                        ])
                    ])
                ], className="mb-3"),
                dbc.Card([
                    dbc.CardHeader(html.H5("Quick Stats", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="quick-stats-panel")
                    ])
                ])
            ], lg=4, className="mb-4")
        ]),
        
        # Category-specific graphs
        dcc.Loading(
            id="loading-category-graphs",
            type="default",
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
            children=html.Div(id="category-graphs-container", className="mb-4"),
        ),
        
        # Intersection graph (hidden - not meaningful enough yet)
        html.Div(id="intersection-graph-container", className="mb-4", style={"display": "none"}),
        
        # Data Categories Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Data Categories", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="categories-summary-container")
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Data Sources Status", className="mb-0"),
                        dbc.Button("View All", href="/explore", color="link", size="sm")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="data-sources-status-container")
                    ])
                ])
            ], md=6)
        ]),

        # ── Activity Log ──
        create_progress_box("dash", [
            "progress-dash-qc",
            "progress-dash-cats",
            "progress-dash-graphs",
            "progress-dash-map",
            "progress-dash-stats",
        ]),
    ])


# ==================== FILTER STATUS BAR CALLBACKS ====================

@callback(
    [Output("filter-location-display", "children"),
     Output("filter-time-display", "children"),
     Output("filter-categories-display", "children")],
    [Input("quick-check-lat", "value"),
     Input("quick-check-lon", "value"),
     Input("global-time-range", "value"),
     Input("category-checklist", "value")],
    prevent_initial_call=False
)
def update_filter_display(lat, lon, time_range, categories):
    """Update the filter status bar to show current selections."""
    lat = lat or 37.7749
    lon = lon or -122.4194
    time_range = time_range or "7D"
    categories = categories or []
    
    location_text = f"Lat: {lat:.2f}, Lon: {lon:.2f}"
    time_text = f"Range: {time_range}"
    cat_text = f"{len(categories)} categories"
    
    return location_text, time_text, cat_text


# ==================== CENTRAL DATA LOADING CALLBACK ====================

@callback(
    [Output("loaded-category-data", "data"),
     Output("progress-dash-cats", "data")],
    [Input("quick-check-btn", "n_clicks"),
     Input("location-updated-trigger", "data"),
     Input("global-time-range", "value"),
     Input("category-checklist", "value"),
     Input("reload-all-data-btn", "n_clicks"),
     Input("initial-load-trigger", "n_intervals")],
    [State("quick-check-lat", "value"),
     State("quick-check-lon", "value"),
     State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=False
)
def load_all_category_data(
    quick_clicks, location_trigger, time_range, categories, 
    reload_clicks, n_intervals, quick_lat, quick_lon, 
    sidebar_lat, sidebar_lon
):
    """
    Central data loading callback - triggers on:
    - Quick check button
    - Location search (via trigger store, after geocoding completes)
    - Category selection changes
    - Reload all button
    - Initial page load (via interval)
    """
    _t0 = time.time()
    triggered = ctx.triggered_id
    
    if triggered == "location-updated-trigger" and location_trigger:
        lat = location_trigger.get("lat", 37.7749)
        lon = location_trigger.get("lon", -122.4194)
    else:
        lat = quick_lat or 37.7749
        lon = quick_lon or -122.4194
    
    if not categories:
        categories = [
            "air_quality", "weather", "water", "marine",
            "earthquakes", "radiation", "climate", "soil",
            "wildfires", "biodiversity",
        ]
    
    loaded_data = {
        "location": {"lat": lat, "lon": lon},
        "timestamp": datetime.now().isoformat(),
        "time_range": time_range or "7D",
        "categories": {}
    }

    effective_time = time_range or "7D"
    _TIME_RANGE_TO_DAYS = {
        "1H": 1, "6H": 1, "24H": 1, "7D": 7,
        "30D": 30, "90D": 90, "1Y": 365, "custom": 30,
    }
    effective_days = _TIME_RANGE_TO_DAYS.get(effective_time, 7)

    # ---- Parallel API fetch for ALL categories at once ----
    api_results = get_categories_parallel(categories, lat, lon, days=effective_days)

    for cat_id in categories:
        try:
            cat_data = api_results.get(cat_id, {"error": "No response"})

            # Data Commons (only for long time ranges -- DC data is annual)
            dc_data = {}
            if cat_id in CATEGORY_VARIABLES and effective_time in ("90D", "1Y", "custom"):
                try:
                    dc_data = get_dc_category_data(cat_id, lat, lon)
                except Exception as dc_err:
                    logger.warning("DC fetch for %s failed: %s", cat_id, dc_err)

            data_list = cat_data.get("data") or cat_data.get("sources") or []
            combined_data = merge_category_sources(data_list)

            if dc_data:
                combined_data["_data_commons"] = dc_data

            loaded_data["categories"][cat_id] = {
                "combined": combined_data,
                "summary": _build_merged_summary(cat_id, combined_data, dc_data),
                "raw": data_list,
                "dc": dc_data,
            }
        except Exception as e:
            loaded_data["categories"][cat_id] = {"error": str(e)}

    # ── Build progress log entries ──
    _elapsed = int((time.time() - _t0) * 1000)
    progress = []
    progress.append(make_entry("info", f"Fetching data for ({lat:.2f}, {lon:.2f}), {len(categories)} categories"))
    for _cid in categories:
        _cr = loaded_data["categories"].get(_cid, {})
        _raw_sources = _cr.get("raw", [])
        _n_src = len(_raw_sources) if isinstance(_raw_sources, list) else 0
        _src_names = []
        if isinstance(_raw_sources, list):
            for _rs in _raw_sources:
                if isinstance(_rs, dict):
                    _src_names.append(_rs.get("source", _rs.get("source_id", "?")))
        _src_label = f" [{', '.join(_src_names)}]" if _src_names else ""

        if "error" in _cr:
            progress.append(make_entry("error", f"{_cid}: {str(_cr['error'])[:60]}"))
        elif _is_category_empty(_cr):
            progress.append(make_entry("warning", f"{_cid}: 0 records from {_n_src} source(s){_src_label}"))
        else:
            _combined = _cr.get("combined", {})
            _rc = _count_records(_cid, _combined)
            _detail = _summarize_for_log(_cid, _cr.get("summary", {}), _rc)
            _status = "complete" if _rc > 0 else "warning"
            progress.append(make_entry(_status, f"{_cid}: {_detail} ({_n_src} src{_src_label})"))
    progress.append(make_entry("complete", f"All {len(categories)} categories processed", duration_ms=_elapsed))

    return loaded_data, progress


def _build_merged_summary(
    category_id: str,
    combined: Dict[str, Any],
    dc_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Build category summary with DC data taking precedence."""
    # Start with backend-derived summary
    summary = extract_category_summary(category_id, combined)
    # Override with DC values where available
    if dc_data:
        dc_summary = get_dc_summary_for_category(category_id, dc_data)
        for key, val in dc_summary.items():
            if val is not None:
                summary[key] = val
    return summary


# ==================== MAP UPDATE CALLBACK ====================

@callback(
    [Output("dashboard-map", "children"),
     Output("map-data-count", "children"),
     Output("progress-dash-map", "data")],
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_dashboard_map(loaded_data):
    """Update the map with loaded category data using Plotly Scattermapbox (no API key needed)."""
    _map_t0 = time.time()
    location = loaded_data.get("location", {}) if loaded_data else {}
    lat = location.get("lat", MAP_CONFIG["default_lat"])
    lon = location.get("lon", MAP_CONFIG["default_lon"])
    categories_data = loaded_data.get("categories", {}) if loaded_data else {}

    # Category color map — distinct, colorblind-friendly palette
    cat_colors = {
        "earthquakes": "#C73E1D",   # Red
        "wildfires": "#F18F01",     # Orange
        "air_quality": "#2E86AB",   # Blue
        "radiation": "#8F3F97",     # Purple
        "marine": "#00B4D8",        # Cyan
        "biodiversity": "#2D6A4F",  # Dark green
        "weather": "#E9C46A",       # Gold
        "water": "#0077B6",         # Navy blue
        "climate": "#6C757D",       # Grey
        "soil": "#BC6C25",          # Brown
    }

    # Collect data points by category for separate traces
    traces_by_cat: Dict[str, List[Dict]] = {}
    total_points = 0

    for cat_id, data in categories_data.items():
        if not isinstance(data, dict) or "error" in data:
            continue

        combined = data.get("combined", {})
        points = []

        if cat_id == "earthquakes":
            for f in combined.get("features", [])[:30]:
                coords = f.get("geometry", {}).get("coordinates", [])
                props = f.get("properties", {})
                if len(coords) >= 2:
                    points.append({
                        "lat": coords[1], "lon": coords[0],
                        "text": f"M{props.get('mag', '?')} - {props.get('place', 'Unknown')}",
                        "size": max(6, (props.get("mag", 2) or 2) * 4),
                    })

        elif cat_id == "wildfires":
            # Try incidents format
            for inc in combined.get("incidents", [])[:30]:
                if isinstance(inc, dict) and inc.get("latitude") and inc.get("longitude"):
                    try:
                        acres = float(str(inc.get('acres_burned', inc.get('acres', 0)) or 0).replace(",", ""))
                    except (ValueError, TypeError):
                        acres = 0
                    points.append({
                        "lat": float(inc["latitude"]), "lon": float(inc["longitude"]),
                        "text": f"{inc.get('title', 'Fire')} - {acres:,.0f} acres",
                        "size": 10,
                    })
            # Try GeoJSON features format
            if not points:
                for f in combined.get("features", [])[:30]:
                    if not isinstance(f, dict):
                        continue
                    geom = f.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    props = f.get("properties", f.get("attributes", {}))
                    if isinstance(coords, list) and len(coords) >= 2 and isinstance(props, dict):
                        # Polygon centroid or point
                        if isinstance(coords[0], list):
                            # Skip complex polygons for now
                            continue
                        points.append({
                            "lat": float(coords[1]), "lon": float(coords[0]),
                            "text": props.get("IncidentName", props.get("poly_IncidentName", "Fire")),
                            "size": 10,
                        })
            # Try NASA FIRMS fire points format
            if not points:
                fire_list = combined.get("fires", combined.get("data", []))
                if isinstance(fire_list, list):
                    for fp in fire_list[:30]:
                        if isinstance(fp, dict) and fp.get("latitude") and fp.get("longitude"):
                            try:
                                frp = float(fp.get("frp", fp.get("brightness", 0)) or 0)
                            except (ValueError, TypeError):
                                frp = 0
                            points.append({
                                "lat": float(fp["latitude"]),
                                "lon": float(fp["longitude"]),
                                "text": f"Fire: FRP {frp:.1f} MW ({fp.get('acq_date', 'N/A')})",
                                "size": max(7, min(14, frp / 10)),
                            })
            # Fallback: pin at search location if category has data
            if not points and combined:
                fire_count = len(combined.get("fires", []))
                if fire_count > 0:
                    points.append({
                        "lat": lat, "lon": lon,
                        "text": f"Wildfire data: {fire_count} fire points (coords unavailable)",
                        "size": 10,
                    })

        elif cat_id == "air_quality":
            # Try OpenAQ locations format (results[] with coordinates)
            for loc in combined.get("results", [])[:20]:
                if isinstance(loc, dict):
                    loc_lat = loc.get("latitude") or (loc.get("coordinates", {}) or {}).get("latitude")
                    loc_lon = loc.get("longitude") or (loc.get("coordinates", {}) or {}).get("longitude")
                    if loc_lat and loc_lon:
                        # Get a representative value from parameters
                        params = loc.get("parameters", [])
                        param_text = ""
                        if isinstance(params, list) and params:
                            p = params[0]
                            param_text = f"{p.get('parameter', 'AQ')}: {p.get('lastValue', 'N/A')}"
                        elif loc.get("parameter"):
                            param_text = f"{loc['parameter']}: {loc.get('value', 'N/A')}"
                        points.append({
                            "lat": float(loc_lat), "lon": float(loc_lon),
                            "text": param_text or f"AQ station: {loc.get('name', loc.get('location', 'Station'))}",
                            "size": 8,
                        })
            # Legacy measurements format
            if not points:
                for m in combined.get("measurements", [])[:20]:
                    if isinstance(m, dict) and m.get("latitude") and m.get("longitude"):
                        points.append({
                            "lat": m["latitude"], "lon": m["longitude"],
                            "text": f"{m.get('parameter', 'AQ')}: {m.get('value', 'N/A')} {m.get('unit', '')}",
                            "size": 8,
                        })
            # Fallback: pin at search location if we have data but no coords
            if not points and combined:
                points.append({
                    "lat": lat, "lon": lon,
                    "text": "Air quality data (station coords unavailable)",
                    "size": 10,
                })

        elif cat_id == "radiation":
            for m in combined.get("measurements", [])[:30]:
                if m.get("latitude") and m.get("longitude"):
                    points.append({
                        "lat": m["latitude"], "lon": m["longitude"],
                        "text": f"Radiation: {m.get('value', '?')} {m.get('unit', 'cpm')}",
                        "size": 8,
                    })

        elif cat_id == "marine":
            # Try stations format
            for s in combined.get("stations", [])[:20]:
                if isinstance(s, dict):
                    slat = s.get("latitude", s.get("lat"))
                    slon = s.get("longitude", s.get("lon"))
                    if slat and slon:
                        points.append({
                            "lat": float(slat), "lon": float(slon),
                            "text": f"{s.get('name', 'Marine Station')} - Level: {s.get('water_level', 'N/A')}",
                            "size": 8,
                        })
            # Try observations format
            if not points:
                for obs in combined.get("observations", [])[:20]:
                    if isinstance(obs, dict):
                        slat = obs.get("latitude", obs.get("lat"))
                        slon = obs.get("longitude", obs.get("lon"))
                        if slat and slon:
                            points.append({
                                "lat": float(slat), "lon": float(slon),
                                "text": f"Buoy {obs.get('station', obs.get('stationId', 'Unknown'))}",
                                "size": 8,
                            })
            # Fallback: pin at search location
            if not points and combined:
                points.append({
                    "lat": lat, "lon": lon,
                    "text": "Marine data (station coords unavailable)",
                    "size": 10,
                })

        elif cat_id == "biodiversity":
            for r in combined.get("results", [])[:30]:
                dlat = r.get("decimalLatitude")
                dlon = r.get("decimalLongitude")
                if dlat and dlon:
                    points.append({
                        "lat": dlat, "lon": dlon,
                        "text": r.get("species", r.get("scientificName", "Unknown")),
                        "size": 7,
                    })

        elif cat_id == "weather":
            current = combined.get("current_weather", {})
            if current:
                temp = current.get("temperature", "?")
                wind = current.get("windspeed", "?")
                points.append({
                    "lat": lat, "lon": lon,
                    "text": f"Weather: {temp}\u00b0C, Wind {wind} km/h",
                    "size": 12,
                })

        elif cat_id == "water":
            for s in combined.get("value", {}).get("timeSeries", [])[:15]:
                geo = s.get("sourceInfo", {}).get("geoLocation", {})
                slat = geo.get("latitude") or geo.get("geogLocation", {}).get("latitude")
                slon = geo.get("longitude") or geo.get("geogLocation", {}).get("longitude")
                if slat and slon:
                    site_name = s.get("sourceInfo", {}).get("siteName", "Station")
                    points.append({
                        "lat": float(slat), "lon": float(slon),
                        "text": f"Water: {site_name[:30]}",
                        "size": 8,
                    })
            if not points:
                # Fallback: show pin at search location
                points.append({
                    "lat": lat, "lon": lon,
                    "text": "Water data (no station coords)",
                    "size": 10,
                })

        elif cat_id == "climate":
            daily = combined.get("daily", {})
            if daily and daily.get("temperature_2m_max"):
                t_max_vals = daily["temperature_2m_max"][:7]
                avg_t = sum(float(v) for v in t_max_vals) / len(t_max_vals) if t_max_vals else 0
                points.append({
                    "lat": lat, "lon": lon,
                    "text": f"Climate: avg max {avg_t:.1f}\u00b0C",
                    "size": 11,
                })

        elif cat_id == "soil":
            # SoilGrids or USDA data — show pin at search location
            has_data = bool(
                combined.get("properties", {}).get("layers")
                or combined.get("mapunits")
                or combined.get("mapunit")
                or combined.get("Table")
                or combined.get("table")
            )
            # Also check for any non-meta keys
            if not has_data:
                has_data = any(
                    k not in ("_data_commons", "type", "geometry")
                    and v is not None
                    for k, v in combined.items()
                )
            if has_data:
                layer_info = ""
                layers = combined.get("properties", {}).get("layers", [])
                if layers:
                    names = [ly.get("name", "?") for ly in layers[:3]]
                    layer_info = f": {', '.join(names)}"
                points.append({
                    "lat": lat, "lon": lon,
                    "text": f"Soil data{layer_info}",
                    "size": 10,
                })

        if points:
            traces_by_cat[cat_id] = points
            total_points += len(points)

        # --- Data Commons data points (rendered as a secondary trace) ---
        dc_info = data.get("dc", {})
        if dc_info and dc_info.get("variables"):
            dc_place = dc_info.get("place_dcid", "")
            dc_type = dc_info.get("place_type", "")
            # We don't have per-variable coordinates from DC (it's aggregate
            # for a resolved place), but we show a summary pin at the user's
            # search location so they know DC data was loaded.
            var_summary_lines = []
            for label, vinfo in dc_info["variables"].items():
                val = vinfo.get("value")
                unit = vinfo.get("unit", "")
                date = vinfo.get("date", "")
                var_summary_lines.append(f"{label}: {val} {unit} ({date})")
            hover_text = (
                f"<b>Data Commons ({dc_type})</b><br>"
                f"Place: {dc_place}<br>"
                + "<br>".join(var_summary_lines[:6])
            )
            dc_key = f"dc_{cat_id}"
            traces_by_cat[dc_key] = [{
                "lat": lat,
                "lon": lon,
                "text": hover_text,
                "size": 14,
            }]
            total_points += 1

    # Build Plotly figure with OpenStreetMap tiles (no API key required)
    fig = go.Figure()

    # Per-category offsets to prevent point stacking at same location
    # Small angular offset (~300m at equator) per category index
    _OFFSETS = [
        (0.0, 0.0), (0.003, 0.002), (-0.003, 0.002),
        (0.002, -0.003), (-0.002, -0.003), (0.004, 0.0),
        (-0.004, 0.0), (0.0, 0.004), (0.003, -0.003),
        (-0.003, -0.003), (0.005, 0.003), (-0.005, 0.003),
    ]
    _cat_order = list(traces_by_cat.keys())

    for cat_idx, cat_id in enumerate(_cat_order):
        points = traces_by_cat[cat_id]
        dlat, dlon = _OFFSETS[cat_idx % len(_OFFSETS)]
        lats = [p["lat"] + dlat for p in points]
        lons = [p["lon"] + dlon for p in points]
        texts = [p["text"] for p in points]
        sizes = [p["size"] for p in points]

        is_dc = cat_id.startswith("dc_")
        if is_dc:
            # Gold diamond for Data Commons overlay pins
            base_cat = cat_id[3:]
            color = "#FFD700"
            cat_label = f"DC: {base_cat.replace('_', ' ').title()}"
            symbol = "diamond"
        else:
            color = cat_colors.get(cat_id, "#6C757D")
            cat_label = cat_id.replace("_", " ").title()
            symbol = "circle"

        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode="markers",
            marker=dict(size=sizes, color=color, opacity=0.85, symbol=symbol),
            text=texts,
            hoverinfo="text",
            name=cat_label,
        ))

    # If no data points, add an invisible center marker so the map still renders
    if not traces_by_cat:
        fig.add_trace(go.Scattermapbox(
            lat=[lat], lon=[lon], mode="markers",
            marker=dict(size=1, opacity=0),
            hoverinfo="skip", showlegend=False,
        ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=lat, lon=lon),
            zoom=4 if total_points > 5 else 8,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#ddd", borderwidth=1,
            font=dict(size=11),
        ),
    )

    map_component = dcc.Graph(
        id="env-dashboard-map",
        figure=fig,
        config={"displayModeBar": True, "scrollZoom": True},
        style={"borderRadius": "8px", "overflow": "hidden"},
    )

    count_text = f"{total_points} data points" if total_points > 0 else "No data loaded"
    _map_ms = int((time.time() - _map_t0) * 1000)

    # Per-category detail lines for the progress entry
    _map_details = []
    for cat_id in categories_data:
        if cat_id.startswith("dc_"):
            continue
        pts = traces_by_cat.get(cat_id, [])
        _map_details.append(f"{cat_id}: {len(pts)} points on map")

    _map_prog = make_entry(
        "complete" if total_points > 0 else "error",
        f"Map rendered: {count_text} across {len([k for k in traces_by_cat if not k.startswith('dc_')])} categories",
        duration_ms=_map_ms,
        details=_map_details,
    )
    return map_component, count_text, _map_prog


# ==================== CATEGORY GRAPHS CALLBACK ====================

@callback(
    [Output("category-graphs-container", "children"),
     Output("progress-dash-graphs", "data")],
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_category_graphs(loaded_data):
    """Generate individualized graphs for each selected category."""
    _g_t0 = time.time()
    _graph_progress: List[Dict[str, Any]] = []
    if not loaded_data:
        _graph_progress.append(make_entry("info", "Graphs: awaiting data"))
        return html.P(
            "Select categories in the sidebar to view data visualizations.", 
            className="text-muted text-center py-4"
        ), _graph_progress
    
    categories_data = loaded_data.get("categories", {})
    
    if not categories_data:
        _graph_progress.append(make_entry("warning", "Graphs: no categories selected"))
        return html.P(
            "No categories selected. Check the sidebar to enable data sources.", 
            className="text-muted text-center py-4"
        ), _graph_progress
    
    _graph_progress.append(make_entry("info", f"Rendering graphs for {len(categories_data)} categories"))
    graph_cards = []
    location = loaded_data.get("location", {})
    base_lat = location.get("lat", 37.7749)
    base_lon = location.get("lon", -122.4194)
    _rendered = 0
    _skipped = 0
    _errored = 0
    
    for cat_id, data in categories_data.items():
        cat_info = next((c for c in DATA_CATEGORIES if c["id"] == cat_id), None)
        if not cat_info:
            continue

        _cat_label = f"{cat_info['icon']} {cat_info['name']}"
        api_url = f"{API_BASE_URL}/api/v1/hub/category/{cat_id}?lat={base_lat}&lon={base_lon}"

        if data is None or (isinstance(data, dict) and "error" in data):
            error_msg = data.get("error", "Unknown error") if isinstance(data, dict) else "No data"
            _errored += 1
            _graph_progress.append(make_entry("error", f"{_cat_label}: {str(error_msg)[:60]}"))
            graph_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(f"{cat_info['icon']} {cat_info['name']}"),
                        dbc.CardBody([
                            dbc.Alert(f"Error loading data: {str(error_msg)[:80]}", color="warning"),
                            html.A("View raw API data ->", href=api_url,
                                   target="_blank", className="btn btn-outline-secondary btn-sm")
                        ])
                    ], style={"opacity": "0.5"})
                ], lg=6, className="mb-3")
            )
            continue

        # Check if category has actual content
        if _is_category_empty(data):
            _skipped += 1
            _graph_progress.append(make_entry("warning", f"{_cat_label}: no data at location"))
            graph_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(f"{cat_info['icon']} {cat_info['name']}"),
                        dbc.CardBody([
                            html.P(
                                f"No {cat_info['name'].lower()} data available for this location.",
                                className="text-muted text-center py-3 mb-0"
                            )
                        ])
                    ], style={"opacity": "0.5"})
                ], lg=6, className="mb-3")
            )
            continue

        payload = data.get("combined", data) if isinstance(data, dict) else data
        dc_payload = data.get("dc") if isinstance(data, dict) else None
        active_time_range = loaded_data.get("time_range", "7D")

        cat_info = next((c for c in DATA_CATEGORIES if c["id"] == cat_id), None)
        if not cat_info:
            continue

        try:
            _gt0 = time.time()
            fig = get_graph_for_category(cat_id, payload, dc_data=dc_payload, time_range=active_time_range)
            _gt_ms = int((time.time() - _gt0) * 1000)
            _rendered += 1
            _graph_progress.append(make_entry(
                "complete", f"{_cat_label}: graph rendered", duration_ms=_gt_ms,
            ))
            
            graph_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Span(
                                f"{cat_info['icon']} {cat_info['name']}",
                                className="fw-bold"
                            ),
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=fig, config={"displayModeBar": False}),
                            html.A("View raw API data ->", href=api_url,
                                   target="_blank", className="small text-muted")
                        ])
                    ], className="h-100")
                ], lg=6, className="mb-3")
            )
        except Exception as e:
            _errored += 1
            _graph_progress.append(make_entry("error", f"{_cat_label}: {str(e)[:60]}"))
            graph_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(f"{cat_info['icon']} {cat_info['name']}"),
                        dbc.CardBody([
                            dbc.Alert(f"Error: {str(e)[:80]}", color="warning"),
                            html.A("View raw API data ->", href=api_url,
                                   target="_blank", className="btn btn-outline-secondary btn-sm")
                        ])
                    ])
                ], lg=6, className="mb-3")
            )
    
    _g_total_ms = int((time.time() - _g_t0) * 1000)
    _graph_progress.append(make_entry(
        "complete" if _rendered > 0 else "warning",
        f"Graphs: {_rendered} rendered, {_skipped} empty, {_errored} errors",
        duration_ms=_g_total_ms,
    ))

    if not graph_cards:
        return html.P(
            "No data available for selected categories.", 
            className="text-muted text-center py-4"
        ), _graph_progress
    
    return dbc.Row(graph_cards), _graph_progress


# ==================== INTERSECTION GRAPH CALLBACK ====================

@callback(
    Output("intersection-graph-container", "children"),
    Input("loaded-category-data", "data"),
    prevent_initial_call=False
)
def update_intersection_graph(loaded_data):
    """Cross-domain intersection graph - hidden for now (not meaningful enough)."""
    return html.Div()


# ==================== STATS AND STATUS CALLBACKS ====================

@callback(
    [Output("dashboard-stats-row", "children"),
     Output("progress-dash-stats", "data")],
    [Input("reload-all-data-btn", "n_clicks"),
     Input("loaded-category-data", "data")],
    prevent_initial_call=False
)
def update_dashboard_stats(n_clicks, loaded_data):
    """Update the dashboard statistics cards."""
    _st0 = time.time()
    try:
        hub_info = get_hub_info()
        
        data_points = 0
        dc_variables_count = 0
        if loaded_data:
            for cat_data in loaded_data.get("categories", {}).values():
                if isinstance(cat_data, dict):
                    combined = cat_data.get("combined", {})
                    data_points += len(combined.get("features", []))
                    data_points += len(combined.get("incidents", []))
                    data_points += len(combined.get("measurements", []))
                    data_points += len(combined.get("results", []))
                    data_points += len(combined.get("stations", []))
                    # Count DC variables
                    dc = cat_data.get("dc", {})
                    dc_variables_count += len(dc.get("variables", {}))
        
        total_display = str(data_points)
        if dc_variables_count > 0:
            total_display = f"{data_points} + {dc_variables_count} DC"
        
        stats = {
            "total_sources": hub_info.get("total_sources", 24),
            "active_alerts": 0,
            "data_points": total_display,
            "last_update": datetime.now().strftime("%H:%M:%S")
        }
        
        return create_stats_cards(stats), make_entry(
            "complete",
            f"Stats: {stats['total_sources']} sources, {stats['data_points']} data points",
            duration_ms=int((time.time() - _st0) * 1000),
        )
    except Exception as e:
        return create_stats_cards({
            "total_sources": "Error",
            "active_alerts": "Error",
            "data_points": "Error",
            "last_update": str(e)[:20]
        }), make_entry("error", f"Stats failed: {str(e)[:50]}")


@callback(
    [Output("quick-check-status", "children"),
     Output("aqi-gauge-container", "children"),
     Output("weather-summary-container", "children"),
     Output("loading-indicator", "children"),
     Output("progress-dash-qc", "data")],
    [Input("quick-check-btn", "n_clicks"),
     Input("location-updated-trigger", "data"),
     Input("initial-load-trigger", "n_intervals")],
    [State("quick-check-lat", "value"),
     State("quick-check-lon", "value"),
     State("latitude-input", "value"),
     State("longitude-input", "value")],
    prevent_initial_call=False
)
def update_quick_check(
    quick_clicks, location_trigger, n_intervals, 
    quick_lat, quick_lon, sidebar_lat, sidebar_lon
):
    """Update quick check results when location changes or on initial load."""
    triggered = ctx.triggered_id
    
    if triggered == "location-updated-trigger" and location_trigger:
        lat = location_trigger.get("lat", 37.7749)
        lon = location_trigger.get("lon", -122.4194)
    else:
        lat = quick_lat or 37.7749
        lon = quick_lon or -122.4194
    
    try:
        _qc0 = time.time()
        result = quick_check(lat, lon)
        
        status_map = {
            "normal": ("Normal Conditions", "success"),
            "alert": ("Alert - Check Details", "danger"),
            "caution": ("Caution - Minor Issues", "warning"),
            "partial_data": ("Partial Data Available", "info"),
            "unknown": ("Status Unknown", "secondary")
        }
        overall_status = result.get("overall_status", "unknown")
        status_text, status_color = status_map.get(overall_status, ("Unknown", "secondary"))
        status_badge = dbc.Alert(status_text, color=status_color, className="mb-0 py-2")
        
        air_quality = result.get("air_quality", {})
        aqi_value = air_quality.get("us_aqi", 0) if air_quality else 0
        aqi_status = air_quality.get("status", "Unknown") if air_quality else "Unknown"
        aqi_label = aqi_status.replace("_", " ").title()
        aqi_gauge = dcc.Graph(
            figure=create_aqi_gauge(aqi_value, f"Air Quality Index\n{aqi_label}"),
            config={"displayModeBar": False}
        )
        
        weather = result.get("weather", {})
        temp = weather.get("temperature_c", "N/A")
        wind = weather.get("wind_speed_kmh", "N/A")
        weather_status = weather.get("status", "unknown")
        
        # Determine if weather data is actually present
        has_weather = (temp not in ("N/A", None, 0, "") and wind not in ("N/A", None, ""))

        weather_summary = html.Div([
            html.H6("Weather"),
            html.P([html.Strong("Temperature: "), f"{temp}\u00b0C" if has_weather else "No data"]),
            html.P([html.Strong("Wind: "), f"{wind} km/h" if has_weather else "No data"]),
            html.P([html.Strong("Conditions: "), weather_status.replace("_", " ").title() if has_weather else "Unavailable"])
        ]) if has_weather else html.Div([
            html.H6("Weather"),
            dbc.Alert("No weather data available for this location", color="secondary", className="py-1 mb-0")
        ])
        
        loading_text = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
        
        # Validation: red X if both AQI=0 and weather missing
        has_aqi = aqi_value is not None and aqi_value > 0
        _qc_ms = int((time.time() - _qc0) * 1000)

        if has_aqi and has_weather:
            _qc_status = "complete"
            _qc_msg = f"Quick check: AQI {aqi_value} ({aqi_label}), {temp}\u00b0C"
        elif has_aqi:
            _qc_status = "warning"
            _qc_msg = f"Quick check: AQI {aqi_value} ({aqi_label}), weather N/A"
        elif has_weather:
            _qc_status = "warning"
            _qc_msg = f"Quick check: AQI unavailable, {temp}\u00b0C"
        else:
            _qc_status = "error"
            _qc_msg = "Quick check: No AQI or weather data at this location"

        _qc_prog = make_entry(_qc_status, _qc_msg, duration_ms=_qc_ms)
        
        return status_badge, aqi_gauge, weather_summary, loading_text, _qc_prog
        
    except Exception as e:
        error_alert = dbc.Alert(f"Error: {str(e)[:50]}", color="danger", className="mb-0 py-2")
        return (
            error_alert, 
            html.P("Unable to load AQI"), 
            html.P("Unable to load weather"), 
            "Error loading data",
            make_entry("error", f"Quick check failed: {str(e)[:50]}"),
        )


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
        
        loaded_cats = set(loaded_data.get("categories", {}).keys()) if loaded_data else set()
        
        badges = []
        for cat in DATA_CATEGORIES:
            cat_id = cat["id"]
            cat_sources = sources_by_cat.get(cat_id, [])
            count = len(cat_sources) if isinstance(cat_sources, list) else 0
            
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


# ==================== HELPER: CHECK EMPTY CATEGORY ====================

def _count_records(cat_id: str, combined: Dict[str, Any]) -> int:
    """Count actual data records from raw combined data for a category.

    Returns the number of primary data records (features, incidents,
    measurements, results, etc.) so we can compare source vs widget.
    """
    if not combined or not isinstance(combined, dict):
        return 0

    if cat_id == "air_quality":
        # OpenAQ results, legacy measurements, or hourly array
        n = len(combined.get("results", []))
        if not n:
            n = len(combined.get("measurements", []))
        if not n:
            hourly = combined.get("hourly", {})
            if isinstance(hourly, dict):
                for k in ("us_aqi", "european_aqi", "pm2_5", "pm10"):
                    vals = hourly.get(k, [])
                    if vals:
                        n = len([v for v in vals if v is not None])
                        break
        # Fallback: direct AQI value counts as 1
        if not n:
            for k in ("us_aqi", "european_aqi", "aqi", "aqi_value"):
                if combined.get(k) is not None:
                    n = 1
                    break
        return n

    if cat_id == "weather":
        hourly = combined.get("hourly", {})
        if isinstance(hourly, dict) and hourly.get("time"):
            return len(hourly["time"])
        if combined.get("current_weather"):
            return 1
        return 0

    if cat_id == "earthquakes":
        return len(combined.get("features", []))

    if cat_id == "wildfires":
        n = len(combined.get("incidents", []))
        if not n:
            n = len(combined.get("features", []))
        return n

    if cat_id == "water":
        ts = combined.get("value", {}).get("timeSeries", [])
        return len(ts) if isinstance(ts, list) else 0

    if cat_id == "marine":
        n = len(combined.get("stations", []))
        if not n:
            n = len(combined.get("observations", []))
        if not n:
            n = len(combined.get("predictions", {}).get("predictions", []))
        return n

    if cat_id == "radiation":
        return len(combined.get("measurements", []))

    if cat_id == "climate":
        daily = combined.get("daily", {})
        if isinstance(daily, dict) and daily.get("time"):
            return len(daily["time"])
        return 0

    if cat_id == "soil":
        layers = combined.get("properties", {}).get("layers", [])
        if layers:
            return len(layers)
        if combined.get("mapunits") or combined.get("mapunit"):
            return 1
        if combined.get("Table") or combined.get("table"):
            return 1
        return 0

    if cat_id == "biodiversity":
        return len(combined.get("results", []))

    return 0


def _summarize_for_log(cat_id: str, summary: Dict[str, Any],
                       record_count: int = 0) -> str:
    """One-line human-readable summary with record count for the activity log."""
    rc_tag = f" [{record_count} rec]" if record_count > 0 else " [0 rec]"

    if cat_id == "air_quality":
        aqi = summary.get("us_aqi", summary.get("aqi", summary.get("aqi_value")))
        pm = summary.get("pm25", summary.get("pm2_5"))
        parts = []
        if aqi is not None:
            parts.append(f"AQI {aqi}")
        if pm is not None:
            parts.append(f"PM2.5 {pm}")
        return (", ".join(parts) if parts else "Data loaded") + rc_tag
    if cat_id == "weather":
        temp = summary.get("temperature_c", summary.get("temperature"))
        wind = summary.get("wind_speed_kmh", summary.get("windspeed"))
        parts = []
        if temp is not None:
            parts.append(f"{temp}\u00b0C")
        if wind is not None:
            parts.append(f"wind {wind}km/h")
        return (", ".join(parts) if parts else "Data loaded") + rc_tag
    if cat_id == "earthquakes":
        return f"{record_count} events" + rc_tag
    if cat_id == "wildfires":
        return f"{record_count} incidents" + rc_tag
    if cat_id == "water":
        return f"{record_count} stations" + rc_tag
    if cat_id == "marine":
        return f"{record_count} observations" + rc_tag
    if cat_id == "radiation":
        val = summary.get("value", summary.get("avg_value"))
        label = f"{val} cpm" if val is not None else "Data loaded"
        return label + rc_tag
    if cat_id == "climate":
        avg = summary.get("avg_temp", summary.get("temperature"))
        label = f"Avg {avg}\u00b0C" if avg is not None else "Data loaded"
        return label + rc_tag
    if cat_id == "soil":
        return f"{record_count} layers" + rc_tag
    if cat_id == "biodiversity":
        return f"{record_count} species" + rc_tag
    # Generic fallback
    parts = [f"{k}: {v}" for k, v in list(summary.items())[:2] if v]
    return (", ".join(parts) if parts else "Data loaded") + rc_tag


def _is_category_empty(cat_data: Dict[str, Any]) -> bool:
    """Check if a category's loaded data is effectively empty."""
    if not cat_data or not isinstance(cat_data, dict):
        return True
    if "error" in cat_data:
        return True
    combined = cat_data.get("combined", {})
    if not combined:
        return True
    # Check for actual data content
    data_keys = [
        "features", "incidents", "measurements", "results",
        "stations", "observations", "current_weather", "hourly",
        "daily", "value", "properties", "mapunits", "Table",
        "fires", "count", "data", "records",
    ]
    for key in data_keys:
        val = combined.get(key)
        if val:
            if isinstance(val, (list, dict)) and len(val) > 0:
                return False
            elif val:
                return False
    # Check if there are any non-meta keys with values
    meta_keys = {"_data_commons", "type", "geometry", "latitude", "longitude",
                 "utc_offset_seconds", "timezone", "timezone_abbreviation",
                 "generationtime_ms", "elevation"}
    for k, v in combined.items():
        if k not in meta_keys and v is not None:
            if isinstance(v, (list, dict)) and len(v) > 0:
                return False
            elif not isinstance(v, (list, dict)):
                return False
    return True


# ==================== CATEGORY AVAILABILITY CALLBACK ====================

@callback(
    Output("category-checklist", "options"),
    Input("loaded-category-data", "data"),
    prevent_initial_call=True
)
def update_category_availability(loaded_data):
    """Disable/grey out categories that have no data for the current location."""
    null_cats = set()
    if loaded_data:
        for cat_id, data in loaded_data.get("categories", {}).items():
            if _is_category_empty(data):
                null_cats.add(cat_id)

    options = []
    for cat in DATA_CATEGORIES:
        opt = {"label": f"{cat['icon']} {cat['name']}", "value": cat["id"]}
        if cat["id"] in null_cats:
            opt["disabled"] = True
            opt["label"] = f"{cat['icon']} {cat['name']} (No data)"
        options.append(opt)

    return options


# ==================== PROGRESS BOX CALLBACKS ====================

@callback(
    Output("progress-entries-dash", "children"),
    [Input("progress-dash-qc", "data"),
     Input("progress-dash-cats", "data"),
     Input("progress-dash-graphs", "data"),
     Input("progress-dash-map", "data"),
     Input("progress-dash-stats", "data")],
    prevent_initial_call=False,
)
def render_dash_progress(qc, cats, graphs, map_prog, stats):
    """Combine all task progress stores into a single rendered activity log."""
    entries: List[Dict[str, Any]] = []

    # ── Quick Check ──
    if qc:
        entries.append(qc) if isinstance(qc, dict) else entries.extend(qc)
    else:
        entries.append(make_entry("loading", "Loading quick check (AQI + Weather)..."))

    # ── Category data fetch ──
    if cats:
        if isinstance(cats, list):
            entries.extend(cats)
        else:
            entries.append(cats)
    else:
        entries.append(make_entry("loading", "Loading 10 data categories..."))

    # ── Graph rendering ──
    if graphs:
        if isinstance(graphs, list):
            entries.extend(graphs)
        else:
            entries.append(graphs)
    else:
        entries.append(make_entry("loading", "Rendering category graphs..."))

    # ── Map ──
    if map_prog:
        entries.append(map_prog) if isinstance(map_prog, dict) else entries.extend(map_prog)
    else:
        entries.append(make_entry("loading", "Rendering environmental data map..."))

    # ── Stats ──
    if stats:
        entries.append(stats) if isinstance(stats, dict) else entries.extend(stats)
    else:
        entries.append(make_entry("loading", "Computing dashboard statistics..."))

    # ── Completion banner ──
    all_done = all(x is not None for x in [qc, cats, graphs, map_prog, stats])
    if all_done:
        entries.append(make_entry("separator", ""))
        entries.append(make_entry("success", "All tasks complete -- Dashboard fully loaded"))

    return render_entries(entries)


@callback(
    [Output("progress-body-dash", "is_open"),
     Output("progress-icon-dash", "className")],
    Input("progress-toggle-dash", "n_clicks"),
    State("progress-body-dash", "is_open"),
    prevent_initial_call=True,
)
def toggle_dash_progress(n, is_open):
    """Toggle the progress box open/closed."""
    new_state = not is_open
    icon = "fas fa-chevron-up" if new_state else "fas fa-chevron-down"
    return new_state, icon