/**
 * Google Maps JavaScript API Integration for Environmental Monitoring Dashboard
 * 
 * Features:
 * - Advanced Markers (AdvancedMarkerElement)
 * - Data Layers for GeoJSON
 * - Custom info windows with environmental data
 * - Marker clustering for dense data
 * - Dynamic styling based on data values (AQI, magnitude, etc.)
 * 
 * Note: Heatmap Layer is deprecated (May 2026) - use deck.gl for heatmaps
 */

// Global map instance and marker collections
let envMap = null;
let markers = [];
let infoWindow = null;
let dataLayer = null;

// AQI color scale (EPA Standard)
const AQI_COLORS = {
    good: '#00E400',           // 0-50
    moderate: '#FFFF00',       // 51-100
    unhealthySensitive: '#FF7E00', // 101-150
    unhealthy: '#FF0000',      // 151-200
    veryUnhealthy: '#8F3F97',  // 201-300
    hazardous: '#7E0023'       // 301+
};

// Category icons (using SVG paths for custom markers)
const CATEGORY_ICONS = {
    air_quality: {
        path: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z',
        color: '#2E86AB',
        scale: 1.5
    },
    earthquake: {
        path: 'M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z',
        color: '#C73E1D',
        scale: 1.5
    },
    wildfire: {
        path: 'M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z',
        color: '#F18F01',
        scale: 1.5
    },
    water: {
        path: 'M12 2c-5.33 4.55-8 8.48-8 11.8 0 4.98 3.8 8.2 8 8.2s8-3.22 8-8.2c0-3.32-2.67-7.25-8-11.8zm0 18c-3.35 0-6-2.57-6-6.2 0-2.34 1.95-5.44 6-9.14 4.05 3.7 6 6.79 6 9.14 0 3.63-2.65 6.2-6 6.2z',
        color: '#17A2B8',
        scale: 1.5
    },
    weather: {
        path: 'M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM19 18H6c-2.21 0-4-1.79-4-4s1.79-4 4-4h.71C7.37 7.69 9.48 6 12 6c3.04 0 5.5 2.46 5.5 5.5v.5H19c1.66 0 3 1.34 3 3s-1.34 3-3 3z',
        color: '#28A745',
        scale: 1.5
    },
    marine: {
        path: 'M17 15.97c-.51 0-1.01-.2-1.41-.59L14 13.79l-1.59 1.59c-.78.78-2.05.78-2.83 0L8 13.79l-1.59 1.59c-.39.39-.89.59-1.41.59s-1.01-.2-1.41-.59L2 13.79V17c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-3.21l-1.59 1.59c-.4.39-.9.59-1.41.59zM22 8c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v4.21l1.59-1.59c.78-.78 2.05-.78 2.83 0L8 12.21l1.59-1.59c.78-.78 2.05-.78 2.83 0l1.59 1.59 1.59-1.59c.78-.78 2.05-.78 2.83 0L22 12.21V8z',
        color: '#2E86AB',
        scale: 1.5
    },
    default: {
        path: 'M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z',
        color: '#6C757D',
        scale: 1.5
    }
};

/**
 * Get AQI color based on value
 */
function getAqiColor(aqi) {
    if (aqi <= 50) return AQI_COLORS.good;
    if (aqi <= 100) return AQI_COLORS.moderate;
    if (aqi <= 150) return AQI_COLORS.unhealthySensitive;
    if (aqi <= 200) return AQI_COLORS.unhealthy;
    if (aqi <= 300) return AQI_COLORS.veryUnhealthy;
    return AQI_COLORS.hazardous;
}

/**
 * Get earthquake color based on magnitude
 */
function getEarthquakeColor(magnitude) {
    if (magnitude < 3) return '#00E400';
    if (magnitude < 4) return '#FFFF00';
    if (magnitude < 5) return '#FF7E00';
    if (magnitude < 6) return '#FF0000';
    if (magnitude < 7) return '#8F3F97';
    return '#7E0023';
}

/**
 * Get marker size based on value (for scaling markers by data)
 */
function getMarkerSize(value, minValue, maxValue, minSize = 20, maxSize = 50) {
    if (maxValue === minValue) return (minSize + maxSize) / 2;
    const normalized = (value - minValue) / (maxValue - minValue);
    return minSize + normalized * (maxSize - minSize);
}

/**
 * Initialize the Google Map
 */
async function initEnvMap(mapElementId, lat = 37.7749, lon = -122.4194, zoom = 10) {
    // Load the Maps JavaScript API with marker library
    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    
    const mapElement = document.getElementById(mapElementId);
    if (!mapElement) {
        console.error(`Map element '${mapElementId}' not found`);
        return null;
    }
    
    envMap = new Map(mapElement, {
        center: { lat: lat, lng: lon },
        zoom: zoom,
        mapId: 'ENV_MONITOR_MAP', // Required for Advanced Markers
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            mapTypeIds: ['roadmap', 'satellite', 'hybrid', 'terrain']
        },
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true
    });
    
    // Create shared info window
    infoWindow = new google.maps.InfoWindow();
    
    // Initialize data layer for GeoJSON
    dataLayer = envMap.data;
    
    return envMap;
}

