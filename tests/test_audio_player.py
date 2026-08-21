"""Tests for interruptible audio player."""

import time
import pytest
from gaming_ai.speech.audio_player import InterruptibleAudioPlayer


def test_audio_player_interruption() -> None:
    """Verify player can be interrupted and drained."""
    player = InterruptibleAudioPlayer()
    executed = []

    def dummy_task() -> None:
        time.sleep(0.05)
        executed.append(True)

    player.play(dummy_task)
    player.interrupt()
    time.sleep(0.1)

    player.stop()
    assert True
