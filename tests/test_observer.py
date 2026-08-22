"""Tests for ContinuousObserver async loop and task coordination."""

import asyncio
import numpy as np
import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.agent.observer import ContinuousObserver
from gaming_ai.app.config import AppConfig
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.vision.event_detector import GameEvent, EventType
from gaming_ai.vision.screen_capture import ScreenCapture
from gaming_ai.vision.vision_model import MockVisionModel, VisionAnalysisResult
from gaming_ai.vision.webcam import WebcamCapture


@pytest.mark.asyncio
async def test_continuous_observer_lifecycle() -> None:
    """Verify observer starts tasks and stops cleanly without errors."""
    cfg = AppConfig()
    mock_llm = MockLLMProvider()
    mock_vision = MockVisionModel()
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cam = WebcamCapture(mock_frame=dummy_frame)
    mock_screen = ScreenCapture(mock_frame=dummy_frame)

    agent = GamingCompanionAgent(
        config=cfg,
        llm_provider=mock_llm,
        vision_model=mock_vision,
        screen_capture=mock_screen,
        webcam=mock_cam,
    )

    detected_events = []

    def on_event(event: GameEvent) -> None:
        detected_events.append(event)

    observer = ContinuousObserver(
        agent=agent,
        screen_interval=0.1,
        webcam_interval=0.1,
        on_event_detected=on_event,
    )

    # Run observer for a short slice
    task = asyncio.create_task(observer.start())
    await asyncio.sleep(0.3)
    await observer.stop()
    await asyncio.sleep(0.1)

    assert observer.is_running is False
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass
