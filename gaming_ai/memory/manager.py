"""Multi-layer memory manager orchestrating sessions, events, turns, and long-term facts."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from gaming_ai.memory.db import DatabaseManager
from gaming_ai.memory.models import ConversationTurn, MemoryRecord, Session, StoredEvent
from gaming_ai.vision.event_detector import EventType, GameEvent

logger = logging.getLogger("gaming_ai.memory.manager")


class MemoryManager:
    """Manages multi-tier player memory: Working, Session, Episodic, and Semantic."""

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self.db = db or DatabaseManager()
        self.current_session: Optional[Session] = None

    def start_session(self, game: str = "general") -> Session:
        """Initialize and persist a new gaming session."""
        session_id = str(uuid.uuid4())[:8]
        session = Session(session_id=session_id, game=game.lower(), start_time=time.time())

        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, game, start_time, death_count, victory_count) VALUES (?, ?, ?, 0, 0);",
                (session.session_id, session.game, session.start_time),
            )
            conn.commit()

        self.current_session = session
        logger.info("Started session %s for game '%s'", session.session_id, session.game)
        return session

    def record_event(self, event: GameEvent) -> StoredEvent:
        """Store a detected gameplay event and update session statistics."""
        if not self.current_session:
            self.start_session()

        session_id = self.current_session.session_id
        event_id = str(uuid.uuid4())[:8]

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO events (event_id, session_id, event_type, description, interestingness, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event_id,
                    session_id,
                    event.event_type.value,
                    event.description,
                    event.interestingness,
                    event.timestamp,
                    json.dumps(event.metadata),
                ),
            )

            # Update session counters
            if event.event_type == EventType.DEATH:
                self.current_session.death_count += 1
                conn.execute(
                    "UPDATE sessions SET death_count = death_count + 1 WHERE session_id = ?;",
                    (session_id,),
                )
            elif event.event_type in (EventType.VICTORY, EventType.BOSS_DEFEAT):
                self.current_session.victory_count += 1
                conn.execute(
                    "UPDATE sessions SET victory_count = victory_count + 1 WHERE session_id = ?;",
                    (session_id,),
                )
            conn.commit()

        return StoredEvent(
            event_id=event_id,
            session_id=session_id,
            event_type=event.event_type.value,
            description=event.description,
            interestingness=event.interestingness,
            timestamp=event.timestamp,
            metadata=event.metadata,
        )

    def record_turn(self, role: str, content: str) -> ConversationTurn:
        """Store a conversational turn."""
        if not self.current_session:
            self.start_session()

        session_id = self.current_session.session_id
        turn_id = str(uuid.uuid4())[:8]
        now = time.time()

        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (turn_id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?);",
                (turn_id, session_id, role, content, now),
            )
            conn.commit()

        return ConversationTurn(
            turn_id=turn_id,
            session_id=session_id,
            role=role,
            content=content,
            timestamp=now,
        )

    def save_memory(
        self,
        category: str,
        content: str,
        game: str = "general",
        importance: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Save a long-term player fact, preference, or past achievement."""
        memory_id = str(uuid.uuid4())[:8]
        now = time.time()
        meta = metadata or {}

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories (memory_id, category, content, game, importance, created_at, last_accessed, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (memory_id, category, content, game.lower(), importance, now, now, json.dumps(meta)),
            )
            conn.commit()

        logger.info("Saved long-term memory [%s]: '%s'", category, content)
        return MemoryRecord(
            memory_id=memory_id,
            category=category,
            content=content,
            game=game.lower(),
            importance=importance,
            created_at=now,
            last_accessed=now,
            metadata=meta,
        )

    def get_memories(
        self,
        game: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryRecord]:
        """Query relevant long-term memories sorted by importance."""
        query = "SELECT * FROM memories WHERE 1=1"
        params: List[Any] = []

        if game and game.lower() != "general":
            query += " AND (game = ? OR game = 'general')"
            params.append(game.lower())
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY importance DESC, created_at DESC LIMIT ?;"
        params.append(limit)

        records: List[MemoryRecord] = []
        with self.db.get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            for r in rows:
                records.append(
                    MemoryRecord(
                        memory_id=r["memory_id"],
                        category=r["category"],
                        content=r["content"],
                        game=r["game"],
                        importance=r["importance"],
                        created_at=r["created_at"],
                        last_accessed=r["last_accessed"],
                        metadata=json.loads(r["metadata"] or "{}"),
                    )
                )

        return records

    def get_prompt_memory_block(self, game: Optional[str] = None, limit: int = 5) -> Optional[str]:
        """Assemble a grounded long-term memory block for prompt injection."""
        memories = self.get_memories(game=game, limit=limit)
        if not memories:
            return None

        lines = ["LONG-TERM PLAYER MEMORY & HISTORY:"]
        for m in memories:
            lines.append(f"- [{m.category.upper()}] {m.content}")

        # Add recent past session stats if available
        recent_sessions = self.get_recent_sessions(game=game, limit=2)
        if recent_sessions:
            for s in recent_sessions:
                if s.session_id != (self.current_session.session_id if self.current_session else None):
                    lines.append(
                        f"- [PAST SESSION ({s.game.upper()})]: {s.death_count} deaths, {s.victory_count} victories."
                    )

        return "\n".join(lines)

    def get_recent_sessions(self, game: Optional[str] = None, limit: int = 3) -> List[Session]:
        """Fetch past completed or ongoing sessions."""
        query = "SELECT * FROM sessions"
        params: List[Any] = []
        if game and game.lower() != "general":
            query += " WHERE game = ?"
            params.append(game.lower())
        query += " ORDER BY start_time DESC LIMIT ?;"
        params.append(limit)

        sessions: List[Session] = []
        with self.db.get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            for r in rows:
                sessions.append(
                    Session(
                        session_id=r["session_id"],
                        game=r["game"],
                        start_time=r["start_time"],
                        end_time=r["end_time"],
                        summary=r["summary"],
                        death_count=r["death_count"],
                        victory_count=r["victory_count"],
                    )
                )
        return sessions

    def end_session(self, summary: Optional[str] = None) -> Optional[Session]:
        """Close current session and persist final summary."""
        if not self.current_session:
            return None

        now = time.time()
        self.current_session.end_time = now
        self.current_session.summary = summary

        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET end_time = ?, summary = ? WHERE session_id = ?;",
                (now, summary, self.current_session.session_id),
            )
            conn.commit()

        session = self.current_session
        self.current_session = None
        logger.info("Session %s closed (Deaths: %d, Victories: %d)", session.session_id, session.death_count, session.victory_count)
        return session
