"""Tests for companion personality prompt generation and daily assistant personas."""

from gaming_ai.agent.personality import PersonalityEngine
from gaming_ai.app.config import PersonalityConfig


def test_personality_prompt_generation_gaming() -> None:
    """Verify gaming persona includes gamer slang and brevity rules."""
    config = PersonalityConfig(name="Glitch", persona="gaming", sarcasm=85, humor=80, game_slang=True)
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt(current_game="Elden Ring")

    assert "Glitch" in prompt
    assert "Elden Ring" in prompt
    assert "sarcastic" in prompt


def test_personality_prompt_generation_daily_assistant() -> None:
    """Verify daily assistant persona constructs a versatile personal helper prompt."""
    config = PersonalityConfig(name="Nova", persona="daily_assistant", sarcasm=30, humor=70)
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt()

    assert "Nova" in prompt
    assert "personal companion" in prompt.lower() or "daily assistant" in prompt.lower()
    assert "screen" in prompt.lower()


def test_custom_prompt_override() -> None:
    """Verify custom prompt overrides dynamic generation."""
    config = PersonalityConfig(custom_system_prompt="Custom daily assistant override prompt.")
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt()

    assert prompt == "Custom daily assistant override prompt."
