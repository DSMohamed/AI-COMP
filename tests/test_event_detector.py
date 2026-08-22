"""Tests for EventDetector, GameEvent scoring, and DecisionEngine attention system."""

import time
import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.agent.decision import DecisionEngine
from gaming_ai.app.config import AppConfig, PersonalityConfig
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.vision.event_detector import EventDetector, EventType, GameEvent
from gaming_ai.vision.vision_model import MockVisionModel, VisionAnalysisResult


def test_event_detector_classification() -> None:
    """Verify event classification and scoring across different game situations."""
    detector = EventDetector()

    # Death event
    death_result = VisionAnalysisResult(
        description="Player was crushed by the boss. YOU DIED screen.",
        scene="death_screen",
        important_event=True,
        player_state="dead",
    )
    event_death = detector.detect_event(death_result)
    assert event_death.event_type == EventType.DEATH
    assert event_death.interestingness >= 0.90
    assert event_death.is_major is True

    # Boss encounter
    boss_result = VisionAnalysisResult(
        description="Boss health bar appeared. Giant dragon swoops down.",
        scene="boss_fight",
        important_event=True,
        player_state="normal",
    )
    event_boss = detector.detect_event(boss_result)
    assert event_boss.event_type == EventType.BOSS_ENCOUNTER
    assert event_boss.interestingness >= 0.80

    # Menu screen (low interest)
    menu_result = VisionAnalysisResult(
        description="Player opened inventory menu.",
        scene="menu",
        important_event=False,
        player_state="normal",
    )
    event_menu = detector.detect_event(menu_result)
    assert event_menu.event_type == EventType.MENU
    assert event_menu.interestingness <= 0.30
    assert event_menu.is_major is False


def test_decision_engine_thresholding() -> None:
    """Verify DecisionEngine filters events according to score and talkativeness."""
    # Normal talkativeness (50) -> threshold 0.70
    decision = DecisionEngine(personality_config=PersonalityConfig(talkativeness=50))
    assert 0.65 <= decision.effective_threshold <= 0.75

    minor_event = GameEvent(event_type=EventType.EXPLORATION, description="Walking in forest", interestingness=0.30)
    major_event = GameEvent(event_type=EventType.DEATH, description="Player fell off cliff", interestingness=0.95)

    assert decision.should_comment(minor_event) is False
    assert decision.should_comment(major_event) is True


def test_decision_engine_cooldown() -> None:
    """Verify speech cooldown suppresses commentary until cooldown expires."""
    decision = DecisionEngine(
        personality_config=PersonalityConfig(talkativeness=50),
        min_speech_interval=5.0,
    )
    event = GameEvent(event_type=EventType.BOSS_ENCOUNTER, description="Boss attacking", interestingness=0.85)

    # First time: can speak
    assert decision.should_comment(event) is True
    decision.record_speech()

    # Immediately after: suppressed by cooldown
    assert decision.should_comment(event) is False

    # Force reset cooldown (e.g. user talked or time passed)
    decision.reset_cooldown()
    assert decision.should_comment(event) is True


@pytest.mark.asyncio
async def test_agent_process_gameplay_frame() -> None:
    """Verify agent process_gameplay_frame detects event and generates comment."""
    cfg = AppConfig()
    mock_llm = MockLLMProvider(canned_response="BRO YOU ACTUALLY DIED AGAIN 😭")
    mock_vision = MockVisionModel(
        canned_result=VisionAnalysisResult(
            description="YOU DIED screen visible after boss combo.",
            scene="death_screen",
            important_event=True,
            player_state="dead",
        )
    )

    agent = GamingCompanionAgent(
        config=cfg,
        llm_provider=mock_llm,
        vision_model=mock_vision,
    )

    event = await agent.process_gameplay_frame(force_analysis=True)
    assert event is not None
    assert event.event_type == EventType.DEATH
    assert len(agent.context._history) >= 2
