"""Tests for Voice Activity Detection and energy calculation."""

import numpy as np
import pytest
from gaming_ai.speech.vad import VoiceActivityDetector


def test_vad_silence_detection() -> None:
    """Verify silence does not trigger speech state."""
    vad = VoiceActivityDetector(energy_threshold=0.02)
    silent_chunk = np.zeros(512, dtype=np.float32)

    is_speaking, speech_started, speech_ended = vad.process_chunk(silent_chunk)
    assert not is_speaking
    assert not speech_started
    assert not speech_ended


def test_vad_speech_detection() -> None:
    """Verify high energy audio triggers speech onset."""
    vad = VoiceActivityDetector(energy_threshold=0.01)
    # Generate high amplitude sine wave simulating voice
    t = np.linspace(0, 0.05, 512, endpoint=False)
    loud_chunk = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    is_speaking, speech_started, speech_ended = vad.process_chunk(loud_chunk)
    assert is_speaking is True
    assert speech_started is True
