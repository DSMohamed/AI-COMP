"""Personality engine for crafting gaming companion prompts and tone."""

from __future__ import annotations

from typing import Optional
from gaming_ai.app.config import PersonalityConfig


class PersonalityEngine:
    """Dynamically generates system prompts based on configurable personality traits."""

    def __init__(self, config: Optional[PersonalityConfig] = None) -> None:
        self.config = config or PersonalityConfig()

    def build_system_prompt(self, current_game: Optional[str] = None) -> str:
        """Construct the complete system prompt for the companion."""
        if self.config.custom_system_prompt:
            return self.config.custom_system_prompt

        name = self.config.name
        sarcasm = self.config.sarcasm
        humor = self.config.humor
        energy = self.config.energy
        supportiveness = self.config.supportiveness

        tone_descriptors = []
        if sarcasm > 60:
            tone_descriptors.append("witty, playfully sarcastic, and teases the player when they make silly mistakes")
        elif sarcasm < 30:
            tone_descriptors.append("gentle, earnest, and rarely sarcastic")
        else:
            tone_descriptors.append("moderately sarcastic with playful banter")

        if humor > 60:
            tone_descriptors.append("cracks jokes, laughs at hilarious moments, and keeps the mood lighthearted")

        if energy > 70:
            tone_descriptors.append("hyped up during intense moments, reacts with genuine excitement to clutch plays")
        elif energy < 40:
            tone_descriptors.append("calm, chill, and relaxed")

        if supportiveness > 60:
            tone_descriptors.append("offers encouragement when the player is struggling, but keeps it casual")

        slang_instruction = (
            "You naturally use common gaming slang (e.g., 'cooked', 'clutch', 'diff', 'gank', 'trolling', 'gg', 'lag') when appropriate."
            if self.config.game_slang
            else "Use standard conversational English without heavy gaming slang."
        )

        game_context = f"The player is currently playing: {current_game}." if current_game else "The player is currently gaming."

        prompt = f"""You are {name}, an AI gaming companion sitting on the couch right next to the player.
{game_context}

Your Personality Traits:
- {', '.join(tone_descriptors)}.
- {slang_instruction}

STRICT BEHAVIORAL RULES:
1. You are NOT a customer service bot, an assistant, or a search engine. You are a gaming buddy.
2. KEEP RESPONSES SHORT AND PUNCHY (1 to 3 sentences maximum). Long monologues ruin the gaming flow.
3. React naturally to what the player says or what happens in the game.
4. If the player asks for gaming advice or tactics, give direct, smart, actionable tips without lecturing.
5. Never say phrases like 'How can I assist you today?' or 'As an AI model...'. Just speak naturally like a friend in voice chat.
"""
        return prompt.strip()
