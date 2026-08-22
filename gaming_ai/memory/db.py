"""SQLite database connection and schema migration manager."""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3
from typing import Optional

logger = logging.getLogger("gaming_ai.memory.db")


class DatabaseManager:
    """Thread-safe SQLite database manager with WAL mode and indices."""

    def __init__(self, db_path: str | Path = "data/memory.db") -> None:
        self.db_path = str(db_path)
        self._shared_in_memory_conn: Optional[sqlite3.Connection] = None

        if self.db_path == ":memory:":
            self._shared_in_memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_in_memory_conn.row_factory = sqlite3.Row
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create or return connection configured for high performance."""
        if self._shared_in_memory_conn is not None:
            return self._shared_in_memory_conn

        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Run schema migrations."""
        conn = self.get_connection()
        try:
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    game TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    summary TEXT,
                    death_count INTEGER DEFAULT 0,
                    victory_count INTEGER DEFAULT 0
                );
            """)

            # Long-term Memories table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    game TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    metadata TEXT DEFAULT '{}'
                );
            """)

            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    interestingness REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                );
            """)

            # Conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    turn_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
                );
            """)

            # Performance indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_game ON memories(game);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);")
            conn.commit()
            logger.info("SQLite memory schema initialized at %s", self.db_path)
        finally:
            if self._shared_in_memory_conn is None:
                conn.close()
