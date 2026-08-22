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
from gaming_ai.agent.decision import DecisionEngine
from gaming_ai.memory.manager import MemoryManager
from gaming_ai.rag.retriever import RAGRetriever
from gaming_ai.tools.builtin import (
    AppLauncherTool,
    BrowserGuideTool,
    ClipboardTool,
    NoteTakingTool,
    ScreenshotTool,
    TimeDateTool,
    TimerTool,
    VolumeControlTool,
)
from gaming_ai.tools.registry import ToolRegistry
from gaming_ai.vision.event_detector import EventDetector, GameEvent
from gaming_ai.vision.frame_analyzer import FrameAnalyzer
from gaming_ai.vision.screen_capture import ScreenCapture
from gaming_ai.vision.vision_model import BaseVisionModel, OllamaVisionModel, VisionAnalysisResult
from gaming_ai.vision.webcam import WebcamCapture
from gaming_ai.vision.player_analyzer import PlayerAnalyzer, PlayerReaction

logger = logging.getLogger("gaming_ai.agent")


class GamingCompanionAgent:
    """Orchestrates perception (audio + screen + webcam), tools, RAG, memory, and speech."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeechEngine] = None,
        vision_model: Optional[BaseVisionModel] = None,
        screen_capture: Optional[ScreenCapture] = None,
        webcam: Optional[WebcamCapture] = None,
        player_analyzer: Optional[PlayerAnalyzer] = None,
        event_detector: Optional[EventDetector] = None,
        frame_analyzer: Optional[FrameAnalyzer] = None,
        decision_engine: Optional[DecisionEngine] = None,
        retriever: Optional[RAGRetriever] = None,
        memory: Optional[MemoryManager] = None,
        tools: Optional[ToolRegistry] = None,
    ) -> None:
        self.config = config or get_config()
        self.personality = PersonalityEngine(self.config.personality)
        self.context = ContextEngine(
            personality_engine=self.personality,
            history_limit=self.config.memory.short_term_history_limit,
        )

        # Multi-layer Persistent Memory Manager (Phase 7)
        self.memory = memory or (MemoryManager() if self.config.memory.enabled else None)
        if self.memory and not self.memory.current_session:
            self.memory.start_session(game="general")

        # Sandboxed Computer Control Tools (Phase 9 & Daily Productivity)
        self.tools = tools or ToolRegistry(
            enabled=self.config.tools.enabled,
            allow_privileged=self.config.tools.allow_privileged,
        )
        # Register default tools
        self.tools.register(ScreenshotTool())
        self.tools.register(TimerTool())
        self.tools.register(BrowserGuideTool())
        self.tools.register(AppLauncherTool())
        self.tools.register(NoteTakingTool())
        self.tools.register(TimeDateTool())
        self.tools.register(VolumeControlTool())
        self.tools.register(ClipboardTool())

        # Initialize LLM Provider
        self.llm = llm_provider or OllamaProvider(
            model_name=self.config.ai.model,
            host=self.config.ai.host,
            timeout=self.config.ai.request_timeout,
        )

        # Knowledge Base / RAG Retriever
        self.retriever = retriever

        # Audio Player & TTS
        self.player = InterruptibleAudioPlayer()
        self.tts = tts or TextToSpeechEngine(
            engine_type=self.config.tts.engine,
            voice=self.config.tts.voice,
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

        # Vision Subsystem
        self.screen_capture = screen_capture or ScreenCapture()
        self.frame_analyzer = frame_analyzer or FrameAnalyzer()
        self.vision_model = vision_model or OllamaVisionModel(
            model_name=self.config.vision.model if self.config.vision.model != "qwen2-vl:2b" else "llava:latest",
            host=self.config.ai.host,
            timeout=45.0,
        )

        # Event Detection & Decision Engine (Phases 4 & 5)
        self.event_detector = event_detector or EventDetector()
        self.decision_engine = decision_engine or DecisionEngine(
            personality_config=self.config.personality
        )

        # Webcam Subsystem (Optional / In-Memory only)
        self.webcam = webcam or (WebcamCapture() if self.config.vision.webcam_enabled else None)
        self.player_analyzer = player_analyzer or PlayerAnalyzer()

    def _on_speech_started(self) -> None:
        """Callback invoked immediately when user begins speaking into the microphone."""
        if self.config.tts.interrupt_on_speech:
            self.tts.interrupt()
        # Direct user speech resets autonomous cooldown
        self.decision_engine.reset_cooldown()

    async def observe_player(self) -> Optional[PlayerReaction]:
        """Capture webcam and analyze player reaction in-memory."""
        if self.webcam is None:
            return None
        frame = await asyncio.to_thread(self.webcam.capture_frame)
        reaction = await asyncio.to_thread(self.player_analyzer.analyze_frame, frame)
        self.context.update_webcam_context(reaction.summary)
        logger.info("Player Reaction: %s (Emotion: %s, Engagement: %s)", reaction.summary, reaction.emotion, reaction.engagement)
        return reaction

    async def process_gameplay_frame(self, force_analysis: bool = False) -> Optional[GameEvent]:
        """
        Process current game screen, detect events, and decide whether to speak.
        """
        frame_rgb = await asyncio.to_thread(self.screen_capture.capture_frame_numpy)
        has_changed, delta = await asyncio.to_thread(self.frame_analyzer.has_significant_change, frame_rgb)

        if not has_changed and not force_analysis:
            return None

        # Run structured VLM analysis
        vision_result = await self.observe_screen(structured=True)
        event = self.event_detector.detect_event(vision_result, frame_delta=delta)

        # Store event in persistent memory
        if self.memory:
            try:
                self.memory.record_event(event)
            except Exception as e:
                logger.debug("Failed to record event to memory: %s", e)

        # Evaluate attention and commentary decision
        if self.decision_engine.should_comment(event, force=force_analysis):
            prompt = (
                f"React naturally and spontaneously to this in-game event: [{event.event_type.value.upper()}]. "
                f"Situation: {event.description}."
            )
            # Generate autonomous comment
            await self.respond_to_text(prompt, speak=True, include_screen=False)
            self.decision_engine.record_speech()

        return event

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

    def _is_visual_query(self, text: str) -> bool:
        """Check if user query is asking about the current screen or game view."""
        visual_triggers = [
            "what is happening",
            "what's happening",
            "what do you see",
            "look at this",
            "look at my screen",
            "what's on my screen",
            "what is on my screen",
            "can you see",
            "check my screen",
            "what is that",
            "am i cooked",
            "where am i",
        ]
        lower = text.lower()
        return any(t in lower for t in visual_triggers)

    async def _handle_tool_intent(self, text: str) -> Optional[str]:
        """Detect and execute tool commands if user requests them."""
        lower = text.lower()
        if not self.tools or not self.tools.enabled:
            return None

        # Time & Date intent
        if any(w in lower for w in ("what time", "current time", "what's the date", "what is the date", "what day is")):
            res = await self.tools.execute("get_time")
            return res.output if res.success else res.error

        # Note taking intent
        if "take a note" in lower or "note that" in lower or "write this down" in lower:
            note_content = text
            for prefix in ("take a note that", "take a note:", "take a note", "note that", "write this down:"):
                if prefix in lower:
                    idx = lower.find(prefix) + len(prefix)
                    note_content = text[idx:].strip()
                    break
            res = await self.tools.execute("take_note", note=note_content)
            return res.output if res.success else res.error

        # App Launching intent
        if "open" in lower or "launch" in lower or "start" in lower:
            for app in ("notepad", "calculator", "calc", "code", "vscode", "spotify", "chrome", "edge", "terminal"):
                if app in lower:
                    res = await self.tools.execute("launch_app", app_name=app)
                    return res.output if res.success else res.error

        # Screenshot intent
        if any(w in lower for w in ("take a screenshot", "take screenshot", "grab screenshot", "screenshot that", "clip that")):
            res = await self.tools.execute("take_screenshot")
            return res.output if res.success else res.error

        # Timer intent
        if "timer" in lower and ("set" in lower or "start" in lower):
            import re
            match = re.search(r"(\d+)\s*(sec|second|min|minute)", lower)
            seconds = 60
            if match:
                val, unit = int(match.group(1)), match.group(2)
                seconds = val * 60 if "min" in unit else val
            res = await self.tools.execute("set_timer", seconds=seconds, label="Alert")
            return res.output if res.success else res.error

        # Volume intent
        if "volume" in lower and ("set" in lower or "change" in lower):
            import re
            match = re.search(r"(\d+)", lower)
            if match:
                vol = int(match.group(1))
                res = await self.tools.execute("set_volume", volume=vol)
                return res.output if res.success else res.error

        return None

    async def observe_screen(
        self, custom_prompt: Optional[str] = None, structured: bool = True
    ) -> VisionAnalysisResult:
        """Capture the screen and analyze it with the vision-language model."""
        start_time = time.perf_counter()
        img_b64 = await asyncio.to_thread(self.screen_capture.capture_base64)
        result = await self.vision_model.analyze(
            image_base64=img_b64, prompt=custom_prompt, structured=structured
        )
        self.context.update_vision_context(
            f"Scene: {result.scene}. State: {result.player_state}. Description: {result.description}"
        )
        total_time = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "Screen Observation: '%s' (Scene: %s, Latency: %.1fms)",
            result.description,
            result.scene,
            total_time,
        )
        return result

    async def respond_to_text(
        self, user_text: str, speak: bool = True, include_screen: Optional[bool] = None
    ) -> str:
        """
        Process a text query from the user, stream LLM response, and speak it.

        Returns:
            The complete response text from the companion.
        """
        start_time = time.perf_counter()
        logger.info("Player: '%s'", user_text)

        # Automatically observe screen if query is visual or requested
        should_observe = include_screen if include_screen is not None else self._is_visual_query(user_text)
        if should_observe:
            try:
                await self.observe_screen()
            except Exception as e:
                logger.warning("Screen observation failed: %s", e)

        # Retrieve relevant RAG knowledge if available
        if self.retriever:
            try:
                rag_context = await self.retriever.retrieve_formatted_context(
                    query=user_text, game=self.context.current_game
                )
                self.context.update_rag_context(rag_context)
            except Exception as e:
                logger.warning("RAG retrieval failed: %s", e)

        # Retrieve long-term memory block if available
        if self.memory:
            try:
                mem_block = self.memory.get_prompt_memory_block(game=self.context.current_game)
                self.context.update_memory_context(mem_block)
            except Exception as e:
                logger.warning("Memory retrieval failed: %s", e)

        # Check for tool intent (e.g. screenshot, timer, browser guide)
        tool_feedback = await self._handle_tool_intent(user_text)
        if tool_feedback:
            user_text += f"\n[SYSTEM: Executed tool action: {tool_feedback}]"

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

        # Persist turn in short-term history and SQLite database
        self.context.add_user_message(user_text)
        self.context.add_assistant_message(response_text)

        if self.memory:
            try:
                self.memory.record_turn("user", user_text)
                self.memory.record_turn("assistant", response_text)
            except Exception as e:
                logger.debug("Failed to persist turns to memory: %s", e)

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
