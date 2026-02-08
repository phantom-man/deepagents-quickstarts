"""
Data-Specific Graph Components for Environmental Monitoring Dashboard.

Best Practices for Environmental Data Visualization:
- Air Quality: AQI gauges, pollutant bar charts, time series trends
- Earthquakes: Magnitude scatter/bubble plots, depth vs magnitude, timeline
- Wildfires: Incident counts, containment status pie, geographic heat maps
- Radiation: CPM readings over time, geographic distribution
- Weather: Temperature/humidity trends, wind roses, precipitation bars
- Marine: Wave height/period, buoy status, SST trends
- Water: Quality indices, contaminant levels, flow rates
- Soil: Moisture content, temperature profiles, nutrient levels
- Climate: Long-term trends, anomalies, seasonal patterns
- Biodiversity: Species counts, observation maps, temporal patterns
"""
from datetime import datetime
from typing import Any, Dict, Optional

import plotly.graph_objects as go


def create_air_quality_graph(data: Dict[str, Any]) -> go.Figure:
    """Create air quality visualization with pollutant breakdown."""
    fig = go.Figure()
    
    # Handle API response structure - data might have 'current' nested object
    current = data.get("current", data)
    
    # Get pollutant data - try both snake_case and direct keys
    pollutants = {
        "PM2.5": current.get("pm2_5", current.get("pm25", 0)),
        "PM10": current.get("pm10", 0),
        "O3": current.get("ozone", current.get("o3", 0)),
        "NO2": current.get("nitrogen_dioxide", current.get("no2", 0)),
        "SO2": current.get("sulphur_dioxide", current.get("so2", 0)),
        "CO": current.get("carbon_monoxide", current.get("co", 0))
    }
    
    # Normalize CO (usually in μg/m³ x100 range) for visualization
    if pollutants["CO"] and pollutants["CO"] > 100:
        pollutants["CO"] = pollutants["CO"] / 10  # Scale down for chart
    
    # Filter out zero values
    pollutants = {k: v for k, v in pollutants.items() if v and v > 0}
    
    if pollutants:
        colors = ["#e74c3c", "#9b59b6", "#3498db", "#2ecc71", "#f1c40f", "#e67e22"]
        fig.add_trace(go.Bar(
            x=list(pollutants.keys()),
            y=list(pollutants.values()),
            marker_color=colors[:len(pollutants)],
            text=[f"{v:.1f}" for v in pollutants.values()],
            textposition='outside'
        ))
        
        # Get AQI value for title
        aqi = current.get("us_aqi", current.get("aqi", 0))
        aqi_text = f" (AQI: {aqi})" if aqi else ""
        
        fig.update_layout(
            title=f"Current Pollutant Levels{aqi_text}",
            xaxis_title="Pollutant",
            yaxis_title="Concentration (µg/m³)",
            showlegend=False
        )
    else:
        fig.add_annotation(
            text="No pollutant data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        height=300
    )
    
    return fig


