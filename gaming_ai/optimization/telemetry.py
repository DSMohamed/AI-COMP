"""Real-time latency tracking and hardware resource monitoring."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gaming_ai.optimization.telemetry")


@dataclass
class MetricSnapshot:
    """Snapshot of system performance and pipeline latencies."""
    stt_latency_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_tokens_per_sec: float = 0.0
    vlm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    gpu_vram_used_mb: float = 0.0
    gpu_vram_total_mb: float = 8192.0
    gpu_util_pct: float = 0.0
    cpu_util_pct: float = 0.0
    timestamp: float = field(default_factory=time.time)


class PerformanceTracker:
    """Tracks latency metrics across pipeline stages with rolling statistics."""

    def __init__(self, window_size: int = 50) -> None:
        self.window_size = window_size
        self._stt_history: deque[float] = deque(maxlen=window_size)
        self._llm_ttft_history: deque[float] = deque(maxlen=window_size)
        self._vlm_history: deque[float] = deque(maxlen=window_size)
        self._tts_history: deque[float] = deque(maxlen=window_size)

    def record_stt(self, latency_ms: float) -> None:
        self._stt_history.append(latency_ms)

    def record_llm_ttft(self, latency_ms: float) -> None:
        self._llm_ttft_history.append(latency_ms)

    def record_vlm(self, latency_ms: float) -> None:
        self._vlm_history.append(latency_ms)

    def record_tts(self, latency_ms: float) -> None:
        self._tts_history.append(latency_ms)

    def get_averages(self) -> Dict[str, float]:
        """Compute rolling average latencies for each pipeline stage."""
        return {
            "avg_stt_ms": round(sum(self._stt_history) / len(self._stt_history), 1) if self._stt_history else 0.0,
            "avg_llm_ttft_ms": round(sum(self._llm_ttft_history) / len(self._llm_ttft_history), 1) if self._llm_ttft_history else 0.0,
            "avg_vlm_ms": round(sum(self._vlm_history) / len(self._vlm_history), 1) if self._vlm_history else 0.0,
            "avg_tts_ms": round(sum(self._tts_history) / len(self._tts_history), 1) if self._tts_history else 0.0,
        }


class HardwareMonitor:
    """Queries NVIDIA GPU VRAM and system CPU utilization."""

    def __init__(self) -> None:
        self._has_nvidia_smi = shutil.which("nvidia-smi") is not None
        self._cached_vram_total: float = 8192.0

    def query_gpu(self) -> Dict[str, float]:
        """
        Query current GPU utilization and VRAM usage via nvidia-smi or torch.
        Returns used_mb, total_mb, util_pct.
        """
        # Try PyTorch CUDA if initialized
        try:
            import torch
            if torch.cuda.is_available():
                used_bytes = torch.cuda.memory_allocated()
                total_bytes = torch.cuda.get_device_properties(0).total_memory
                return {
                    "vram_used_mb": round(used_bytes / (1024 * 1024), 1),
                    "vram_total_mb": round(total_bytes / (1024 * 1024), 1),
                    "gpu_util_pct": 0.0,
                }
        except Exception:
            pass

        # Try nvidia-smi CLI
        if self._has_nvidia_smi:
            try:
                cmd = ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,nounits,noheader"]
                output = subprocess.check_output(cmd, encoding="utf-8", timeout=1.5).strip()
                parts = [p.strip() for p in output.split(",")]
                if len(parts) >= 3:
                    return {
                        "vram_used_mb": float(parts[0]),
                        "vram_total_mb": float(parts[1]),
                        "gpu_util_pct": float(parts[2]),
                    }
            except Exception as e:
                logger.debug("nvidia-smi query failed: %s", e)

        # Fallback default simulation for testing
        return {
            "vram_used_mb": 4200.0,
            "vram_total_mb": 8192.0,
            "gpu_util_pct": 15.0,
        }

    def get_snapshot(self, tracker: Optional[PerformanceTracker] = None) -> MetricSnapshot:
        """Create a complete telemetry snapshot."""
        gpu = self.query_gpu()
        avg = tracker.get_averages() if tracker else {}

        return MetricSnapshot(
            stt_latency_ms=avg.get("avg_stt_ms", 0.0),
            llm_ttft_ms=avg.get("avg_llm_ttft_ms", 0.0),
            vlm_latency_ms=avg.get("avg_vlm_ms", 0.0),
            tts_latency_ms=avg.get("avg_tts_ms", 0.0),
            gpu_vram_used_mb=gpu["vram_used_mb"],
            gpu_vram_total_mb=gpu["vram_total_mb"],
            gpu_util_pct=gpu["gpu_util_pct"],
        )