/**
 * Create a custom marker element with SVG icon
 */
function createMarkerContent(category, color, size = 40) {
    const iconConfig = CATEGORY_ICONS[category] || CATEGORY_ICONS.default;
    const markerColor = color || iconConfig.color;
    
    const div = document.createElement('div');
    div.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" 
             width="${size}" height="${size}" 
             viewBox="0 0 24 24" 
             fill="${markerColor}"
             style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.3));">
            <path d="${iconConfig.path}"/>
        </svg>
    `;
    return div;
}

/**
 * Add environmental data markers to the map
 */
async function addEnvMarkers(dataPoints, category = 'default', valueField = null) {
    if (!envMap) {
        console.error('Map not initialized');
        return;
    }
    
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    
    // Clear existing markers
    clearMarkers();
    
    // Calculate min/max for scaling if value field provided
    let minValue = Infinity;
    let maxValue = -Infinity;
    if (valueField) {
        dataPoints.forEach(point => {
            const val = point[valueField];
            if (val !== undefined && val !== null) {
                minValue = Math.min(minValue, val);
                maxValue = Math.max(maxValue, val);
            }
        });
    }
    
    // Add markers for each data point
    dataPoints.forEach(point => {
        const lat = point.latitude || point.lat;
        const lon = point.longitude || point.lon || point.lng;
        
        if (lat === undefined || lon === undefined) return;
        
        // Determine marker color based on category and value
        let markerColor = null;
        let markerSize = 40;
        
        if (valueField && point[valueField] !== undefined) {
            const value = point[valueField];
            
            if (category === 'air_quality') {
                markerColor = getAqiColor(value);
            } else if (category === 'earthquake') {
                markerColor = getEarthquakeColor(value);
                markerSize = getMarkerSize(value, 0, 9, 20, 60);
            } else {
                markerSize = getMarkerSize(value, minValue, maxValue, 20, 50);
            }
        }
        
        const markerContent = createMarkerContent(category, markerColor, markerSize);
        
        const marker = new AdvancedMarkerElement({
            map: envMap,
            position: { lat: lat, lng: lon },
            content: markerContent,
            title: point.name || point.title || `${category} reading`
        });
        
        // Add click event to show info window
        marker.addListener('click', () => {
            const content = createInfoWindowContent(point, category);
            infoWindow.setContent(content);
            infoWindow.open(envMap, marker);
        });
        
        markers.push(marker);
    });
    
    // Fit map to markers if we have any
    if (markers.length > 0) {
        const bounds = new google.maps.LatLngBounds();
        markers.forEach(marker => {
            bounds.extend(marker.position);
        });
        envMap.fitBounds(bounds);
    }
}

/**
 * Create info window content for a data point
 */
function createInfoWindowContent(point, category) {
    let content = '<div style="max-width: 300px; padding: 8px;">';
    
    // Title
    const title = point.name || point.title || point.location || 'Unknown Location';
    content += `<h6 style="margin: 0 0 8px 0; color: #2E86AB;">${title}</h6>`;
    
    // Category-specific content
    if (category === 'air_quality') {
        if (point.aqi !== undefined) {
            const aqiColor = getAqiColor(point.aqi);
            content += `<p style="margin: 4px 0;"><strong>AQI:</strong> <span style="color: ${aqiColor}; font-weight: bold;">${point.aqi}</span></p>`;
        }
        if (point.pm25 !== undefined) content += `<p style="margin: 4px 0;"><strong>PM2.5:</strong> ${point.pm25} µg/m³</p>`;
        if (point.pm10 !== undefined) content += `<p style="margin: 4px 0;"><strong>PM10:</strong> ${point.pm10} µg/m³</p>`;
        if (point.o3 !== undefined) content += `<p style="margin: 4px 0;"><strong>O₃:</strong> ${point.o3} ppb</p>`;
    } else if (category === 'earthquake') {
        if (point.magnitude !== undefined) {
            const magColor = getEarthquakeColor(point.magnitude);
            content += `<p style="margin: 4px 0;"><strong>Magnitude:</strong> <span style="color: ${magColor}; font-weight: bold;">${point.magnitude.toFixed(1)}</span></p>`;
        }
        if (point.depth !== undefined) content += `<p style="margin: 4px 0;"><strong>Depth:</strong> ${point.depth} km</p>`;
        if (point.time !== undefined) content += `<p style="margin: 4px 0;"><strong>Time:</strong> ${new Date(point.time).toLocaleString()}</p>`;
    } else if (category === 'wildfire') {
        if (point.confidence !== undefined) content += `<p style="margin: 4px 0;"><strong>Confidence:</strong> ${point.confidence}%</p>`;
        if (point.brightness !== undefined) content += `<p style="margin: 4px 0;"><strong>Brightness:</strong> ${point.brightness}K</p>`;
        if (point.frp !== undefined) content += `<p style="margin: 4px 0;"><strong>Fire Radiative Power:</strong> ${point.frp} MW</p>`;
    } else if (category === 'water') {
        if (point.value !== undefined) content += `<p style="margin: 4px 0;"><strong>Value:</strong> ${point.value}</p>`;
        if (point.unit !== undefined) content += `<p style="margin: 4px 0;"><strong>Unit:</strong> ${point.unit}</p>`;
        if (point.parameter !== undefined) content += `<p style="margin: 4px 0;"><strong>Parameter:</strong> ${point.parameter}</p>`;
    } else if (category === 'weather') {
        if (point.temperature !== undefined) content += `<p style="margin: 4px 0;"><strong>Temperature:</strong> ${point.temperature}°${point.temp_unit || 'C'}</p>`;
        if (point.humidity !== undefined) content += `<p style="margin: 4px 0;"><strong>Humidity:</strong> ${point.humidity}%</p>`;
        if (point.wind_speed !== undefined) content += `<p style="margin: 4px 0;"><strong>Wind:</strong> ${point.wind_speed} ${point.wind_unit || 'm/s'}</p>`;
        if (point.conditions !== undefined) content += `<p style="margin: 4px 0;"><strong>Conditions:</strong> ${point.conditions}</p>`;
    } else {
        // Generic display for other categories
        for (const [key, value] of Object.entries(point)) {
            if (['lat', 'latitude', 'lon', 'lng', 'longitude', 'geometry'].includes(key)) continue;
            if (value === null || value === undefined) continue;
            content += `<p style="margin: 4px 0;"><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</p>`;
        }
    }
    
    // Timestamp
    if (point.timestamp || point.updated_at || point.measured_at) {
        const ts = point.timestamp || point.updated_at || point.measured_at;
        content += `<p style="margin: 8px 0 0 0; font-size: 11px; color: #6C757D;">Updated: ${new Date(ts).toLocaleString()}</p>`;
    }
    
    content += '</div>';
    return content;
}

/**
 * Clear all markers from the map
 */
function clearMarkers() {
    markers.forEach(marker => {
        marker.map = null;
    });
    markers = [];
}

/**
 * Load GeoJSON data onto the map
 */
function loadGeoJson(geoJsonData, styleOptions = {}) {
    if (!envMap || !dataLayer) {
        console.error('Map or data layer not initialized');
        return;
    }
    
    // Clear existing data
    dataLayer.forEach(feature => {
        dataLayer.remove(feature);
    });
    
    // Add new data
    if (typeof geoJsonData === 'string') {
        dataLayer.loadGeoJson(geoJsonData);
    } else {
        dataLayer.addGeoJson(geoJsonData);
    }
    
    // Apply styling
    const defaultStyle = {
        fillColor: '#2E86AB',
        fillOpacity: 0.4,
        strokeColor: '#1a5276',
        strokeWeight: 2,
        strokeOpacity: 0.8
    };
    
    const mergedStyle = { ...defaultStyle, ...styleOptions };
    
    dataLayer.setStyle(feature => {
        // Check for feature-specific properties
        const props = {};
        feature.forEachProperty((value, key) => {
            props[key] = value;
        });
        
        // Dynamic styling based on feature properties
        let fillColor = mergedStyle.fillColor;
        let fillOpacity = mergedStyle.fillOpacity;
        
        if (props.aqi !== undefined) {
            fillColor = getAqiColor(props.aqi);
            fillOpacity = 0.6;
        } else if (props.magnitude !== undefined) {
            fillColor = getEarthquakeColor(props.magnitude);
            fillOpacity = 0.6;
        } else if (props.containment !== undefined) {
            // Wildfire containment - less contained = more red
            const containment = parseFloat(props.containment) || 0;
            fillColor = containment > 50 ? '#F18F01' : '#C73E1D';
            fillOpacity = 0.5;
        }
        
        return {
            fillColor: fillColor,
            fillOpacity: fillOpacity,
            strokeColor: mergedStyle.strokeColor,
            strokeWeight: mergedStyle.strokeWeight,
            strokeOpacity: mergedStyle.strokeOpacity
        };
    });
    
    // Add click events for features
    dataLayer.addListener('click', event => {
        const props = {};
        event.feature.forEachProperty((value, key) => {
            props[key] = value;
        });
        
        const content = createInfoWindowContent(props, 'geojson');
        infoWindow.setContent(content);
        infoWindow.setPosition(event.latLng);
        infoWindow.open(envMap);
    });
}

/**
 * Set map center and zoom
 */
function setMapView(lat, lon, zoom = null) {
    if (!envMap) return;
    
    envMap.setCenter({ lat: lat, lng: lon });
    if (zoom !== null) {
        envMap.setZoom(zoom);
    }
}

/**
 * Get current map bounds
 */
function getMapBounds() {
    if (!envMap) return null;
    
    const bounds = envMap.getBounds();
    if (!bounds) return null;
    
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    
    return {
        north: ne.lat(),
        south: sw.lat(),
        east: ne.lng(),
        west: sw.lng()
    };
}

// Export functions for global access
window.envMapAPI = {
    init: initEnvMap,
    addMarkers: addEnvMarkers,
    clearMarkers: clearMarkers,
    loadGeoJson: loadGeoJson,
    setView: setMapView,
    getBounds: getMapBounds,
    getMap: () => envMap
};
