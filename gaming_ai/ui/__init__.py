"""User Interface and Dashboard subsystem for real-time telemetry, transcript, and control."""

from gaming_ai.ui.state import DashboardState, TranscriptItem
from gaming_ai.ui.web_server import create_dashboard_app

__all__ = ["DashboardState", "TranscriptItem", "create_dashboard_app"]
