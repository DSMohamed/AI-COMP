"""Central Gaming Companion Agent orchestrator."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator, Callable, Optional

from gaming_ai.agent.context import ContextEngine
from gaming_ai.agent.personality import PersonalityEngine
from gaming_ai.app.config import AppConfig, get_config
from gaming_ai.models.ollama import OllamaProvider
from gaming_ai.models.provider import BaseLLMProvider
from gaming_ai.speech.audio_player import InterruptibleAudioPlayer
from gaming_ai.speech.microphone import MicrophoneStream
from gaming_ai.speech.stt import SpeechToText
from gaming_ai.speech.tts import TextToSpeechEngine

logger = logging.getLogger("gaming_ai.agent")


class GamingCompanionAgent:
    """Orchestrates perception, reasoning, speech, and interruption handling."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeechEngine] = None,
    ) -> None:
        self.config = config or get_config()
        self.personality = PersonalityEngine(self.config.personality)
        self.context = ContextEngine(
            personality_engine=self.personality,
            history_limit=self.config.memory.short_term_history_limit,
        )

        # Initialize LLM Provider
        self.llm = llm_provider or OllamaProvider(
            model_name=self.config.ai.model,
            host=self.config.ai.host,
            timeout=self.config.ai.request_timeout,
        )

        # Audio Player & TTS
        self.player = InterruptibleAudioPlayer()
        self.tts = tts or TextToSpeechEngine(
            engine_type=self.config.tts.engine,
            rate=self.config.tts.rate,
            volume=self.config.tts.volume,
            voice_index=self.config.tts.voice_index,
            player=self.player,
        )

        # STT & Microphone
        self.stt = stt or SpeechToText(
            model_size=self.config.speech.stt_model,
            device=self.config.speech.device,
            compute_type=self.config.speech.compute_type,
        )
        self.mic: Optional[MicrophoneStream] = None

    def _on_speech_started(self) -> None:
        """Callback invoked immediately when user begins speaking into the microphone."""
        if self.config.tts.interrupt_on_speech:
            self.tts.interrupt()

    def start_microphone(self) -> None:
        """Start listening to microphone input."""
        if self.mic is None:
            self.mic = MicrophoneStream(
                sample_rate=self.config.speech.sample_rate,
                device=self.config.speech.input_device,
                on_speech_started=self._on_speech_started,
            )
        self.mic.start()

    def stop_microphone(self) -> None:
        """Stop microphone capture."""
        if self.mic is not None:
            self.mic.stop()
            self.mic = None

    async def respond_to_text(self, user_text: str, speak: bool = True) -> str:
        """
        Process a text query from the user, stream LLM response, and speak it.

        Returns:
            The complete response text from the companion.
        """
        start_time = time.perf_counter()
        logger.info("Player: '%s'", user_text)

        messages = self.context.build_context(current_user_input=user_text)

        # Stream response from LLM
        stream_gen = self.llm.generate_stream(
            messages=messages,
            temperature=self.config.ai.temperature,
            max_tokens=self.config.ai.max_tokens,
        )

        if speak:
            response_text = await self.tts.speak_stream(stream_gen)
        else:
            chunks = []
            async for chunk in stream_gen:
                chunks.append(chunk)
            response_text = "".join(chunks)

        total_time = (time.perf_counter() - start_time) * 1000.0
        logger.info("Companion (%s): '%s' (Latency: %.1fms)", self.config.personality.name, response_text, total_time)

        # Persist turn in short-term history
        self.context.add_user_message(user_text)
        self.context.add_assistant_message(response_text)

        return response_text

    async def run_voice_loop(
        self,
        on_transcription: Optional[Callable[[str, float], None]] = None,
        on_response: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Continuous asynchronous voice observation loop.
        """
        self.start_microphone()
        logger.info("Voice companion active. Speak into your microphone...")

        try:
            while True:
                # Poll microphone stream for complete spoken utterance (non-blocking in thread)
                audio_utterance = await asyncio.to_thread(self.mic.get_utterance, 0.1)

                if audio_utterance is not None and len(audio_utterance) > 0:
                    # Transcribe with faster-whisper
                    text, stt_latency = await asyncio.to_thread(self.stt.transcribe, audio_utterance)
                    if text and len(text.strip()) > 1:
                        if on_transcription:
                            on_transcription(text, stt_latency)

                        # Generate response & speak
                        response = await self.respond_to_text(text, speak=True)
                        if on_response:
                            on_response(response)

                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            logger.info("Voice loop cancelled")
        finally:
            self.stop_microphone()
            self.player.stop()
