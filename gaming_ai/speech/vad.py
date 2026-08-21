"""Voice Activity Detection (VAD) module with adaptive energy and timing tracking."""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("gaming_ai.speech.vad")


class VoiceActivityDetector:
    """Detects active speech in audio chunks with adaptive noise calibration."""

    def __init__(
        self,
        energy_threshold: float = 0.015,
        silence_duration_threshold: float = 0.8,
        min_speech_duration: float = 0.3,
        sample_rate: int = 16000,
    ) -> None:
        self.energy_threshold = energy_threshold
        self.silence_duration_threshold = silence_duration_threshold
        self.min_speech_duration = min_speech_duration
        self.sample_rate = sample_rate

        self._in_speech: bool = False
        self._speech_start_time: Optional[float] = None
        self._last_speech_time: Optional[float] = None
        self._noise_floor: float = 0.005

    def calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """Calculate Root Mean Square (RMS) energy of a 1D audio array."""
        if len(audio_chunk) == 0:
            return 0.0
        # Ensure float32 normalized between -1.0 and 1.0
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)
        rms = np.sqrt(np.mean(audio_chunk**2))
        return float(rms)

    def process_chunk(self, audio_chunk: np.ndarray) -> Tuple[bool, bool, bool]:
        """
        Process an audio chunk and update speech state.

        Returns:
            Tuple of (is_currently_speaking, speech_started, speech_ended)
        """
        energy = self.calculate_energy(audio_chunk)
        now = time.time()

        # Dynamic ambient noise adaptation during silence
        if not self._in_speech and energy < self.energy_threshold:
            self._noise_floor = 0.95 * self._noise_floor + 0.05 * energy

        effective_threshold = max(self.energy_threshold, self._noise_floor * 2.5)
        is_speech_frame = energy >= effective_threshold

        speech_started = False
        speech_ended = False

        if is_speech_frame:
            self._last_speech_time = now
            if not self._in_speech:
                self._in_speech = True
                self._speech_start_time = now
                speech_started = True
                logger.debug("Speech onset detected (RMS: %.4f, threshold: %.4f)", energy, effective_threshold)
        else:
            if self._in_speech and self._last_speech_time is not None:
                silence_elapsed = now - self._last_speech_time
                if silence_elapsed >= self.silence_duration_threshold:
                    total_speech_duration = (self._last_speech_time - (self._speech_start_time or now))
                    self._in_speech = False
                    self._speech_start_time = None
                    self._last_speech_time = None

                    if total_speech_duration >= self.min_speech_duration:
                        speech_ended = True
                        logger.debug("Speech endpoint detected (duration: %.2fs)", total_speech_duration)

        return self._in_speech, speech_started, speech_ended

    def reset(self) -> None:
        """Reset internal speech state."""
        self._in_speech = False
        self._speech_start_time = None
        self._last_speech_time = None
