"""Performance optimization, hardware telemetry, and dynamic VRAM guard subsystem."""

from gaming_ai.optimization.telemetry import PerformanceTracker, HardwareMonitor, MetricSnapshot
from gaming_ai.optimization.vram_guard import VRAMGuard, VRAMState

__all__ = [
    "PerformanceTracker",
    "HardwareMonitor",
    "MetricSnapshot",
    "VRAMGuard",
    "VRAMState",
]
