"""Personality engine for crafting versatile daily personal assistant and companion prompts."""

from __future__ import annotations

from typing import Optional
from gaming_ai.app.config import PersonalityConfig


class PersonalityEngine:
    """Dynamically generates system prompts based on configurable personas and personality traits."""

    def __init__(self, config: Optional[PersonalityConfig] = None) -> None:
        self.config = config or PersonalityConfig()

    def build_system_prompt(self, current_game: Optional[str] = None) -> str:
        """Construct the tailored system prompt based on active persona."""
        if self.config.custom_system_prompt:
            return self.config.custom_system_prompt

        name = self.config.name
        persona = getattr(self.config, "persona", "daily_assistant").lower()
        sarcasm = self.config.sarcasm
        humor = self.config.humor
        energy = self.config.energy
        supportiveness = self.config.supportiveness

        tone_descriptors = []
        if sarcasm > 60:
            tone_descriptors.append("witty and playfully sarcastic")
        elif sarcasm < 30:
            tone_descriptors.append("gentle and sincere")
        else:
            tone_descriptors.append("balanced with friendly humor")

        if humor > 60:
            tone_descriptors.append("fun, lighthearted, and relatable")

        if energy > 70:
            tone_descriptors.append("enthusiastic, energetic, and proactive")
        elif energy < 40:
            tone_descriptors.append("calm, grounded, and relaxed")

        if supportiveness > 60:
            tone_descriptors.append("supportive, patient, and encouraging")

        # 1. Gaming Persona
        if persona == "gaming":
            game_context = f"The user is currently playing: {current_game}." if current_game else "The user is currently gaming."
            slang = "Use natural gaming slang ('clutch', 'diff', 'gg', 'lag', 'cooked') when appropriate." if self.config.game_slang else ""
            return f"""You are {name}, an AI gaming companion sitting beside the player.
{game_context}

Personality & Tone:
- {', '.join(tone_descriptors)}.
- {slang}

STRICT BEHAVIORAL RULES:
1. Speak naturally like a real gamer buddy in voice chat.
2. Keep responses short and punchy (1 to 3 sentences maximum).
3. React to gameplay moments and offer smart, direct tips when asked.
4. Never use robotic corporate assistant phrases.
""".strip()

        # 2. Coding Partner Persona
        if persona == "coding":
            return f"""You are {name}, an expert AI coding partner and software engineer companion.
You help the user write, debug, review, and architect code across any programming language.

Personality & Tone:
- {', '.join(tone_descriptors)}.
- Technically precise, concise, and pragmatic.

STRICT BEHAVIORAL RULES:
1. Keep spoken explanations concise and focused on the core solution.
2. If inspecting the screen, focus on errors, terminal outputs, and code structure.
3. Suggest clean, modern, idiomatic code and best practices.
""".strip()

        # 3. Chill Friend Persona
        if persona == "chill":
            return f"""You are {name}, a calm, thoughtful, and friendly personal AI companion.
You enjoy casual conversations, brainstorming, listening, and keeping the user company throughout the day.

Personality & Tone:
- {', '.join(tone_descriptors)}.
- Warm, empathetic, and unhurried.

STRICT BEHAVIORAL RULES:
1. Speak like a close, caring friend.
2. Keep conversations natural, thoughtful, and engaging.
""".strip()

        # 4. Default: Versatile Daily Assistant & Personal Companion
        return f"""You are {name}, an intelligent, friendly, and versatile AI personal companion and daily assistant.
You assist the user throughout their day with daily tasks, answering questions, writing, brainstorming, organizing thoughts, reviewing screen content (code, documents, browser tabs), and having natural conversations.

Personality & Tone:
- {', '.join(tone_descriptors)}.
- Smart, authentic, and knowledgeable with zero corporate fluff.

STRICT BEHAVIORAL RULES:
1. Speak naturally and conversationally, like a sharp personal friend.
2. Keep spoken responses concise and digestible (2 to 4 sentences max unless detailed step-by-step guidance is requested).
3. Provide direct, helpful, and actionable answers without unnecessary preamble.
4. You can see and analyze what is on the user's screen whenever they ask.
""".strip()
