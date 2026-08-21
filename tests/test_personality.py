"""Tests for companion personality prompt generation."""

from gaming_ai.agent.personality import PersonalityEngine
from gaming_ai.app.config import PersonalityConfig


def test_personality_prompt_generation() -> None:
    """Verify system prompt includes companion name and tone descriptors."""
    config = PersonalityConfig(name="Glitch", sarcasm=85, humor=80, game_slang=True)
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt(current_game="Elden Ring")

    assert "Glitch" in prompt
    assert "Elden Ring" in prompt
    assert "sarcastic" in prompt
    assert "gaming slang" in prompt.lower() or "cooked" in prompt.lower()
    assert "SHORT AND PUNCHY" in prompt


def test_custom_prompt_override() -> None:
    """Verify custom prompt overrides dynamic generation."""
    config = PersonalityConfig(custom_system_prompt="Custom gaming buddy override prompt.")
    engine = PersonalityEngine(config)
    prompt = engine.build_system_prompt()

    assert prompt == "Custom gaming buddy override prompt."
