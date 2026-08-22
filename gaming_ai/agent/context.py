"""Context engine for managing short-term history and prompt assembly."""

from __future__ import annotations

from typing import List, Optional
from collections import deque

from gaming_ai.agent.personality import PersonalityEngine
from gaming_ai.models.provider import Message


class ContextEngine:
    """Aggregates conversation history, personality prompt, and game context."""

    def __init__(
        self,
        personality_engine: Optional[PersonalityEngine] = None,
        history_limit: int = 10,
    ) -> None:
        self.personality = personality_engine or PersonalityEngine()
        self.history_limit = history_limit
        self._history: deque[Message] = deque(maxlen=history_limit * 2)
        self.current_game: Optional[str] = None
        self.latest_vision_context: Optional[str] = None
        self.latest_webcam_context: Optional[str] = None
        self.latest_rag_context: Optional[str] = None
        self.latest_memory_context: Optional[str] = None

    def add_user_message(self, text: str) -> None:
        """Add a player utterance to history."""
        self._history.append(Message(role="user", content=text))

    def add_assistant_message(self, text: str) -> None:
        """Add companion response to history."""
        self._history.append(Message(role="assistant", content=text))

    def update_vision_context(self, visual_description: str) -> None:
        """Update the latest perceived screen state."""
        self.latest_vision_context = visual_description

    def update_webcam_context(self, reaction_summary: str) -> None:
        """Update the latest perceived player webcam reaction."""
        self.latest_webcam_context = reaction_summary

    def update_rag_context(self, rag_text: Optional[str]) -> None:
        """Update the latest retrieved game knowledge context."""
        self.latest_rag_context = rag_text

    def update_memory_context(self, memory_text: Optional[str]) -> None:
        """Update persistent long-term memories about the player."""
        self.latest_memory_context = memory_text

    def clear_history(self) -> None:
        """Reset short-term conversation history."""
        self._history.clear()

    def build_context(self, current_user_input: Optional[str] = None) -> List[Message]:
        """
        Assemble the complete message payload for the LLM.
        """
        system_prompt = self.personality.build_system_prompt(current_game=self.current_game)
        
        if self.latest_memory_context:
            system_prompt += f"\n\n{self.latest_memory_context}"

        if self.latest_vision_context:
            system_prompt += f"\n\nCURRENT SCREEN OBSERVATION:\n{self.latest_vision_context}"

        if self.latest_webcam_context:
            system_prompt += f"\n\nPLAYER WEBCAM REACTION:\n{self.latest_webcam_context}"

        if self.latest_rag_context:
            system_prompt += f"\n\n{self.latest_rag_context}"

        messages: List[Message] = [Message(role="system", content=system_prompt)]

        # Append historical turns
        messages.extend(list(self._history))

        # Append current user input if provided and not already in history
        if current_user_input:
            messages.append(Message(role="user", content=current_user_input))

        return messages
