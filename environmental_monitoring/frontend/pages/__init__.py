"""Pages package for Environmental Monitoring Dashboard."""
from pages.dashboard import create_dashboard_layout
from pages.explore import create_explore_layout
from pages.analyze import create_analyze_layout
from pages.reports import create_reports_layout

__all__ = [
    "create_dashboard_layout",
    "create_explore_layout",
    "create_analyze_layout",
    "create_reports_layout"
]
