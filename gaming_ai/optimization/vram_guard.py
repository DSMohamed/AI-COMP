"""Dynamic VRAM guard protecting gameplay frame rates and preventing out-of-memory crashes."""

from __future__ import annotations

from enum import Enum
import logging
from typing import Callable, Dict, Optional

from gaming_ai.optimization.telemetry import HardwareMonitor

logger = logging.getLogger("gaming_ai.optimization.vram_guard")


class VRAMState(str, Enum):
    """VRAM operating state levels."""
    NORMAL = "normal"      # < 6.0 GB (Full observation active)
    WARNING = "warning"    # 6.0 GB - 7.2 GB (Throttled vision capture)
    CRITICAL = "critical"  # > 7.2 GB (Auto-evict VLM, degrade to text/voice)


class VRAMGuard:
    """Monitors GPU memory headroom and dynamically throttles AI pipelines to prevent game stutter."""

    def __init__(
        self,
        hardware_monitor: Optional[HardwareMonitor] = None,
        warning_threshold_mb: float = 6144.0,   # 6.0 GB
        critical_threshold_mb: float = 7372.0,  # 7.2 GB (90% of 8GB RTX 3070)
        on_state_change: Optional[Callable[[VRAMState, float], None]] = None,
    ) -> None:
        self.monitor = hardware_monitor or HardwareMonitor()
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.on_state_change = on_state_change
        self.current_state: VRAMState = VRAMState.NORMAL

    def check_vram(self, vram_override_mb: Optional[float] = None) -> VRAMState:
        """
        Evaluate current VRAM usage and trigger adaptation callbacks on state transitions.
        """
        if vram_override_mb is not None:
            used_mb = vram_override_mb
        else:
            gpu_data = self.monitor.query_gpu()
            used_mb = gpu_data.get("vram_used_mb", 4000.0)

        prev_state = self.current_state

        if used_mb >= self.critical_threshold_mb:
            new_state = VRAMState.CRITICAL
        elif used_mb >= self.warning_threshold_mb:
            new_state = VRAMState.WARNING
        else:
            new_state = VRAMState.NORMAL

        if new_state != prev_state:
            logger.warning(
                "⚠️ VRAM State Transition: [%s -> %s] (Usage: %.1f MB / Critical: %.1f MB)",
                prev_state.value.upper(),
                new_state.value.upper(),
                used_mb,
                self.critical_threshold_mb,
            )
            self.current_state = new_state
            if self.on_state_change:
                self.on_state_change(new_state, used_mb)

        return new_state

    def get_suggested_screen_interval(self) -> float:
        """Get recommended observation polling interval based on current VRAM state."""
        if self.current_state == VRAMState.CRITICAL:
            return 10.0  # Heavily throttled
        elif self.current_state == VRAMState.WARNING:
            return 4.0   # Mildly throttled
        return 2.0       # Normal real-time pace
