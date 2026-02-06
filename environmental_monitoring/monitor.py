#!/usr/bin/env python3
"""
Environmental Monitoring System - Monitoring Dashboard
Provides real-time monitoring and statistics for the environmental monitoring system.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import curses
import threading
from queue import Queue


class MonitoringDashboard:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=5.0)
        self.running = True
        self.update_queue = Queue()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def fetch_dashboard_stats(self) -> Dict[str, Any]:
        """Fetch dashboard statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/dashboard/stats")
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def fetch_sensor_stats(self) -> Dict[str, Any]:
        """Fetch sensor statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/dashboard/sensor-stats")
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def fetch_alert_stats(self) -> Dict[str, Any]:
        """Fetch alert statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/alerts/statistics")
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def fetch_collaboration_status(self) -> Dict[str, Any]:
        """Fetch collaboration status."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/collaboration/status")
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def update_data(self):
        """Continuously update monitoring data."""
        while self.running:
            try:
                # Fetch all data concurrently
                dashboard_stats, sensor_stats, alert_stats, collab_status = await asyncio.gather(
                    self.fetch_dashboard_stats(),
                    self.fetch_sensor_stats(),
                    self.fetch_alert_stats(),
                    self.fetch_collaboration_status()
                )

                # Put data in queue for display thread
                self.update_queue.put({
                    "timestamp": datetime.now(),
                    "dashboard": dashboard_stats,
                    "sensors": sensor_stats,
                    "alerts": alert_stats,
                    "collaboration": collab_status
                })

            except Exception as e:
                self.update_queue.put({"error": str(e)})

            await asyncio.sleep(5)  # Update every 5 seconds

    def format_number(self, num: float) -> str:
        """Format numbers for display."""
        if isinstance(num, int):
            return f"{num:,}"
        return f"{num:.2f}"

    def draw_dashboard(self, stdscr):
        """Draw the monitoring dashboard."""
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(1000)  # Refresh every second

        while self.running:
            try:
                # Clear screen
                stdscr.clear()

                # Title
                title = "🌱 Environmental Monitoring System - Live Dashboard"
                stdscr.addstr(0, 0, title, curses.A_BOLD)
                stdscr.addstr(1, 0, "=" * len(title))

                # Check for new data
                if not self.update_queue.empty():
                    data = self.update_queue.get()

                    if "error" in data:
                        stdscr.addstr(3, 0, f"❌ Connection Error: {data['error']}", curses.A_BOLD | curses.color_pair(1))
                    else:
                        self.display_data(stdscr, data)

                # Status bar
                height, width = stdscr.getmaxyx()
                status = f"Last update: {datetime.now().strftime('%H:%M:%S')} | Press 'q' to quit"
                stdscr.addstr(height - 1, 0, status, curses.A_DIM)

                stdscr.refresh()

                # Check for quit key
                key = stdscr.getch()
                if key == ord('q'):
                    self.running = False
                    break

            except KeyboardInterrupt:
                self.running = False
                break

    def display_data(self, stdscr, data: Dict[str, Any]):
        """Display monitoring data on screen."""
        y_pos = 3

        # Dashboard Stats
        if "dashboard" in data and "error" not in data["dashboard"]:
            stats = data["dashboard"]
            stdscr.addstr(y_pos, 0, "📊 System Overview", curses.A_BOLD)
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Total Sensors: {self.format_number(stats.get('total_sensors', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Active Readings: {self.format_number(stats.get('active_readings', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Alerts Today: {self.format_number(stats.get('alerts_today', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"System Uptime: {stats.get('uptime_hours', 0):.1f}h")
            y_pos += 2

        # Sensor Stats
        if "sensors" in data and "error" not in data["sensors"]:
            sensor_data = data["sensors"]
            stdscr.addstr(y_pos, 0, "🌡️ Sensor Status", curses.A_BOLD)
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Online Sensors: {self.format_number(sensor_data.get('online_sensors', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Offline Sensors: {self.format_number(sensor_data.get('offline_sensors', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Avg Temperature: {sensor_data.get('avg_temperature', 0):.1f}°C")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Avg Air Quality: {sensor_data.get('avg_air_quality', 0):.1f}")
            y_pos += 2

        # Alert Stats
        if "alerts" in data and "error" not in data["alerts"]:
            alert_data = data["alerts"]
            stdscr.addstr(y_pos, 0, "🚨 Alert Statistics", curses.A_BOLD)
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Total Alerts: {self.format_number(alert_data.get('total_alerts', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Active Alerts: {self.format_number(alert_data.get('active_alerts', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Resolved Today: {self.format_number(alert_data.get('resolved_today', 0))}")
            y_pos += 2

        # Collaboration Status
        if "collaboration" in data and "error" not in data["collaboration"]:
            collab_data = data["collaboration"]
            stdscr.addstr(y_pos, 0, "🤝 Agent Collaboration", curses.A_BOLD)
            y_pos += 1
            status = collab_data.get("status", "unknown")
            status_color = curses.color_pair(2) if status == "active" else curses.color_pair(1)
            stdscr.addstr(y_pos, 2, f"Status: {status.upper()}", status_color)
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Active Sessions: {self.format_number(collab_data.get('active_sessions', 0))}")
            y_pos += 1
            stdscr.addstr(y_pos, 2, f"Completed Tasks: {self.format_number(collab_data.get('completed_tasks', 0))}")

    def run(self):
        """Run the monitoring dashboard."""
        def update_thread():
            """Run the data update loop in a separate thread."""
            asyncio.run(self.update_data())

        # Start update thread
        update_thread = threading.Thread(target=update_thread, daemon=True)
        update_thread.start()

        # Initialize curses
        curses.wrapper(self.draw_dashboard)


async def main():
    """Main function for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Environmental Monitoring System Dashboard")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the system")
    parser.add_argument("--once", action="store_true", help="Print stats once and exit")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    async with MonitoringDashboard(args.url) as dashboard:
        if args.once:
            # Single snapshot
            dashboard_stats, sensor_stats, alert_stats, collab_status = await asyncio.gather(
                dashboard.fetch_dashboard_stats(),
                dashboard.fetch_sensor_stats(),
                dashboard.fetch_alert_stats(),
                dashboard.fetch_collaboration_status()
            )

            data = {
                "timestamp": datetime.now().isoformat(),
                "dashboard": dashboard_stats,
                "sensors": sensor_stats,
                "alerts": alert_stats,
                "collaboration": collab_status
            }

            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print("🌱 Environmental Monitoring System - Status Report")
                print("=" * 55)
                print(f"Timestamp: {data['timestamp']}")
                print()

                for section, section_data in data.items():
                    if section == "timestamp":
                        continue
                    print(f"📊 {section.capitalize()}:")
                    if "error" in section_data:
                        print(f"  ❌ Error: {section_data['error']}")
                    else:
                        for key, value in section_data.items():
                            print(f"  {key}: {value}")
                    print()

        else:
            # Interactive dashboard
            try:
                dashboard.run()
            except KeyboardInterrupt:
                print("\n👋 Dashboard stopped")


if __name__ == "__main__":
    asyncio.run(main())