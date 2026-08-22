"""Game event detection and interestingness scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional

from gaming_ai.vision.vision_model import VisionAnalysisResult

logger = logging.getLogger("gaming_ai.vision.event_detector")


class EventType(str, Enum):
    """Classified game event types."""
    DEATH = "death"
    VICTORY = "victory"
    BOSS_ENCOUNTER = "boss_encounter"
    BOSS_DEFEAT = "boss_defeat"
    CRITICAL_HEALTH = "critical_health"
    CLUTCH_PLAY = "clutch_play"
    MISTAKE = "mistake"
    ACHIEVEMENT = "achievement"
    RARE_ITEM = "rare_item"
    CUTSCENE = "cutscene"
    EXPLORATION = "exploration"
    MENU = "menu"
    UNKNOWN = "unknown"


@dataclass
class GameEvent:
    """Represents a detected gameplay event with calculated interestingness."""
    event_type: EventType
    description: str
    interestingness: float = 0.5  # 0.0 to 1.0 scale
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_major(self) -> bool:
        """Check if event warrants high priority commentary."""
        return self.interestingness >= 0.75


class EventDetector:
    """Extracts game events from VLM scene analysis and calculates attention scores."""

    def __init__(self, sensitivity: float = 1.0) -> None:
        self.sensitivity = max(0.1, min(2.0, sensitivity))
        self._last_event_type: Optional[EventType] = None
        self._last_event_time: float = 0.0
        self._consecutive_deaths: int = 0

    def detect_event(
        self,
        vision_result: VisionAnalysisResult,
        frame_delta: float = 0.5,
    ) -> GameEvent:
        """
        Evaluate structured vision analysis and frame motion to detect game events.
        """
        scene = vision_result.scene.lower()
        player_state = vision_result.player_state.lower()
        description = vision_result.description

        # Base event classification
        if "death" in scene or "dead" in player_state or "died" in description.lower() or "you died" in description.lower():
            event_type = EventType.DEATH
            self._consecutive_deaths += 1
            base_score = 0.95
        elif "victory" in scene or "won" in description.lower() or "boss defeated" in description.lower():
            event_type = EventType.VICTORY
            self._consecutive_deaths = 0
            base_score = 0.92
        elif "boss" in scene or "boss fight" in description.lower():
            event_type = EventType.BOSS_ENCOUNTER
            base_score = 0.85
        elif "critical" in player_state or "low_health" in player_state or "low hp" in description.lower():
            event_type = EventType.CRITICAL_HEALTH
            base_score = 0.78
        elif "cutscene" in scene or "cinematic" in description.lower():
            event_type = EventType.CUTSCENE
            base_score = 0.40
        elif "menu" in scene or "inventory" in description.lower() or "loading" in scene:
            event_type = EventType.MENU
            base_score = 0.15
        else:
            event_type = EventType.EXPLORATION
            base_score = 0.35 if frame_delta > 0.3 else 0.20

        # Adjust score based on explicit importance flag from VLM
        if vision_result.important_event:
            base_score = min(1.0, base_score + 0.15)

        # Scale by sensitivity
        final_score = min(1.0, max(0.0, base_score * self.sensitivity))

        now = time.time()
        # Cooldown reduction for repeating same minor event
        if event_type == self._last_event_type and (now - self._last_event_time) < 15.0:
            if event_type not in (EventType.DEATH, EventType.VICTORY):
                final_score *= 0.6  # Dampen repetitive events

        self._last_event_type = event_type
        self._last_event_time = now

        event = GameEvent(
            event_type=event_type,
            description=description,
            interestingness=round(final_score, 2),
            timestamp=now,
            metadata={
                "scene": vision_result.scene,
                "player_state": vision_result.player_state,
                "consecutive_deaths": self._consecutive_deaths,
                "frame_delta": frame_delta,
            },
        )

        logger.info(
            "Game Event Detected: [%s] (Score: %.2f) — %s",
            event.event_type.value,
            event.interestingness,
            event.description,
        )
        return event

    def reset(self) -> None:
        """Reset internal event tracking state."""
        self._last_event_type = None
        self._last_event_time = 0.0
        self._consecutive_deaths = 0