def create_earthquake_graph(data: Dict[str, Any]) -> go.Figure:
    """Create earthquake visualization - magnitude distribution and timeline."""
    fig = go.Figure()
    
    features = data.get("features", [])
    
    if features:
        magnitudes = []
        depths = []
        times = []
        places = []
        
        for f in features:
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [0, 0, 0])
            
            mag = props.get("mag", 0)
            if mag:
                magnitudes.append(mag)
                depths.append(coords[2] if len(coords) > 2 else 0)
                times.append(datetime.fromtimestamp(props.get("time", 0) / 1000))
                places.append(props.get("place", "Unknown"))
        
        if magnitudes:
            # Magnitude vs Depth scatter
            fig.add_trace(go.Scatter(
                x=magnitudes,
                y=depths,
                mode='markers',
                marker=dict(
                    size=[max(5, m * 5) for m in magnitudes],
                    color=magnitudes,
                    colorscale='YlOrRd',
                    showscale=True,
                    colorbar=dict(title="Mag")
                ),
                text=places,
                hovertemplate="Mag: %{x}<br>Depth: %{y} km<br>%{text}<extra></extra>",
                name="Earthquakes"
            ))
            
            fig.update_layout(
                title=f"Recent Earthquakes ({len(magnitudes)} events)",
                xaxis_title="Magnitude",
                yaxis_title="Depth (km)",
                yaxis=dict(autorange="reversed")  # Deeper earthquakes at bottom
            )
    else:
        fig.add_annotation(
            text="No earthquake data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig


def create_wildfire_graph(data: Dict[str, Any]) -> go.Figure:
    """Create wildfire visualization - incident counts and containment."""
    fig = go.Figure()
    
    incidents = data.get("incidents", [])
    
    if incidents:
        # Group by source/type
        contained = sum(1 for i in incidents if i.get("containment", 0) == 100)
        active = len(incidents) - contained
        
        fig.add_trace(go.Pie(
            labels=["Active", "Contained"],
            values=[active, contained],
            marker_colors=["#e74c3c", "#2ecc71"],
            textinfo='label+value',
            hole=0.4
        ))
        
        fig.update_layout(
            title=f"Wildfire Status ({len(incidents)} incidents)",
            annotations=[dict(text=f"{len(incidents)}", x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
    else:
        fig.add_annotation(
            text="No wildfire data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig


def create_radiation_graph(data: Dict[str, Any]) -> go.Figure:
    """Create radiation visualization - measurements distribution."""
    fig = go.Figure()
    
    measurements = data.get("measurements", [])
    
    if measurements:
        values = [m.get("value", 0) for m in measurements if m.get("value")]
        
        if values:
            fig.add_trace(go.Histogram(
                x=values,
                nbinsx=20,
                marker_color="#9b59b6",
                name="Readings"
            ))
            
            # Add average line
            avg_val = sum(values) / len(values)
            fig.add_vline(x=avg_val, line_dash="dash", line_color="red",
                         annotation_text=f"Avg: {avg_val:.1f}")
            
            fig.update_layout(
                title=f"Radiation Readings Distribution ({len(values)} measurements)",
                xaxis_title="CPM (counts per minute)",
                yaxis_title="Frequency"
            )
    else:
        fig.add_annotation(
            text="No radiation data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig


def create_weather_graph(data: Dict[str, Any]) -> go.Figure:
    """Create weather visualization - conditions summary."""
    fig = go.Figure()
    
    # Handle nested 'current' structure from Open-Meteo API
    current = data.get("current", data)
    
    # Extract values with multiple possible key names
    temp = current.get("temperature_2m", current.get("temperature_c", current.get("temperature", 0)))
    humidity = current.get("relative_humidity_2m", current.get("humidity", current.get("relative_humidity", 0)))
    wind = current.get("wind_speed_10m", current.get("wind_speed_kmh", current.get("wind_speed", 0)))
    pressure = current.get("pressure_msl", current.get("pressure_hpa", current.get("pressure", 0)))
    precipitation = current.get("precipitation", 0)
    
    # Check if we have hourly forecast data
    hourly = data.get("hourly", {})
    if hourly and hourly.get("time") and hourly.get("temperature_2m"):
        # Create temperature forecast line chart
        times = hourly.get("time", [])[:24]  # Next 24 hours
        temps = hourly.get("temperature_2m", [])[:24]
        precip_prob = hourly.get("precipitation_probability", [])[:24]
        
        fig.add_trace(go.Scatter(
            x=times, y=temps,
            mode='lines+markers',
            name='Temperature (°C)',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=4)
        ))
        
        if precip_prob:
            fig.add_trace(go.Bar(
                x=times, y=precip_prob,
                name='Rain Probability (%)',
                marker_color='rgba(52, 152, 219, 0.5)',
                yaxis='y2'
            ))
        
        fig.update_layout(
            title=f"24-Hour Forecast (Current: {temp:.1f}°C, {humidity}% humidity)",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            yaxis2=dict(
                title="Rain Probability (%)",
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
    elif temp or humidity or wind:
        # Fallback to radar chart for current conditions only
        categories = ["Temperature", "Humidity", "Wind Speed", "Pressure"]
        values = [temp, humidity, wind, pressure / 10 if pressure > 100 else pressure]
        
        max_vals = [50, 100, 100, 110]
        normalized = [min(100, (v / m) * 100) if m > 0 else 0 for v, m in zip(values, max_vals)]
        
        fig.add_trace(go.Scatterpolar(
            r=normalized,
            theta=categories,
            fill='toself',
            name='Current',
            marker_color='#3498db'
        ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=f"Weather: {temp:.1f}°C, {humidity}% humidity, {wind:.1f} km/h wind",
            showlegend=False
        )
    else:
        fig.add_annotation(
            text="No weather data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig


def create_marine_graph(data: Dict[str, Any]) -> go.Figure:
    """Create marine visualization from NOAA NDBC observations."""
    import re
    fig = go.Figure()
    
    # Handle NOAA NDBC observations format
    observations = data.get("observations", [])
    stations = data.get("stations", [])
    
    if observations:
        wind_data = []  # [(station_name, wind_speed)]
        wave_data = []  # [(station_name, wave_height)]
        
        for obs in observations[:12]:  # Limit to 12 stations
            station = obs.get("station", "Unknown")
            # Clean station name
            station_clean = station.split(" - ")[-1][:25] if " - " in station else station[:25]
            conditions = obs.get("conditions", "")
            
            # Parse wind speed and wave height from HTML content
            wind_match = re.search(r'Wind Speed:</b>\s*(\d+)\s*knots', conditions)
            wave_match = re.search(r'Wave Height:</b>\s*(\d+)\s*ft', conditions)
            
            if wind_match:
                wind_data.append((station_clean, int(wind_match.group(1))))
            if wave_match:
                wave_data.append((station_clean, int(wave_match.group(1))))
        
        # Display wind data if available
        if wind_data:
            station_names = [d[0] for d in wind_data]
            wind_speeds = [d[1] for d in wind_data]
            fig.add_trace(go.Bar(
                x=station_names,
                y=wind_speeds,
                marker_color='#3498db',
                text=[f"{s} kts" for s in wind_speeds],
                textposition='outside',
                name='Wind Speed'
            ))
            fig.update_layout(
                title=f"Wind Speeds ({len(wind_speeds)} stations)",
                xaxis_title="Station",
                yaxis_title="Wind Speed (knots)",
                xaxis_tickangle=45
            )
        # Fall back to wave data if no wind data
        elif wave_data:
            station_names = [d[0] for d in wave_data]
            wave_heights = [d[1] for d in wave_data]
            fig.add_trace(go.Bar(
                x=station_names,
                y=wave_heights,
                marker_color='#2ecc71',
                text=[f"{h} ft" for h in wave_heights],
                textposition='outside',
                name='Wave Height'
            ))
            fig.update_layout(
                title=f"Wave Heights ({len(wave_heights)} readings)",
                xaxis_title="Station",
                yaxis_title="Wave Height (ft)",
                xaxis_tickangle=45
            )
        else:
            # No parseable data in observations - show raw count
            fig.add_annotation(
                text=f"Marine data: {len(observations)} observations (unparseable)",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    elif stations:
        # Fallback to old format
        wave_heights = []
        station_names = []
        for s in stations[:10]:
            obs = s.get("latest_observation", {})
            wh = obs.get("wave_height", obs.get("WVHT"))
            if wh:
                wave_heights.append(float(wh))
                station_names.append(s.get("name", s.get("station_id", "Unknown"))[:20])
        if wave_heights:
            fig.add_trace(go.Bar(x=station_names, y=wave_heights, marker_color='#3498db'))
            fig.update_layout(title="Wave Heights", xaxis_title="Station", yaxis_title="Height (m)")
    else:
        fig.add_annotation(
            text="No marine data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=80), height=300)
    return fig


def create_water_graph(data: Dict[str, Any]) -> go.Figure:
    """Create water quality visualization from USGS stream data."""
    fig = go.Figure()
    
    # Try to extract USGS time series data
    time_series = data.get("value", {}).get("timeSeries", [])
    
    if time_series:
        # Group by variable type (streamflow, gage height)
        streamflow_sites = []
        gage_height_sites = []
        
        for ts in time_series[:20]:  # Limit to first 20 for performance
            site_info = ts.get("sourceInfo", {})
            site_name = site_info.get("siteName", "Unknown")[:30]  # Truncate
            variable = ts.get("variable", {})
            var_name = variable.get("variableName", "")
            
            values_list = ts.get("values", [{}])[0].get("value", [])
            if values_list:
                value = values_list[0].get("value", "0")
                try:
                    val = float(value)
                    if val > -999990:  # Filter out no-data values
                        if "Streamflow" in var_name:
                            streamflow_sites.append((site_name, val))
                        elif "Gage height" in var_name:
                            gage_height_sites.append((site_name, val))
                except (ValueError, TypeError):
                    pass
        
        if streamflow_sites:
            # Show top 8 streamflow sites
            streamflow_sites.sort(key=lambda x: x[1], reverse=True)
            top_sites = streamflow_sites[:8]
            
            fig.add_trace(go.Bar(
                x=[s[0] for s in top_sites],
                y=[s[1] for s in top_sites],
                marker_color='#3498db',
                text=[f"{s[1]:.0f}" for s in top_sites],
                textposition='outside',
                name='Streamflow (ft³/s)'
            ))
            
            fig.update_layout(
                title=f"Stream Flow Rates ({len(streamflow_sites)} sites)",
                xaxis_title="Monitoring Site",
                yaxis_title="Discharge (ft³/s)",
                xaxis_tickangle=45
            )
        elif gage_height_sites:
            gage_height_sites.sort(key=lambda x: x[1], reverse=True)
            top_sites = gage_height_sites[:8]
            
            fig.add_trace(go.Bar(
                x=[s[0] for s in top_sites],
                y=[s[1] for s in top_sites],
                marker_color='#2ecc71',
                text=[f"{s[1]:.1f}" for s in top_sites],
                textposition='outside',
                name='Gage Height (ft)'
            ))
            
            fig.update_layout(
                title=f"Water Levels ({len(gage_height_sites)} sites)",
                xaxis_title="Monitoring Site",
                yaxis_title="Gage Height (ft)",
                xaxis_tickangle=45
            )
        else:
            fig.add_annotation(
                text="No water data available for this location",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    else:
        # Fallback: check for simple quality metrics
        quality = data.get("quality", data.get("results", {}))
        if isinstance(quality, dict) and quality:
            metrics = ["pH", "Turbidity", "DO", "Conductivity"]
            values = [
                quality.get("ph", quality.get("pH", 7)),
                quality.get("turbidity", 0),
                quality.get("dissolved_oxygen", quality.get("DO", 0)),
                quality.get("conductivity", 0) / 100
            ]
            fig.add_trace(go.Bar(x=metrics, y=values, marker_color=["#9b59b6", "#e67e22", "#3498db", "#2ecc71"]))
            fig.update_layout(title="Water Quality Metrics", xaxis_title="Metric", yaxis_title="Value")
        else:
            fig.add_annotation(
                text="No water data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=80), height=300)
    return fig


def create_soil_graph(data: Dict[str, Any]) -> go.Figure:
    """Create soil data visualization from USDA Soil Data Access."""
    fig = go.Figure()
    
    # Try USDA soil_data.Table format first
    soil_data = data.get("soil_data", {})
    table = soil_data.get("Table", [])
    
    if table and len(table) > 1:
        # First row is headers, rest are data
        headers = table[0] if table else []
        
        # Find indices for key soil properties
        try:
            sand_idx = headers.index("sandtotal_r") if "sandtotal_r" in headers else -1
            silt_idx = headers.index("silttotal_r") if "silttotal_r" in headers else -1
            clay_idx = headers.index("claytotal_r") if "claytotal_r" in headers else -1
            om_idx = headers.index("om_r") if "om_r" in headers else -1
            ph_idx = headers.index("ph1to1h2o_r") if "ph1to1h2o_r" in headers else -1
        except (ValueError, AttributeError):
            sand_idx = silt_idx = clay_idx = om_idx = ph_idx = -1
        
        # Aggregate values from data rows
        sand_vals, silt_vals, clay_vals, om_vals, ph_vals = [], [], [], [], []
        
        for row in table[1:]:
            if len(row) > max(sand_idx, silt_idx, clay_idx, om_idx, ph_idx):
                if sand_idx >= 0 and row[sand_idx]: 
                    try: sand_vals.append(float(row[sand_idx]))
                    except: pass
                if silt_idx >= 0 and row[silt_idx]:
                    try: silt_vals.append(float(row[silt_idx]))
                    except: pass
                if clay_idx >= 0 and row[clay_idx]:
                    try: clay_vals.append(float(row[clay_idx]))
                    except: pass
                if om_idx >= 0 and row[om_idx]:
                    try: om_vals.append(float(row[om_idx]))
                    except: pass
                if ph_idx >= 0 and row[ph_idx]:
                    try: ph_vals.append(float(row[ph_idx]))
                    except: pass
        
        # Calculate averages
        metrics = []
        values = []
        colors = []
        
        if sand_vals:
            metrics.append("Sand %")
            values.append(sum(sand_vals)/len(sand_vals))
            colors.append("#F4D03F")
        if silt_vals:
            metrics.append("Silt %")
            values.append(sum(silt_vals)/len(silt_vals))
            colors.append("#A9CCE3")
        if clay_vals:
            metrics.append("Clay %")
            values.append(sum(clay_vals)/len(clay_vals))
            colors.append("#D35400")
        if om_vals:
            metrics.append("Organic %")
            values.append(sum(om_vals)/len(om_vals))
            colors.append("#27AE60")
        if ph_vals:
            metrics.append("pH")
            values.append(sum(ph_vals)/len(ph_vals))
            colors.append("#8E44AD")
        
        if metrics:
            fig.add_trace(go.Bar(
                x=metrics,
                y=values,
                marker_color=colors,
                text=[f"{v:.1f}" for v in values],
                textposition='outside'
            ))
            
            fig.update_layout(
                title=f"Soil Composition ({len(table)-1} samples)",
                xaxis_title="Property",
                yaxis_title="Value"
            )
        else:
            # No numeric data extracted
            fig.add_annotation(
                text="Soil data available but contains no numeric values",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    else:
        # Fallback: try moisture format
        moisture = data.get("moisture", data.get("soil_moisture", []))
        
        if moisture:
            if isinstance(moisture, list):
                depths = [f"{i*10}cm" for i in range(len(moisture))]
                vals = moisture
            else:
                depths = ["Surface"]
                vals = [moisture]
            
            fig.add_trace(go.Bar(
                x=depths,
                y=vals,
                marker_color='#795548',
                text=[f"{v:.1f}%" for v in vals],
                textposition='outside'
            ))
            
            fig.update_layout(
                title="Soil Moisture by Depth",
                xaxis_title="Depth",
                yaxis_title="Moisture (%)"
            )
        else:
            fig.add_annotation(
                text="No soil data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig


def create_climate_graph(data: Dict[str, Any]) -> go.Figure:
    """Create climate data visualization from Open-Meteo historical/daily data."""
    fig = go.Figure()
    
    # Try to extract Open-Meteo daily data first (most common from climate endpoint)
    daily = data.get("daily", {})
    daily_temps = daily.get("temperature_2m_mean", daily.get("temperature_2m_max", []))
    daily_times = daily.get("time", [])
    
    if daily_temps and daily_times:
        # Use up to last 30 days
        temps = daily_temps[-30:]
        times = daily_times[-30:]
        
        # Color based on temperature
        colors = ['#e74c3c' if t and t > 20 else '#3498db' if t and t < 10 else '#f39c12' 
                  for t in temps]
        
        fig.add_trace(go.Scatter(
            x=times,
            y=temps,
            mode='lines+markers',
            marker=dict(color=colors, size=6),
            line=dict(color='#7f8c8d', width=2),
            name='Daily Mean Temp'
        ))
        
        # Add average line
        valid_temps = [t for t in temps if t is not None]
        if valid_temps:
            avg_temp = sum(valid_temps) / len(valid_temps)
            fig.add_hline(y=avg_temp, line_dash="dash", line_color="orange",
                         annotation_text=f"Avg: {avg_temp:.1f}°C")
        
        fig.update_layout(
            title=f"Climate: Temperature Trend ({len(temps)} Days)",
            xaxis_title="Date",
            yaxis_title="Temperature (°C)",
            xaxis_tickangle=45
        )
    else:
        # Fallback: try hourly data
        hourly = data.get("hourly", {})
        temperatures = hourly.get("temperature_2m", [])
        time_data = hourly.get("time", [])
        
        if temperatures and time_data:
            # Sample last 168 hours (7 days)
            sample_size = min(168, len(temperatures))
            temps = temperatures[-sample_size:]
            times = time_data[-sample_size:]
            
            fig.add_trace(go.Scatter(
                x=times, y=temps,
                mode='lines',
                line=dict(color='#3498db', width=1),
                name='Hourly Temp'
            ))
            
            fig.update_layout(
                title=f"Temperature (Last {len(temps)} Hours)",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)"
            )
        else:
            # Fallback: check for anomaly format
            anomalies = data.get("temperature_anomaly", data.get("anomalies", []))
            if anomalies and isinstance(anomalies, list):
                years = list(range(2020, 2020 + len(anomalies)))
                colors = ['#e74c3c' if a > 0 else '#3498db' for a in anomalies]
                fig.add_trace(go.Bar(x=years, y=anomalies, marker_color=colors,
                                    text=[f"{a:+.2f}°" for a in anomalies], textposition='outside'))
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                fig.update_layout(title="Temperature Anomalies", xaxis_title="Year", yaxis_title="Anomaly (°C)")
            else:
                fig.add_annotation(
                    text="No climate data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=80), height=300)
    return fig


def create_biodiversity_graph(data: Dict[str, Any]) -> go.Figure:
    """Create biodiversity visualization - species observations."""
    fig = go.Figure()
    
    results = data.get("results", [])
    
    if results:
        # Count by taxonomic class/group
        species_counts = {}
        for r in results:
            species = r.get("species", r.get("taxonRank", "Unknown"))
            if species:
                key = species[:15]  # Truncate long names
                species_counts[key] = species_counts.get(key, 0) + 1
        
        if species_counts:
            # Sort and take top 10
            sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            fig.add_trace(go.Bar(
                x=[s[0] for s in sorted_species],
                y=[s[1] for s in sorted_species],
                marker_color='#8BC34A',
                text=[str(s[1]) for s in sorted_species],
                textposition='outside'
            ))
            
            fig.update_layout(
                title=f"Species Observations ({sum(species_counts.values())} total)",
                xaxis_title="Species",
                yaxis_title="Observations",
                xaxis_tickangle=45
            )
    else:
        fig.add_annotation(
            text="No biodiversity data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=80), height=300)
    return fig


def create_intersection_graph(
    datasets: Dict[str, Dict[str, Any]],
    category1: str,
    category2: str
) -> Optional[go.Figure]:
    """
    Create intersection/correlation graph between two datasets.
    
    Meaningful intersections:
    - Air Quality + Weather: AQI vs Temperature/Wind
    - Earthquakes + Radiation: Seismic activity near radiation monitors
    - Wildfires + Air Quality: Fire impact on AQI
    - Weather + Marine: Atmospheric vs ocean conditions
    """
    fig = go.Figure()
    
    data1 = datasets.get(category1, {})
    data2 = datasets.get(category2, {})
    
    if not data1 or not data2:
        return None
    
    # Air Quality + Weather correlation
    if set([category1, category2]) == {"air_quality", "weather"}:
        aqi = data1.get("us_aqi", data2.get("us_aqi", 0))
        temp = data2.get("temperature_c", data1.get("temperature_c", 0))
        wind = data2.get("wind_speed_kmh", data1.get("wind_speed_kmh", 0))
        
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=aqi,
            title={"text": "AQI vs Weather Impact"},
            delta={"reference": 50, "relative": True},
            domain={'x': [0, 0.5], 'y': [0, 1]}
        ))
        
        fig.add_trace(go.Indicator(
            mode="number",
            value=wind,
            title={"text": f"Wind Speed<br>{temp}°C"},
            number={"suffix": " km/h"},
            domain={'x': [0.5, 1], 'y': [0, 1]}
        ))
        
        fig.update_layout(title="Air Quality & Weather Correlation")
    
    # Earthquakes + Wildfires (geographic overlap)
    elif set([category1, category2]) == {"earthquakes", "wildfires"}:
        eq_count = len(data1.get("features", []))
        fire_count = len(data2.get("incidents", data1.get("incidents", [])))
        
        fig.add_trace(go.Bar(
            x=["Earthquakes", "Wildfires"],
            y=[eq_count, fire_count],
            marker_color=["#f39c12", "#e74c3c"],
            text=[str(eq_count), str(fire_count)],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Seismic & Fire Activity",
            yaxis_title="Event Count"
        )
    
    else:
        # Generic comparison
        return None
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig


# Map category IDs to graph creation functions
CATEGORY_GRAPH_FUNCTIONS = {
    "air_quality": create_air_quality_graph,
    "earthquakes": create_earthquake_graph,
    "wildfires": create_wildfire_graph,
    "radiation": create_radiation_graph,
    "weather": create_weather_graph,
    "marine": create_marine_graph,
    "water": create_water_graph,
    "soil": create_soil_graph,
    "climate": create_climate_graph,
    "biodiversity": create_biodiversity_graph
}


def get_graph_for_category(category_id: str, data: Dict[str, Any]) -> go.Figure:
    """Get the appropriate graph for a data category."""
    graph_func = CATEGORY_GRAPH_FUNCTIONS.get(category_id)
    if graph_func:
        return graph_func(data)
    
    # Fallback - generic data display
    fig = go.Figure()
    fig.add_annotation(
        text=f"No visualization for {category_id}",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False
    )
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40), height=300)
    return fig
