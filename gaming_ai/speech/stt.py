"""Speech-to-Text transcriber using faster-whisper (CTranslate2) with hallucination filtering."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("gaming_ai.speech.stt")


class SpeechToText:
    """Local STT engine powered by faster-whisper with hallucination suppression."""

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

    def _is_hallucination(self, text: str) -> bool:
        """Detect and discard common Whisper repetitive silence hallucinations."""
        clean = text.strip().lower()
        if not clean or len(clean) < 2:
            return True

        # Check for single word repetition (e.g. "Okay. Okay. Okay. Okay." or "you you you")
        words = re.findall(r"\b\w+\b", clean)
        if len(words) >= 4:
            unique_words = set(words)
            if len(unique_words) <= 2:  # 4+ words but only 1 or 2 unique words
                return True

        # Common Whisper phantom subtitles during silence
        phantom_phrases = [
            "thank you for watching",
            "thanks for watching",
            "please subscribe",
            "like and subscribe",
            "subtitles by",
            "translated by",
        ]
        if any(p in clean for p in phantom_phrases):
            return True

        return False

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
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text_parts = [segment.text.strip() for segment in segments]
        transcription = " ".join(text_parts).strip()
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if self._is_hallucination(transcription):
            logger.debug("Filtered hallucination: '%s'", transcription)
            return "", latency_ms

        logger.debug("Transcribed in %.2fms: '%s'", latency_ms, transcription)
        return transcription, latency_ms
