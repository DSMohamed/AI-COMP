"""Asynchronous microphone audio capture with sounddevice and ring buffer."""

from __future__ import annotations

import collections
import logging
import queue
import threading
from typing import Callable, Generator, List, Optional
import numpy as np
import sounddevice as sd

from gaming_ai.speech.vad import VoiceActivityDetector

logger = logging.getLogger("gaming_ai.speech.microphone")


class MicrophoneStream:
    """Continuous microphone capture stream with VAD segmentation."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 512,
        device: Optional[int] = None,
        vad: Optional[VoiceActivityDetector] = None,
        on_speech_started: Optional[Callable[[], None]] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device = device
        self.vad = vad or VoiceActivityDetector(sample_rate=sample_rate)
        self.on_speech_started = on_speech_started

        self._stream: Optional[sd.InputStream] = None
        self._is_running = False
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._pre_speech_buffer: collections.deque[np.ndarray] = collections.deque(maxlen=15)  # ~0.5s pre-roll
        self._current_utterance: List[np.ndarray] = []

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
    ) -> None:
        """Callback invoked by PortAudio for each audio frame block."""
        if status:
            logger.warning("Microphone stream status: %s", status)
        if self._is_running:
            # Copy mono 1D float32 audio
            audio_copy = indata[:, 0].copy().astype(np.float32)
            self._audio_queue.put(audio_copy)

    def start(self) -> None:
        """Start recording from the microphone."""
        if self._is_running:
            return

        self._is_running = True
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            device=self.device,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        logger.info("Microphone stream started (Device: %s, Rate: %d Hz)", self.device or "Default", self.sample_rate)

    def stop(self) -> None:
        """Stop microphone recording and release audio stream."""
        self._is_running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.error("Error closing microphone stream: %s", e)
            finally:
                self._stream = None
        self.vad.reset()
        logger.info("Microphone stream stopped")

    def get_utterance(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """
        Poll audio queue and return a complete spoken utterance array when speech ends.
        
        Returns:
            1D numpy array of the complete utterance if speech finished, else None.
        """
        try:
            chunk = self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

        is_speaking, speech_started, speech_ended = self.vad.process_chunk(chunk)

        if speech_started:
            if self.on_speech_started:
                self.on_speech_started()
            # Prepend pre-roll buffer to prevent clipped initial consonants
            self._current_utterance = list(self._pre_speech_buffer)
            self._current_utterance.append(chunk)
        elif is_speaking:
            self._current_utterance.append(chunk)
        else:
            self._pre_speech_buffer.append(chunk)

        if speech_ended and len(self._current_utterance) > 0:
            full_audio = np.concatenate(self._current_utterance)
            self._current_utterance = []
            return full_audio

        return None
