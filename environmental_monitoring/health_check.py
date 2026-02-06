#!/usr/bin/env python3
"""
Environmental Monitoring System - Health Check Script
Checks the health of all system components and agents.
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, List, Any


class HealthChecker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_endpoint(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        """Check a specific endpoint health."""
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}

            return {
                "status": "healthy" if response.status_code < 400 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        return await self.check_endpoint("/api/v1/health/database")

    async def check_cache(self) -> Dict[str, Any]:
        """Check cache connectivity."""
        return await self.check_endpoint("/api/v1/health/cache")

    async def check_agents(self) -> Dict[str, Any]:
        """Check all agents health."""
        agents = ["ecodata", "climateml", "geospatial", "alertsystem"]
        results = {}

        for agent in agents:
            result = await self.check_endpoint(f"/api/v1/health/agent/{agent}")
            results[agent] = result

        # Overall agent health
        healthy_count = sum(1 for r in results.values() if r.get("status") == "healthy")
        total_count = len(results)

        return {
            "status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_agents": healthy_count,
            "total_agents": total_count,
            "details": results
        }

    async def check_moltbook(self) -> Dict[str, Any]:
        """Check Moltbook collaboration service."""
        return await self.check_endpoint("/api/v1/health/moltbook")

    async def check_sensors(self) -> Dict[str, Any]:
        """Check sensor connectivity."""
        try:
            result = await self.check_endpoint("/api/v1/sensors")
            if result["status"] == "healthy":
                sensor_count = len(result.get("data", []))
                return {
                    "status": "healthy",
                    "sensor_count": sensor_count,
                    "message": f"Connected to {sensor_count} sensors"
                }
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def run_full_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        print("🔍 Running comprehensive health check...")

        checks = {
            "api": await self.check_endpoint("/health"),
            "database": await self.check_database(),
            "cache": await self.check_cache(),
            "agents": await self.check_agents(),
            "moltbook": await self.check_moltbook(),
            "sensors": await self.check_sensors()
        }

        # Overall system health
        critical_checks = ["api", "database", "agents"]
        critical_healthy = all(
            checks[check]["status"] == "healthy"
            for check in critical_checks
            if checks[check]["status"] != "error"
        )

        overall_status = "healthy" if critical_healthy else "unhealthy"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy_checks": sum(1 for c in checks.values() if c.get("status") == "healthy"),
                "unhealthy_checks": sum(1 for c in checks.values() if c.get("status") == "unhealthy"),
                "error_checks": sum(1 for c in checks.values() if c.get("status") == "error")
            }
        }


async def main():
    """Main health check function."""
    import argparse

    parser = argparse.ArgumentParser(description="Environmental Monitoring System Health Check")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the system")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--quiet", action="store_true", help="Only show overall status")

    args = parser.parse_args()

    async with HealthChecker(args.url) as checker:
        try:
            result = await checker.run_full_check()

            if args.quiet:
                print(result["overall_status"].upper())
                sys.exit(0 if result["overall_status"] == "healthy" else 1)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                # Pretty print
                print(f"\n🌱 Environmental Monitoring System Health Check")
                print(f"{'='*55}")
                print(f"Timestamp: {result['timestamp']}")
                print(f"Overall Status: {result['overall_status'].upper()}")
                print(f"\n📊 Summary:")
                summary = result["summary"]
                print(f"  Total Checks: {summary['total_checks']}")
                print(f"  Healthy: {summary['healthy_checks']}")
                print(f"  Unhealthy: {summary['unhealthy_checks']}")
                print(f"  Errors: {summary['error_checks']}")

                print(f"\n🔍 Detailed Results:")
                for check_name, check_result in result["checks"].items():
                    status = check_result.get("status", "unknown")
                    emoji = {
                        "healthy": "✅",
                        "unhealthy": "⚠️",
                        "error": "❌",
                        "unknown": "❓"
                    }.get(status, "❓")

                    print(f"  {emoji} {check_name.capitalize()}: {status.upper()}")
                    if "message" in check_result:
                        print(f"      {check_result['message']}")

            # Exit with appropriate code
            sys.exit(0 if result["overall_status"] == "healthy" else 1)

        except Exception as e:
            print(f"❌ Health check failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())