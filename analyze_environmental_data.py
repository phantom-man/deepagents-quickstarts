#!/usr/bin/env python3
"""
Agent Data Analysis - Connect the Dots

This script uses DeepAgents to analyze environmental data from our aggregation hub
and find broader connections that turn data into actionable information.

The agents will:
1. Query the data hub for multiple locations
2. Look for patterns and correlations
3. Generate insights and recommendations
4. Post findings to Moltbook for community discussion
"""

import os
import sys
import json
import asyncio
import httpx
from datetime import datetime
from pathlib import Path

# Add DeepAgents to path
sys.path.insert(0, str(Path(__file__).parent / "DeepAgents"))

# Configuration
HUB_BASE_URL = os.environ.get(
    "ENV_MONITOR_URL",
    "https://env-monitor-api-e2uxyywioq-uc.a.run.app"
)

# Key locations to analyze
ANALYSIS_LOCATIONS = [
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
]


async def fetch_hub_data(client: httpx.AsyncClient, endpoint: str) -> dict:
    """Fetch data from our Environmental Hub."""
    try:
        response = await client.get(f"{HUB_BASE_URL}/api/v1{endpoint}")
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}


async def analyze_location(client: httpx.AsyncClient, location: dict) -> dict:
    """Get comprehensive analysis for a location."""
    lat, lon = location["lat"], location["lon"]
    
    # Get quick check and full analysis
    quick = await fetch_hub_data(client, f"/hub/quick?lat={lat}&lon={lon}")
    analysis = await fetch_hub_data(client, f"/hub/analyze?lat={lat}&lon={lon}")
    
    return {
        "location": location["name"],
        "coordinates": {"lat": lat, "lon": lon},
        "quick_check": quick,
        "full_analysis": analysis,
        "timestamp": datetime.utcnow().isoformat()
    }


async def run_multi_location_analysis():
    """Analyze multiple locations and find cross-location patterns."""
    print("=" * 60)
    print("🌍 ENVIRONMENTAL DATA ANALYSIS - CONNECT THE DOTS")
    print("=" * 60)
    print(f"Hub URL: {HUB_BASE_URL}")
    print(f"Analyzing {len(ANALYSIS_LOCATIONS)} locations...")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, get available sources
        sources = await fetch_hub_data(client, "/hub/sources")
        print(f"📊 Available Data Sources: {sources.get('total', 'Unknown')}")
        
        # Analyze each location
        results = []
        for loc in ANALYSIS_LOCATIONS:
            print(f"\n🔍 Analyzing {loc['name']}...")
            result = await analyze_location(client, loc)
            results.append(result)
            
            # Print quick summary
            quick = result.get("quick_check", {})
            summary = quick.get("summary", {})
            weather = summary.get("weather", {})
            
            if weather.get("temperature_c"):
                print(f"   🌡️  Temperature: {weather['temperature_c']}°C")
            if summary.get("recent_earthquakes_nearby"):
                eq_count = summary["recent_earthquakes_nearby"]
                if eq_count > 0:
                    print(f"   ⚠️  Recent earthquakes: {eq_count}")
        
        # Cross-location analysis
        print("\n" + "=" * 60)
        print("🔗 CROSS-LOCATION PATTERNS")
        print("=" * 60)
        
        # Look for patterns
        earthquake_locations = []
        for r in results:
            quick = r.get("quick_check", {})
            eq_count = quick.get("summary", {}).get("recent_earthquakes_nearby", 0)
            if eq_count > 0:
                earthquake_locations.append((r["location"], eq_count))
        
        if earthquake_locations:
            print("\n📍 Seismic Activity Detected:")
            for loc, count in earthquake_locations:
                print(f"   - {loc}: {count} recent earthquakes")
            print("   ⚡ Recommendation: Monitor water quality in affected areas")
        else:
            print("\n✅ No significant seismic activity in monitored locations")
        
        # Generate insights report
        report = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "locations_analyzed": len(results),
            "data_sources_available": sources.get("total", 0),
            "location_results": results,
            "patterns_found": {
                "seismic_activity": earthquake_locations,
            },
            "recommendations": [
                "Monitor air quality during temperature inversions",
                "Check water quality after seismic events",
                "Track wildfire smoke transport patterns",
                "Correlate marine temperatures with coastal weather"
            ]
        }
        
        # Save report
        output_file = Path(__file__).parent / "agent_outputs" / f"env_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📁 Full report saved to: {output_file}")
        
        return report


async def post_findings_to_moltbook(report: dict):
    """Post analysis findings to Moltbook for community discussion."""
    try:
        from DeepAgents.moltbook_client import get_client
        
        client = get_client()
        if not client.api_key:
            print("⚠️  Moltbook not configured - skipping post")
            return
        
        # Create summary post
        locations = [r["location"] for r in report.get("location_results", [])]
        patterns = report.get("patterns_found", {})
        
        content = f"""# 🌍 Environmental Data Analysis Report

**Analysis Time**: {report.get('analysis_timestamp', 'Unknown')}
**Locations Analyzed**: {', '.join(locations)}
**Data Sources Used**: {report.get('data_sources_available', 0)} APIs

## Key Findings

### Seismic Activity
"""
        
        seismic = patterns.get("seismic_activity", [])
        if seismic:
            for loc, count in seismic:
                content += f"- **{loc}**: {count} recent earthquakes detected\n"
            content += "\n⚠️ *Recommendation: Monitor water quality in affected areas*\n"
        else:
            content += "✅ No significant seismic activity in monitored locations\n"
        
        content += """
## Connect the Dots

Our aggregation hub combines data from 15+ public APIs to find correlations:
- Air quality ↔ Weather patterns
- Earthquakes ↔ Water quality
- Marine temps ↔ Coastal weather
- Wildfires ↔ Regional air quality

## Try It Yourself

🔗 **API Endpoint**: `/api/v1/hub/analyze?lat=YOUR_LAT&lon=YOUR_LON`

*What environmental connections have you noticed in your area?*
"""
        
        result = client.post(
            submolt="tech",
            title="🌍 Environmental Data Analysis: Cross-Location Patterns Found",
            content=content
        )
        
        if result:
            print(f"✅ Posted findings to Moltbook!")
            return True
        
    except Exception as e:
        print(f"⚠️  Could not post to Moltbook: {e}")
    
    return False


async def main():
    """Main entry point."""
    # Run analysis
    report = await run_multi_location_analysis()
    
    # Optionally post to Moltbook
    if "--post" in sys.argv:
        await post_findings_to_moltbook(report)
    else:
        print("\n💡 Tip: Run with --post to share findings on Moltbook")


if __name__ == "__main__":
    asyncio.run(main())
