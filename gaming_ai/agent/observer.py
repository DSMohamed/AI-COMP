"""Asynchronous continuous observation loop coordinating screen, webcam, audio, and commentary."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Optional

from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.optimization.vram_guard import VRAMGuard, VRAMState
from gaming_ai.vision.event_detector import GameEvent

logger = logging.getLogger("gaming_ai.agent.observer")


class ContinuousObserver:
    """Non-blocking multimodal observation orchestrator for live gaming sessions."""

    def __init__(
        self,
        agent: GamingCompanionAgent,
        screen_interval: float = 2.0,
        webcam_interval: float = 4.0,
        on_event_detected: Optional[Callable[[GameEvent], None]] = None,
        vram_guard: Optional[VRAMGuard] = None,
    ) -> None:
        self.agent = agent
        self.screen_interval = screen_interval
        self.webcam_interval = webcam_interval
        self.on_event_detected = on_event_detected
        self.vram_guard = vram_guard or VRAMGuard()

        self._is_running = False
        self._tasks: list[asyncio.Task] = []
        self._user_speaking_flag = asyncio.Event()

    async def _screen_observation_worker(self) -> None:
        """Background worker periodically polling screen for significant game events."""
        logger.info("Screen observer worker started (Base Interval: %.1fs)", self.screen_interval)
        while self._is_running:
            try:
                # Check VRAM state to dynamically throttle if needed
                vram_state = self.vram_guard.check_vram()
                current_interval = self.vram_guard.get_suggested_screen_interval()

                # If player is currently speaking or TTS is active, pause autonomous screen checks
                if self._user_speaking_flag.is_set() or self.agent.player.is_speaking:
                    await asyncio.sleep(0.5)
                    continue

                if vram_state != VRAMState.CRITICAL:
                    event = await self.agent.process_gameplay_frame(force_analysis=False)
                    if event is not None and self.on_event_detected:
                        self.on_event_detected(event)

            except Exception as e:
                logger.error("Error in screen observation worker: %s", e)
                current_interval = self.screen_interval

            await asyncio.sleep(current_interval)

    async def _webcam_observation_worker(self) -> None:
        """Background worker periodically polling webcam for player emotional cues."""
        if self.agent.webcam is None:
            return

        logger.info("Webcam observer worker started (Interval: %.1fs)", self.webcam_interval)
        while self._is_running:
            try:
                if not self._user_speaking_flag.is_set():
                    await self.agent.observe_player()
            except Exception as e:
                logger.error("Error in webcam observation worker: %s", e)

            await asyncio.sleep(self.webcam_interval)

    async def _voice_input_worker(
        self,
        on_transcription: Optional[Callable[[str, float], None]] = None,
        on_response: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Dedicated high-priority worker handling direct microphone speech and interruption."""
        self.agent.start_microphone()
        logger.info("Voice listener active")

        try:
            while self._is_running:
                if self.agent.mic is None:
                    break

                audio_utterance = await asyncio.to_thread(self.agent.mic.get_utterance, 0.05)

                if audio_utterance is not None and len(audio_utterance) > 0:
                    self._user_speaking_flag.set()
                    try:
                        text, latency = await asyncio.to_thread(self.agent.stt.transcribe, audio_utterance)
                        if text and len(text.strip()) > 1:
                            if on_transcription:
                                on_transcription(text, latency)

                            # Directly process turn and speak safely
                            try:
                                response = await self.agent.respond_to_text(text, speak=True)
                                if on_response:
                                    on_response(response)
                            except Exception as resp_err:
                                logger.error("Error processing voice turn: %s", resp_err)
                    finally:
                        self._user_speaking_flag.clear()

                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        finally:
            self.agent.stop_microphone()

    async def start(
        self,
        on_transcription: Optional[Callable[[str, float], None]] = None,
        on_response: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Launch all observation workers concurrently."""
        if self._is_running:
            return

        self._is_running = True
        logger.info("🎮 Starting Continuous Observation Loop...")

        # Spawn decoupled worker tasks
        self._tasks = [
            asyncio.create_task(self._voice_input_worker(on_transcription, on_response)),
            asyncio.create_task(self._screen_observation_worker()),
            asyncio.create_task(self._webcam_observation_worker()),
        ]

        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop all background workers cleanly."""
        if not self._is_running:
            return

        self._is_running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()

        self.agent.stop_microphone()
        self.agent.player.stop()
        if self.agent.webcam is not None:
            self.agent.webcam.stop()
        self.agent.screen_capture.close()
        logger.info("Continuous Observation Loop stopped cleanly")

    @property
    def is_running(self) -> bool:
        return self._is_running
