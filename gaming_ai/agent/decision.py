"""Decision and attention engine for deciding when the companion should speak."""

from __future__ import annotations

import logging
import time
from typing import Optional

from gaming_ai.app.config import PersonalityConfig
from gaming_ai.vision.event_detector import EventType, GameEvent

logger = logging.getLogger("gaming_ai.agent.decision")


class DecisionEngine:
    """Evaluates game events and personality settings to decide if commentary is warranted."""

    def __init__(
        self,
        personality_config: Optional[PersonalityConfig] = None,
        base_threshold: float = 0.70,
        min_speech_interval: float = 8.0,
    ) -> None:
        self.personality = personality_config or PersonalityConfig()
        self.base_threshold = base_threshold
        self.min_speech_interval = min_speech_interval
        self._last_speech_time: float = 0.0

    @property
    def effective_threshold(self) -> float:
        """
        Dynamically adjust threshold based on talkativeness (0-100).
        Talkativeness 100 -> threshold ~0.55 (chats often)
        Talkativeness 0   -> threshold ~0.88 (quiet, speaks only on major events)
        """
        talkativeness_offset = (self.personality.talkativeness - 50) / 250.0  # -0.2 to +0.2
        threshold = self.base_threshold - talkativeness_offset
        return max(0.40, min(0.90, threshold))

    def should_comment(self, event: GameEvent, force: bool = False) -> bool:
        """
        Determine if the companion should comment on an autonomous gameplay event.
        """
        if force:
            return True

        now = time.time()
        elapsed_since_speech = now - self._last_speech_time

        # Check speech cooldown interval
        if elapsed_since_speech < self.min_speech_interval:
            # Exception: Critical major events (e.g. death or victory) can bypass normal cooldown
            if event.event_type in (EventType.DEATH, EventType.VICTORY) and elapsed_since_speech > 3.0:
                logger.debug("Bypassing cooldown for major event: %s", event.event_type.value)
            else:
                logger.debug(
                    "Comment suppressed by cooldown (%.1fs < %.1fs)",
                    elapsed_since_speech,
                    self.min_speech_interval,
                )
                return False

        # Check score against effective threshold
        threshold = self.effective_threshold
        should_speak = event.interestingness >= threshold

        if should_speak:
            logger.info(
                "Decision: SPEAK on [%s] (Score %.2f >= Threshold %.2f)",
                event.event_type.value,
                event.interestingness,
                threshold,
            )
        else:
            logger.debug(
                "Decision: IGNORE [%s] (Score %.2f < Threshold %.2f)",
                event.event_type.value,
                event.interestingness,
                threshold,
            )

        return should_speak

    def record_speech(self) -> None:
        """Record timestamp of companion utterance to reset cooldown."""
        self._last_speech_time = time.time()

    def reset_cooldown(self) -> None:
        """Force reset cooldown (e.g. when user speaks directly)."""
        self._last_speech_time = 0.0
