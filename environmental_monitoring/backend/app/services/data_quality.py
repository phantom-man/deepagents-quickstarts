"""
Data quality validation and monitoring for environmental data.

This module provides:
- Data validation against expected ranges
- Anomaly detection for sensor readings
- Data freshness monitoring
- Quality scoring for ingested data
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """Quality levels for environmental data."""
    EXCELLENT = "excellent"  # 95-100% confidence
    GOOD = "good"            # 80-95% confidence  
    FAIR = "fair"            # 60-80% confidence
    POOR = "poor"            # 40-60% confidence
    SUSPECT = "suspect"      # <40% confidence


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    quality_level: DataQualityLevel
    issues: List[str]
    suggestions: List[str]


# ============================================================================
# VALIDATION RULES FOR ENVIRONMENTAL PARAMETERS
# ============================================================================

PARAMETER_RANGES = {
    # Air Quality Parameters
    "pm25": {"min": 0, "max": 1000, "unit": "μg/m³", "typical_max": 150},
    "pm10": {"min": 0, "max": 2000, "unit": "μg/m³", "typical_max": 300},
    "o3": {"min": 0, "max": 500, "unit": "ppb", "typical_max": 150},
    "no2": {"min": 0, "max": 500, "unit": "ppb", "typical_max": 200},
    "so2": {"min": 0, "max": 500, "unit": "ppb", "typical_max": 100},
    "co": {"min": 0, "max": 50, "unit": "ppm", "typical_max": 10},
    
    # Weather Parameters
    "temperature": {"min": -90, "max": 60, "unit": "celsius", "typical_range": (-20, 45)},
    "humidity": {"min": 0, "max": 100, "unit": "percent"},
    "pressure": {"min": 870, "max": 1085, "unit": "hPa"},
    "wind_speed": {"min": 0, "max": 120, "unit": "m/s", "typical_max": 50},
    
    # Water Quality Parameters
    "ph": {"min": 0, "max": 14, "unit": "pH", "typical_range": (6.5, 8.5)},
    "dissolved_oxygen": {"min": 0, "max": 20, "unit": "mg/L", "typical_range": (4, 12)},
    "discharge": {"min": 0, "max": 100000, "unit": "ft³/s"},
    "turbidity": {"min": 0, "max": 4000, "unit": "NTU", "typical_max": 100},
    "conductivity": {"min": 0, "max": 100000, "unit": "μS/cm"},
}


# ============================================================================
# DATA VALIDATOR
# ============================================================================

class DataValidator:
    """Validates environmental data against expected ranges and patterns."""
    
    def __init__(self):
        self.recent_values: Dict[str, List[Tuple[datetime, float]]] = {}
        self.max_history = 100  # Keep last 100 values per parameter
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate a single data record."""
        issues = []
        suggestions = []
        quality_score = 1.0
        
        # Extract key fields
        parameter = data.get("parameter", "").lower()
        value = data.get("value")
        timestamp = data.get("timestamp")
        source = data.get("source", "unknown")
        
        # Check for missing data
        if value is None:
            issues.append("Missing value")
            quality_score -= 0.5
        
        if parameter not in PARAMETER_RANGES and value is not None:
            # Unknown parameter, still valid but lower confidence
            quality_score -= 0.1
            suggestions.append(f"Unknown parameter '{parameter}' - using generic validation")
        
        # Range validation
        if value is not None and parameter in PARAMETER_RANGES:
            ranges = PARAMETER_RANGES[parameter]
            
            # Hard limits
            if value < ranges["min"] or value > ranges["max"]:
                issues.append(f"Value {value} outside valid range [{ranges['min']}, {ranges['max']}]")
                quality_score -= 0.4
            
            # Typical range warnings
            elif "typical_max" in ranges and value > ranges["typical_max"]:
                suggestions.append(f"Value {value} is unusually high (typical max: {ranges['typical_max']})")
                quality_score -= 0.1
            elif "typical_range" in ranges:
                low, high = ranges["typical_range"]
                if value < low or value > high:
                    suggestions.append(f"Value {value} outside typical range [{low}, {high}]")
                    quality_score -= 0.1
        
        # Timestamp validation
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                else:
                    ts = timestamp
                
                # Check for future timestamps
                if ts > datetime.now(ts.tzinfo) + timedelta(hours=1):
                    issues.append("Timestamp is in the future")
                    quality_score -= 0.2
                
                # Check for very old data
                if ts < datetime.now(ts.tzinfo) - timedelta(days=7):
                    suggestions.append("Data is more than 7 days old")
                    quality_score -= 0.1
                    
            except (ValueError, TypeError) as e:
                issues.append(f"Invalid timestamp format: {e}")
                quality_score -= 0.1
        
        # Anomaly detection using recent history
        if value is not None and parameter:
            anomaly_score = self._check_anomaly(parameter, value)
            if anomaly_score > 0:
                suggestions.append(f"Potential anomaly detected (score: {anomaly_score:.2f})")
                quality_score -= anomaly_score * 0.2
        
        # Ensure score is in valid range
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Determine quality level
        if quality_score >= 0.95:
            quality_level = DataQualityLevel.EXCELLENT
        elif quality_score >= 0.80:
            quality_level = DataQualityLevel.GOOD
        elif quality_score >= 0.60:
            quality_level = DataQualityLevel.FAIR
        elif quality_score >= 0.40:
            quality_level = DataQualityLevel.POOR
        else:
            quality_level = DataQualityLevel.SUSPECT
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            quality_level=quality_level,
            issues=issues,
            suggestions=suggestions
        )
    
    def _check_anomaly(self, parameter: str, value: float) -> float:
        """Check if value is anomalous compared to recent history."""
        key = parameter
        
        # Add to history
        if key not in self.recent_values:
            self.recent_values[key] = []
        
        self.recent_values[key].append((datetime.utcnow(), value))
        
        # Trim old values
        if len(self.recent_values[key]) > self.max_history:
            self.recent_values[key] = self.recent_values[key][-self.max_history:]
        
        # Need at least 10 values for anomaly detection
        if len(self.recent_values[key]) < 10:
            return 0.0
        
        values = [v for _, v in self.recent_values[key][:-1]]  # Exclude current
        
        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            
            if stdev == 0:
                return 0.0
            
            # Z-score
            z_score = abs(value - mean) / stdev
            
            # Convert to 0-1 anomaly score (>3 sigma is highly anomalous)
            if z_score > 3:
                return 1.0
            elif z_score > 2:
                return 0.5
            elif z_score > 1.5:
                return 0.2
            else:
                return 0.0
                
        except statistics.StatisticsError:
            return 0.0
    
    def validate_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of records and return summary."""
        results = []
        valid_count = 0
        quality_scores = []
        
        for record in records:
            result = self.validate(record)
            results.append(result)
            if result.is_valid:
                valid_count += 1
            quality_scores.append(result.quality_score)
        
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.0
        
        return {
            "total_records": len(records),
            "valid_records": valid_count,
            "invalid_records": len(records) - valid_count,
            "average_quality_score": avg_quality,
            "quality_distribution": {
                level.value: sum(1 for r in results if r.quality_level == level)
                for level in DataQualityLevel
            },
            "results": results
        }


# ============================================================================
# DATA FRESHNESS MONITOR
# ============================================================================

class FreshnessMonitor:
    """Monitors data freshness and alerts on stale data."""
    
    def __init__(self):
        self.last_seen: Dict[str, datetime] = {}
        self.expected_intervals: Dict[str, int] = {
            "openaq": 600,      # 10 minutes
            "usgs_water": 900,  # 15 minutes
            "openweathermap": 600,  # 10 minutes
            "airnow": 3600,     # 1 hour
        }
    
    def record_data(self, source: str):
        """Record that we received data from a source."""
        self.last_seen[source] = datetime.utcnow()
    
    def check_freshness(self) -> Dict[str, Any]:
        """Check freshness of all data sources."""
        now = datetime.utcnow()
        status = {}
        
        for source, expected_interval in self.expected_intervals.items():
            if source not in self.last_seen:
                status[source] = {
                    "status": "unknown",
                    "message": "No data received yet"
                }
            else:
                age_seconds = (now - self.last_seen[source]).total_seconds()
                
                if age_seconds <= expected_interval:
                    status[source] = {
                        "status": "fresh",
                        "age_seconds": age_seconds,
                        "last_seen": self.last_seen[source].isoformat()
                    }
                elif age_seconds <= expected_interval * 2:
                    status[source] = {
                        "status": "stale",
                        "age_seconds": age_seconds,
                        "message": f"Data is {age_seconds/60:.1f} minutes old"
                    }
                else:
                    status[source] = {
                        "status": "critical",
                        "age_seconds": age_seconds,
                        "message": f"Data is {age_seconds/3600:.1f} hours old - possible outage"
                    }
        
        return {
            "timestamp": now.isoformat(),
            "sources": status,
            "overall_status": self._get_overall_status(status)
        }
    
    def _get_overall_status(self, status: Dict) -> str:
        """Determine overall status from individual source statuses."""
        statuses = [s.get("status") for s in status.values()]
        
        if "critical" in statuses:
            return "degraded"
        elif "stale" in statuses:
            return "warning"
        elif all(s == "fresh" for s in statuses):
            return "healthy"
        else:
            return "unknown"


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

data_validator = DataValidator()
freshness_monitor = FreshnessMonitor()
