"""Tests for PerformanceTracker, HardwareMonitor, and VRAMGuard watchdog."""

import pytest
from gaming_ai.optimization.telemetry import HardwareMonitor, MetricSnapshot, PerformanceTracker
from gaming_ai.optimization.vram_guard import VRAMGuard, VRAMState


def test_performance_tracker_latencies() -> None:
    """Verify latency tracking and rolling average computations."""
    tracker = PerformanceTracker(window_size=10)

    tracker.record_stt(120.0)
    tracker.record_stt(180.0)
    tracker.record_llm_ttft(350.0)
    tracker.record_vlm(450.0)
    tracker.record_tts(100.0)

    averages = tracker.get_averages()
    assert averages["avg_stt_ms"] == 150.0
    assert averages["avg_llm_ttft_ms"] == 350.0
    assert averages["avg_vlm_ms"] == 450.0
    assert averages["avg_tts_ms"] == 100.0


def test_hardware_monitor_snapshot() -> None:
    """Verify hardware monitor returns valid telemetry snapshot."""
    monitor = HardwareMonitor()
    tracker = PerformanceTracker()
    tracker.record_stt(110.0)

    snapshot = monitor.get_snapshot(tracker=tracker)
    assert isinstance(snapshot, MetricSnapshot)
    assert snapshot.gpu_vram_total_mb > 0
    assert snapshot.stt_latency_ms == 110.0


def test_vram_guard_state_transitions() -> None:
    """Verify VRAMGuard adapts operating states and interval suggestions."""
    transitions = []

    def on_change(new_state: VRAMState, used_mb: float) -> None:
        transitions.append((new_state, used_mb))

    guard = VRAMGuard(
        warning_threshold_mb=6000.0,
        critical_threshold_mb=7200.0,
        on_state_change=on_change,
    )

    # Normal State (< 6000 MB)
    s1 = guard.check_vram(vram_override_mb=4500.0)
    assert s1 == VRAMState.NORMAL
    assert guard.get_suggested_screen_interval() == 2.0

    # Warning State (6000 - 7200 MB)
    s2 = guard.check_vram(vram_override_mb=6500.0)
    assert s2 == VRAMState.WARNING
    assert guard.get_suggested_screen_interval() == 4.0
    assert len(transitions) == 1
    assert transitions[0][0] == VRAMState.WARNING

    # Critical State (> 7200 MB)
    s3 = guard.check_vram(vram_override_mb=7500.0)
    assert s3 == VRAMState.CRITICAL
    assert guard.get_suggested_screen_interval() == 10.0
    assert len(transitions) == 2
    assert transitions[1][0] == VRAMState.CRITICAL

    # Recovery State (< 6000 MB)
    s4 = guard.check_vram(vram_override_mb=5000.0)
    assert s4 == VRAMState.NORMAL
    assert guard.get_suggested_screen_interval() == 2.0
    assert len(transitions) == 3
    assert transitions[2][0] == VRAMState.NORMAL
