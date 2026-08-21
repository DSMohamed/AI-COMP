"""Tests for faster-whisper SpeechToText transcriber."""

import numpy as np
import pytest
from gaming_ai.speech.stt import SpeechToText


def test_stt_transcription_silence() -> None:
    """Verify STT processes silence cleanly."""
    stt = SpeechToText(model_size="base.en", device="cpu", compute_type="int8")
    dummy_audio = np.zeros(16000, dtype=np.float32)
    text, latency = stt.transcribe(dummy_audio)
    assert isinstance(text, str)
    assert latency > 0.0
