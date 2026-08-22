"""Observable thread-safe UI state model for real-time telemetry and transcript broadcasting."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gaming_ai.ui.state")


@dataclass
class TranscriptItem:
    """A single entry in the live transcript feed."""
    id: str
    timestamp: float = field(default_factory=time.time)
    sender: str = "system"  # player, companion, event, system
    text: str = ""
    latency_ms: Optional[float] = None
    event_type: Optional[str] = None
    score: Optional[float] = None


class DashboardState:
    """Central state manager for the companion UI dashboard."""

    def __init__(self) -> None:
        self.mic_status: str = "LISTENING"  # LISTENING, MUTED, PROCESSING
        self.camera_status: str = "ON"       # ON, OFF, DISABLED
        self.screen_status: str = "ACTIVE"   # ACTIVE, PAUSED
        self.ai_status: str = "IDLE"         # IDLE, THINKING, STREAMING
        self.voice_status: str = "SILENT"    # SILENT, SPEAKING
        self.current_game: str = "Elden Ring"

        self.personality: Dict[str, Any] = {
            "name": "Glitch",
            "sarcasm": 70,
            "humor": 80,
            "energy": 75,
            "talkativeness": 65,
            "gaming_slang": True,
        }

        self.telemetry: Dict[str, Any] = {
            "death_count": 0,
            "victory_count": 0,
            "events_detected": 0,
            "vram_used_mb": 4200,
            "vram_total_mb": 8192,
            "last_stt_latency_ms": 0,
            "last_llm_latency_ms": 0,
        }

        self.transcript: List[TranscriptItem] = []
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a notification callback for state changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister a notification callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self) -> None:
        """Broadcast state updates to all active listeners."""
        data = self.to_dict()
        for listener in self._listeners:
            try:
                listener(data)
            except Exception as e:
                logger.debug("Error notifying UI listener: %s", e)

    def set_sensors(
        self,
        mic: Optional[str] = None,
        camera: Optional[str] = None,
        screen: Optional[str] = None,
        ai: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        """Update sensor status indicators."""
        if mic is not None:
            self.mic_status = mic
        if camera is not None:
            self.camera_status = camera
        if screen is not None:
            self.screen_status = screen
        if ai is not None:
            self.ai_status = ai
        if voice is not None:
            self.voice_status = voice
        self._notify()

    def add_transcript(
        self,
        sender: str,
        text: str,
        latency_ms: Optional[float] = None,
        event_type: Optional[str] = None,
        score: Optional[float] = None,
    ) -> TranscriptItem:
        """Append an item to the live transcript feed."""
        import uuid
        item = TranscriptItem(
            id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            sender=sender,
            text=text,
            latency_ms=latency_ms,
            event_type=event_type,
            score=score,
        )
        self.transcript.append(item)
        if len(self.transcript) > 100:
            self.transcript.pop(0)
        self._notify()
        return item

    def update_telemetry(self, **kwargs: Any) -> None:
        """Update telemetry metrics."""
        self.telemetry.update(kwargs)
        self._notify()

    def update_personality(self, **kwargs: Any) -> None:
        """Update personality sliders."""
        self.personality.update(kwargs)
        self._notify()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete dashboard state to JSON-compatible dictionary."""
        return {
            "sensors": {
                "mic": self.mic_status,
                "camera": self.camera_status,
                "screen": self.screen_status,
                "ai": self.ai_status,
                "voice": self.voice_status,
            },
            "current_game": self.current_game,
            "personality": self.personality,
            "telemetry": self.telemetry,
            "transcript": [asdict(t) for t in self.transcript[-30:]],
        }
