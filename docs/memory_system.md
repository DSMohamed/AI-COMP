# 🧠 Multi-Layer Persistent Memory System

The Multi-Layer Memory subsystem gives the AI companion a persistent identity and cross-session memory. The companion remembers player preferences, favorite weapon builds, past boss struggles, and running jokes across multiple gaming sessions.

---

## 🏛️ Memory Architecture (Section 20–23 Compliance)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        4-Tier Memory Hierarchy                         │
├────────────────────────────────┬───────────────────────────────────────┤
│ 1. Working Context             │ Immediate rolling turn buffer &       │
│    (In-Memory Deque)           │ live screen/webcam perception context │
├────────────────────────────────┼───────────────────────────────────────┤
│ 2. Session Memory              │ Current session telemetry: death      │
│    (Active SQLite Session)     │ count, victories, events, turn log    │
├────────────────────────────────┼───────────────────────────────────────┤
│ 3. Episodic Memory             │ Past gaming sessions summaries        │
│    (SQLite `sessions` table)   │ ("Yesterday you died 8 times to Radahn")
├────────────────────────────────┼───────────────────────────────────────┤
│ 4. Semantic Memory             │ Long-term facts, player preferences,  │
│    (SQLite `memories` table)   │ build types, running jokes, playstyle │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 🗄️ SQLite Database Schema (`data/memory.db`)

* `sessions`: `session_id`, `game`, `start_time`, `end_time`, `summary`, `death_count`, `victory_count`
* `memories`: `memory_id`, `category` (preference/playstyle/joke), `content`, `game`, `importance`, `created_at`, `last_accessed`
* `events`: `event_id`, `session_id`, `event_type`, `description`, `interestingness`, `timestamp`, `metadata`
* `conversations`: `turn_id`, `session_id`, `role` (user/assistant), `content`, `timestamp`

---

## 🧩 Components

1. **Database Manager (`gaming_ai.memory.db.DatabaseManager`)**:
   * Thread-safe SQLite connection pool with WAL mode (`PRAGMA journal_mode=WAL`) and indices.
2. **Memory Manager (`gaming_ai.memory.manager.MemoryManager`)**:
   * Tracks session lifecycles and event increments (e.g. death counter).
   * Persists every user utterance and companion reply.
   * Extracts grounded long-term memory blocks and injects them directly into the LLM system prompt.
