"""Thread-safe non-blocking audio player with instant interruption support."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("gaming_ai.speech.audio_player")


class InterruptibleAudioPlayer:
    """Manages audio playback queue and handles instant speech interruptions."""

    def __init__(self) -> None:
        self._speech_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self._is_running = True
        self._is_speaking = False
        self._interrupted = threading.Event()
        self._worker_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._worker_thread.start()

    def _playback_loop(self) -> None:
        """Background worker consuming audio tasks from queue."""
        while self._is_running:
            try:
                task = self._speech_queue.get(timeout=0.05)
            except queue.Empty:
                continue

            if self._interrupted.is_set():
                self._speech_queue.task_done()
                continue

            self._is_speaking = True
            try:
                task()
            except Exception as e:
                logger.error("Audio playback error: %s", e)
            finally:
                self._is_speaking = False
                self._speech_queue.task_done()

    def play(self, play_fn: Callable[[], None]) -> None:
        """Enqueue a speech playback function."""
        self._interrupted.clear()
        self._speech_queue.put(play_fn)

    def interrupt(self) -> None:
        """Immediately interrupt audio playback and drain pending speech."""
        if not self._is_speaking and self._speech_queue.empty():
            return

        logger.info("⚡ Speech interruption triggered: Halting audio playback")
        self._interrupted.set()

        # Clear remaining queue items
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except (queue.Empty, ValueError):
                break

    @property
    def is_speaking(self) -> bool:
        """Check if audio is currently playing."""
        return self._is_speaking

    def stop(self) -> None:
        """Stop worker thread cleanly."""
        self._is_running = False
        self.interrupt()
