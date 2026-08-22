"""Data models for multi-layer persistent gaming memory."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional


@dataclass
class Session:
    """Represents a gaming session."""
    session_id: str
    game: str = "general"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    summary: Optional[str] = None
    death_count: int = 0
    victory_count: int = 0


@dataclass
class MemoryRecord:
    """Long-term semantic or episodic memory fact."""
    memory_id: str
    category: str  # preference, playstyle, achievement, running_joke, lore, past_event
    content: str
    game: str = "general"
    importance: float = 0.5  # 0.0 to 1.0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StoredEvent:
    """Logged in-game event associated with a session."""
    event_id: str
    session_id: str
    event_type: str
    description: str
    interestingness: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """Stored conversation utterance."""
    turn_id: str
    session_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: float = field(default_factory=time.time)
