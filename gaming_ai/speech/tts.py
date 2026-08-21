"""Text-to-Speech synthesis with sentence-level streaming and interruptibility."""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import AsyncIterator, List, Optional
import pyttsx3

from gaming_ai.speech.audio_player import InterruptibleAudioPlayer

logger = logging.getLogger("gaming_ai.speech.tts")


class TextToSpeechEngine:
    """Text-to-speech engine supporting streamed sentence synthesis."""

    def __init__(
        self,
        engine_type: str = "pyttsx3",
        rate: int = 185,
        volume: float = 1.0,
        voice_index: int = 0,
        player: Optional[InterruptibleAudioPlayer] = None,
    ) -> None:
        self.engine_type = engine_type
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        self.player = player or InterruptibleAudioPlayer()
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        """Speak a single text utterance through the interruptible player."""
        clean_text = text.strip()
        if not clean_text:
            return

        def _synthesize_and_play() -> None:
            with self._lock:
                try:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", self.rate)
                    engine.setProperty("volume", self.volume)
                    voices = engine.getProperty("voices")
                    if voices and self.voice_index < len(voices):
                        engine.setProperty("voice", voices[self.voice_index].id)
                    engine.say(clean_text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as e:
                    logger.error("TTS synthesis error: %s", e)

        self.player.play(_synthesize_and_play)

    async def speak_stream(self, token_stream: AsyncIterator[str]) -> str:
        """
        Buffer streaming LLM tokens into complete sentences and speak each as soon as ready.

        Returns:
            The complete accumulated generated text.
        """
        buffer = ""
        full_text = ""
        sentence_delimiters = re.compile(r"([.!?\n]+)")

        async for token in token_stream:
            buffer += token
            full_text += token

            # Check if we have complete sentences in the buffer
            parts = sentence_delimiters.split(buffer)
            if len(parts) > 2:
                # We have at least one complete sentence: parts[0] + parts[1]
                sentence = parts[0] + parts[1]
                buffer = "".join(parts[2:])
                if sentence.strip():
                    self.speak(sentence.strip())

        # Speak any remaining text in buffer
        if buffer.strip():
            self.speak(buffer.strip())

        return full_text

    def interrupt(self) -> None:
        """Stop all speech immediately."""
        self.player.interrupt()
