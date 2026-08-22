"""Tests for Webcam capture and Player Reaction Analyzer."""

import numpy as np
import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.vision.player_analyzer import PlayerAnalyzer, PlayerReaction
from gaming_ai.vision.webcam import WebcamCapture


def test_webcam_mock_capture() -> None:
    """Verify webcam returns valid frame with mock image and encodes base64."""
    mock_img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw simple white box
    mock_img[100:300, 200:400] = 255

    cam = WebcamCapture(mock_frame=mock_img)
    assert cam.is_available() is True
    assert cam.start() is True

    frame = cam.capture_frame()
    assert frame is not None
    assert frame.shape == (480, 640, 3)

    b64 = cam.capture_base64()
    assert isinstance(b64, str)
    assert len(b64) > 50

    cam.stop()
    assert cam.is_active is False


def test_player_analyzer_empty_frame() -> None:
    """Verify analyzer handles empty/None frame gracefully."""
    analyzer = PlayerAnalyzer()
    reaction = analyzer.analyze_frame(None)
    assert reaction.face_detected is False
    assert reaction.engagement == "away"


def test_player_analyzer_synthetic_face() -> None:
    """Verify analyzer returns structured reaction object on synthetic frame."""
    analyzer = PlayerAnalyzer()
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    reaction = analyzer.analyze_frame(dummy_frame)
    assert isinstance(reaction, PlayerReaction)
    assert isinstance(reaction.summary, str)


@pytest.mark.asyncio
async def test_agent_observe_player_reaction() -> None:
    """Verify agent can observe player and update context."""
    cfg = AppConfig()
    mock_llm = MockLLMProvider(canned_response="Why are you laughing so hard? 😭")
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cam = WebcamCapture(mock_frame=dummy_frame)

    agent = GamingCompanionAgent(
        config=cfg,
        llm_provider=mock_llm,
        webcam=mock_cam,
    )

    reaction = await agent.observe_player()
    assert reaction is not None
    assert agent.context.latest_webcam_context is not None

    response = await agent.respond_to_text("Did you see that?", speak=False)
    assert "laughing" in response.lower()
