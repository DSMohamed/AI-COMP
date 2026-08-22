"""Tests for ScreenCapture, FrameAnalyzer, and Vision Model pipeline."""

import numpy as np
import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.vision.frame_analyzer import FrameAnalyzer
from gaming_ai.vision.screen_capture import ScreenCapture
from gaming_ai.vision.vision_model import MockVisionModel, VisionAnalysisResult


def test_screen_capture_frame() -> None:
    """Verify screen capture returns valid image dimensions and base64 string."""
    sc = ScreenCapture(target_resolution=(640, 360))
    frame = sc.capture_frame_numpy()
    assert frame is not None
    assert frame.shape == (360, 640, 3)
    assert frame.dtype == np.uint8

    b64 = sc.capture_base64()
    assert isinstance(b64, str)
    assert len(b64) > 100
    sc.close()


def test_frame_analyzer_delta() -> None:
    """Verify FrameAnalyzer detects changes between frames."""
    analyzer = FrameAnalyzer(change_threshold=0.10)
    frame1 = np.zeros((360, 640, 3), dtype=np.uint8)
    frame2 = np.zeros((360, 640, 3), dtype=np.uint8)
    frame3 = np.ones((360, 640, 3), dtype=np.uint8) * 255

    # First frame is baseline
    delta1 = analyzer.compute_difference(frame1)
    assert delta1 == 1.0

    # Identical second frame should have 0 change
    delta2 = analyzer.compute_difference(frame2)
    assert delta2 < 0.01

    # Completely different third frame should have high change
    has_changed, delta3 = analyzer.has_significant_change(frame3)
    assert has_changed is True
    assert delta3 > 0.8


@pytest.mark.asyncio
async def test_agent_visual_query_flow() -> None:
    """Verify agent triggers visual analysis on visual queries."""
    cfg = AppConfig()
    mock_llm = MockLLMProvider(canned_response="You are in a boss fight, watch out!")
    mock_vision = MockVisionModel(
        canned_result=VisionAnalysisResult(
            description="Player is facing Malenia with critical health.",
            scene="boss_fight",
            important_event=True,
            player_state="critical",
        )
    )

    agent = GamingCompanionAgent(
        config=cfg,
        llm_provider=mock_llm,
        vision_model=mock_vision,
    )

    # Ask a visual query
    response = await agent.respond_to_text("What is happening on my screen?", speak=False)
    assert "boss fight" in response.lower()
    assert agent.context.latest_vision_context is not None
    assert "Malenia" in agent.context.latest_vision_context
