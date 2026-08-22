"""Text-to-Speech synthesis supporting neural natural human voices (edge-tts) and local fallback."""

from __future__ import annotations

import asyncio
import io
import logging
import re
import threading
import time
from typing import AsyncIterator, List, Optional

import sounddevice as sd

try:
    import edge_tts
    import soundfile as sf
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

from gaming_ai.speech.audio_player import InterruptibleAudioPlayer

logger = logging.getLogger("gaming_ai.speech.tts")


class TextToSpeechEngine:
    """Text-to-speech engine supporting realistic neural voices and sentence-level streaming."""

    def __init__(
        self,
        engine_type: str = "edge-tts",
        voice: str = "en-US-ChristopherNeural",
        rate: int = 185,
        volume: float = 1.0,
        voice_index: int = 0,
        player: Optional[InterruptibleAudioPlayer] = None,
    ) -> None:
        self.engine_type = engine_type if HAS_EDGE_TTS else "pyttsx3"
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        self.player = player or InterruptibleAudioPlayer()
        self._lock = threading.Lock()

    def _synthesize_edge_tts(self, text: str) -> None:
        """Synthesize ultra-realistic neural speech via edge-tts."""
        async def _synth():
            try:
                # Rate offset string (e.g. "+5%", "-10%")
                rate_str = "+0%"
                if self.rate > 185:
                    pct = min(50, int(((self.rate - 185) / 185) * 100))
                    rate_str = f"+{pct}%"
                elif self.rate < 185:
                    pct = min(50, int(((185 - self.rate) / 185) * 100))
                    rate_str = f"-{pct}%"

                comm = edge_tts.Communicate(text=text, voice=self.voice, rate=rate_str)
                buf = bytearray()
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        buf.extend(chunk["data"])

                if buf and not self.player._interrupted.is_set():
                    data, sr = sf.read(io.BytesIO(buf), dtype="float32")
                    sd.play(data * self.volume, sr)
                    # Block thread until finished or interrupted
                    while sd.get_stream().active:
                        if self.player._interrupted.is_set():
                            sd.stop()
                            break
                        time.sleep(0.02)
            except Exception as e:
                logger.warning("edge-tts synthesis failed, falling back to pyttsx3: %s", e)
                self._synthesize_pyttsx3(text)

        # Run async synthesis inside sync player thread
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_synth())
        finally:
            loop.close()

    def _synthesize_pyttsx3(self, text: str) -> None:
        """Fallback local SAPI5 synthesis."""
        if not HAS_PYTTSX3:
            return
        with self._lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                voices = engine.getProperty("voices")
                if voices and self.voice_index < len(voices):
                    engine.setProperty("voice", voices[self.voice_index].id)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                logger.error("pyttsx3 synthesis error: %s", e)

    def speak(self, text: str) -> None:
        """Speak a single text utterance with instant interruptibility."""
        clean_text = text.strip()
        if not clean_text:
            return

        def _synthesize_and_play() -> None:
            if self.engine_type == "edge-tts" and HAS_EDGE_TTS:
                self._synthesize_edge_tts(clean_text)
            else:
                self._synthesize_pyttsx3(clean_text)

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
        try:
            sd.stop()
        except Exception:
            pass
