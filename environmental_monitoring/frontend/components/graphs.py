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
    """Create marine visualization - wave and buoy data."""
    fig = go.Figure()
    
    stations = data.get("stations", [])
    
    if stations:
        wave_heights = []
        station_names = []
        
        for s in stations[:10]:  # Limit to 10 stations
            obs = s.get("latest_observation", {})
            wh = obs.get("wave_height", obs.get("WVHT"))
            if wh:
                wave_heights.append(float(wh))
                station_names.append(s.get("name", s.get("station_id", "Unknown"))[:20])
        
        if wave_heights:
            fig.add_trace(go.Bar(
                x=station_names,
                y=wave_heights,
                marker_color='#3498db',
                text=[f"{h:.1f}m" for h in wave_heights],
                textposition='outside'
            ))
            
            fig.update_layout(
                title="Wave Heights by Station",
                xaxis_title="Station",
                yaxis_title="Wave Height (m)",
                xaxis_tickangle=45
            )
    else:
        fig.add_annotation(
            text="No marine data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=70), height=300)
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
    """Create soil data visualization."""
    fig = go.Figure()
    
    moisture = data.get("moisture", data.get("soil_moisture", []))
    
    if moisture:
        if isinstance(moisture, list):
            depths = [f"{i*10}cm" for i in range(len(moisture))]
            values = moisture
        else:
            depths = ["Surface"]
            values = [moisture]
        
        fig.add_trace(go.Bar(
            x=depths,
            y=values,
            marker_color='#795548',
            text=[f"{v:.1f}%" for v in values],
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
    """Create climate data visualization from Open-Meteo historical data."""
    fig = go.Figure()
    
    # Try to extract Open-Meteo hourly data
    hourly = data.get("hourly", {})
    temperatures = hourly.get("temperature_2m", [])
    time_data = hourly.get("time", [])
    
    if temperatures and time_data:
        # Sample the data (daily averages for last 30 days worth)
        # Open-Meteo returns hourly data, so 24 * 30 = 720 points for a month
        sample_size = min(720, len(temperatures))
        temps = temperatures[-sample_size:]
        times = time_data[-sample_size:]
        
        # Calculate daily averages (group by 24 hours)
        daily_temps = []
        daily_dates = []
        for i in range(0, len(temps), 24):
            chunk = temps[i:i+24]
            if chunk:
                avg = sum(chunk) / len(chunk)
                daily_temps.append(avg)
                if i < len(times):
                    daily_dates.append(times[i][:10])  # Just the date part
        
        if daily_temps:
            # Limit to last 14 days for readability
            daily_temps = daily_temps[-14:]
            daily_dates = daily_dates[-14:]
            
            # Calculate color based on temperature
            colors = ['#e74c3c' if t > 20 else '#3498db' if t < 10 else '#f39c12' for t in daily_temps]
            
            fig.add_trace(go.Scatter(
                x=daily_dates,
                y=daily_temps,
                mode='lines+markers',
                marker=dict(color=colors, size=8),
                line=dict(color='#7f8c8d'),
                name='Daily Avg'
            ))
            
            # Add average line
            avg_temp = sum(daily_temps) / len(daily_temps)
            fig.add_hline(y=avg_temp, line_dash="dash", line_color="orange",
                         annotation_text=f"Avg: {avg_temp:.1f}°C")
            
            fig.update_layout(
                title=f"Temperature Trend (Last {len(daily_temps)} Days)",
                xaxis_title="Date",
                yaxis_title="Temperature (°C)",
                xaxis_tickangle=45
            )
        else:
            fig.add_annotation(
                text="Could not process temperature data",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
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
