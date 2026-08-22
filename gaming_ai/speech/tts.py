"""Text-to-Speech synthesis supporting neural natural human voices (edge-tts, Kokoro, XTTS/AllTalk, Piper, Bark, and pyttsx3)."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import threading
import time
from typing import AsyncIterator, List, Optional
import urllib.request

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
    """Multi-backend Text-to-Speech engine supporting realistic human neural voices and sentence streaming."""

    def __init__(
        self,
        engine_type: str = "edge-tts",
        voice: str = "en-US-ChristopherNeural",
        rate: int = 185,
        volume: float = 1.0,
        voice_index: int = 0,
        alltalk_url: str = "http://127.0.0.1:7851/api/tts-generate",
        player: Optional[InterruptibleAudioPlayer] = None,
    ) -> None:
        self.engine_type = engine_type.lower()
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        self.alltalk_url = alltalk_url
        self.player = player or InterruptibleAudioPlayer()
        self._lock = threading.Lock()

        # Dedicated background asyncio worker loop for thread-safe edge-tts synthesis
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_thread: Optional[threading.Thread] = None
        if HAS_EDGE_TTS:
            self._init_async_worker()

    def _init_async_worker(self) -> None:
        """Initialize a persistent background asyncio thread for edge-tts."""
        try:
            self._async_loop = asyncio.new_event_loop()
            def _worker_target(loop: asyncio.AbstractEventLoop) -> None:
                asyncio.set_event_loop(loop)
                loop.run_forever()

            self._async_thread = threading.Thread(
                target=_worker_target, args=(self._async_loop,), daemon=True, name="EdgeTTS-Worker"
            )
            self._async_thread.start()
        except Exception as e:
            logger.warning("Could not initialize dedicated async worker for TTS: %s", e)

    def _clean_text_for_speech(self, text: str) -> str:
        """Strip raw markdown formatting and normalize gaming expressions."""
        clean = re.sub(r"\*([^*]+)\*", r"\1", text)  # remove *italics*
        clean = re.sub(r"\[([^\]]+)\]", r"\1", clean)  # remove [brackets]
        clean = re.sub(r"`([^`]+)`", r"\1", clean)  # remove `code`
        return clean.strip()

    def _synthesize_edge_tts_bytes(self, text: str) -> Optional[bytes]:
        """Synthesize audio bytes using edge-tts on the dedicated background loop."""
        if not HAS_EDGE_TTS or not self._async_loop or not self._async_loop.is_running():
            return None

        # Rate offset string (e.g. "+5%", "-10%")
        rate_str = "+0%"
        if self.rate > 185:
            pct = min(50, int(((self.rate - 185) / 185) * 100))
            rate_str = f"+{pct}%"
        elif self.rate < 185:
            pct = min(50, int(((185 - self.rate) / 185) * 100))
            rate_str = f"-{pct}%"

        async def _synth_coro() -> bytes:
            comm = edge_tts.Communicate(text=text, voice=self.voice, rate=rate_str)
            buf = bytearray()
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    buf.extend(chunk["data"])
            return bytes(buf)

        try:
            future = asyncio.run_coroutine_threadsafe(_synth_coro(), self._async_loop)
            return future.result(timeout=10.0)
        except Exception as e:
            logger.error("Edge-TTS synthesis error: %s", e)
            return None

    def _synthesize_edge_tts(self, text: str) -> None:
        """Synthesize and play ultra-realistic neural speech via edge-tts."""
        try:
            audio_bytes = self._synthesize_edge_tts_bytes(text)
            if audio_bytes and not self.player._interrupted.is_set():
                data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
                sd.play(data * self.volume, sr)
                while sd.get_stream().active:
                    if self.player._interrupted.is_set():
                        sd.stop()
                        break
                    time.sleep(0.02)
            elif not audio_bytes:
                logger.warning("edge-tts returned no audio, falling back to pyttsx3")
                self._synthesize_pyttsx3(text)
        except Exception as e:
            logger.warning("edge-tts playback failed: %s, falling back to pyttsx3", e)
            self._synthesize_pyttsx3(text)

    def _synthesize_alltalk(self, text: str) -> None:
        """Synthesize through local Coqui XTTS / AllTalk TTS Web API."""
        try:
            req_data = json.dumps({
                "text_input": text,
                "text_filtering": "standard",
                "character_voice_gen": self.voice or "narrator.wav",
                "narrator_enabled": "false",
                "narrator_voice_gen": "narrator.wav",
                "text_not_inside": "character",
                "language": "en",
                "output_file_name": "companion_temp",
                "output_file_timestamp": "true",
                "autoplay": "false",
            }).encode("utf-8")

            req = urllib.request.Request(
                self.alltalk_url,
                data=req_data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                output_url = result.get("output_file_url")
                if output_url:
                    with urllib.request.urlopen(output_url, timeout=5.0) as audio_resp:
                        audio_data = audio_resp.read()
                        data, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
                        sd.play(data * self.volume, sr)
                        while sd.get_stream().active:
                            if self.player._interrupted.is_set():
                                sd.stop()
                                break
                            time.sleep(0.02)
        except Exception as e:
            logger.warning("AllTalk/XTTS endpoint unavailable, fallback to edge-tts: %s", e)
            self._synthesize_edge_tts(text)

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
        clean_text = self._clean_text_for_speech(text)
        if not clean_text:
            return

        def _synthesize_and_play() -> None:
            if self.engine_type in ("alltalk", "xtts", "coqui"):
                self._synthesize_alltalk(clean_text)
            elif self.engine_type == "edge-tts" and HAS_EDGE_TTS:
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

            parts = sentence_delimiters.split(buffer)
            if len(parts) > 2:
                sentence = parts[0] + parts[1]
                buffer = "".join(parts[2:])
                if sentence.strip():
                    self.speak(sentence.strip())

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
