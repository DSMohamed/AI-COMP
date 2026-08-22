"""Tests for SQLite Multi-Layer Memory Manager and session tracking."""

import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig
from gaming_ai.memory.db import DatabaseManager
from gaming_ai.memory.manager import MemoryManager
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.vision.event_detector import EventType, GameEvent


def test_database_manager_init() -> None:
    """Verify SQLite database schema and tables initialize cleanly in-memory."""
    db = DatabaseManager(db_path=":memory:")
    with db.get_connection() as conn:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        ]
        assert "sessions" in tables
        assert "memories" in tables
        assert "events" in tables
        assert "conversations" in tables


def test_memory_manager_session_and_events() -> None:
    """Verify session lifecycle, event logging, and counter increments."""
    db = DatabaseManager(db_path=":memory:")
    manager = MemoryManager(db=db)

    # Start session
    session = manager.start_session(game="elden_ring")
    assert session.game == "elden_ring"
    assert session.death_count == 0

    # Log death event
    death_event = GameEvent(
        event_type=EventType.DEATH,
        description="Fell off cliff in Stormveil",
        interestingness=0.95,
    )
    stored_event = manager.record_event(death_event)
    assert stored_event.event_type == "death"
    assert manager.current_session.death_count == 1

    # Log conversation turns
    t1 = manager.record_turn("user", "I hate gravity in this game.")
    t2 = manager.record_turn("assistant", "Gravity is the true final boss.")
    assert t1.role == "user"
    assert t2.role == "assistant"

    # End session
    closed_session = manager.end_session(summary="Explored Stormveil and died once.")
    assert closed_session.death_count == 1
    assert closed_session.summary is not None
    assert manager.current_session is None


def test_long_term_memory_facts() -> None:
    """Verify storing, filtering, and assembling long-term memory blocks."""
    db = DatabaseManager(db_path=":memory:")
    manager = MemoryManager(db=db)

    manager.save_memory(
        category="preference",
        content="Player loves using colossal swords and Strength builds.",
        game="elden_ring",
        importance=0.9,
    )
    manager.save_memory(
        category="running_joke",
        content="Player always forgets to activate Great Runes at divine towers.",
        game="elden_ring",
        importance=0.7,
    )

    memories = manager.get_memories(game="elden_ring")
    assert len(memories) == 2
    assert "colossal swords" in memories[0].content

    block = manager.get_prompt_memory_block(game="elden_ring")
    assert block is not None
    assert "LONG-TERM PLAYER MEMORY" in block
    assert "colossal swords" in block


@pytest.mark.asyncio
async def test_agent_memory_persistence_integration() -> None:
    """Verify companion agent logs turns to database and recalls facts across sessions."""
    db = DatabaseManager(db_path=":memory:")
    manager = MemoryManager(db=db)

    # Preload a long-term memory
    manager.save_memory(
        category="playstyle",
        content="Player prefers aggressive dodge-rolling instead of parrying.",
        game="elden_ring",
    )

    mock_llm = MockLLMProvider(canned_response="I know you love dodge-rolling everything!")
    agent = GamingCompanionAgent(
        config=AppConfig(),
        llm_provider=mock_llm,
        memory=manager,
    )
    agent.context.current_game = "elden_ring"

    reply = await agent.respond_to_text("Should I try to parry this crucible knight?", speak=False)
    assert "dodge-rolling" in reply

    # Verify conversation turns were saved in SQLite
    with db.get_connection() as conn:
        turns = conn.execute("SELECT * FROM conversations;").fetchall()
        assert len(turns) == 2
        assert turns[0]["role"] == "user"
        assert turns[1]["role"] == "assistant"
