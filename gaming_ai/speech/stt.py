"""Speech-to-Text transcriber using faster-whisper (CTranslate2)."""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("gaming_ai.speech.stt")


class SpeechToText:
    """Local STT engine powered by faster-whisper."""

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "auto",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self) -> None:
        """Load the faster-whisper model into memory."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        target_device = self.device
        if target_device == "auto":
            try:
                import torch
                target_device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                target_device = "cpu"

        logger.info(
            "Loading faster-whisper model '%s' on %s (%s)...",
            self.model_size,
            target_device,
            self.compute_type,
        )
        try:
            self._model = WhisperModel(
                self.model_size,
                device=target_device,
                compute_type=self.compute_type,
            )
            logger.info("faster-whisper model loaded successfully")
        except Exception as e:
            logger.warning("Failed to load on %s: %s. Falling back to CPU int8.", target_device, e)
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )

    def transcribe(self, audio: np.ndarray, language: str = "en") -> Tuple[str, float]:
        """
        Transcribe a 1D audio array (16kHz float32).

        Returns:
            Tuple of (transcribed_text, latency_ms)
        """
        self._load_model()
        if len(audio) == 0:
            return "", 0.0

        start_time = time.perf_counter()
        segments, info = self._model.transcribe(
            audio,
            beam_size=3,
            language=language,
            condition_on_previous_text=False,
            temperature=0.0,
        )

        text_parts = [segment.text.strip() for segment in segments]
        transcription = " ".join(text_parts).strip()
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        logger.debug("Transcribed in %.2fms: '%s'", latency_ms, transcription)
        return transcription, latency_ms
