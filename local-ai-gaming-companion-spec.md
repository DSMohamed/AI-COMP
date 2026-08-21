# LOCAL AI GAMING COMPANION

## Complete Technical Specification & Development Prompt

You are an expert AI engineer, machine-learning engineer, computer-vision engineer, speech/voice engineer, Python developer, desktop application developer, and systems architect.

Your task is to build a **local-first AI gaming companion** for Windows.

This is not a simple chatbot.

The final system should behave like an intelligent gaming companion that can:

* see the game screen
* optionally see the player through a webcam
* hear the player through a microphone
* understand spoken conversation
* understand what is happening in games
* retrieve gaming knowledge using RAG
* remember relevant information about the user
* remember important events from previous gaming sessions
* decide when something is worth commenting on
* speak naturally using neural TTS
* optionally interact with the computer
* have a configurable personality
* work primarily locally
* be optimized for an NVIDIA RTX 3070 with 8 GB VRAM

The system should be designed so that individual models can be replaced later without rewriting the entire application.

---

# 1. HARDWARE TARGET

Target computer:

* NVIDIA RTX 3070
* 8 GB VRAM
* Windows 10/11
* CUDA-capable NVIDIA GPU
* Local storage available for models and databases
* Internet connection may exist, but core functionality should not depend on cloud APIs

The application MUST be designed around an 8 GB VRAM constraint.

Do not assume:

* RTX 4090
* RTX 5090
* 24 GB VRAM
* cloud GPU
* enterprise hardware

Use:

* quantized models where appropriate
* GPU acceleration
* CPU/RAM offloading when necessary
* asynchronous processing
* model reuse
* caching
* efficient image processing

Do not load multiple unnecessarily large models into VRAM simultaneously.

---

# 2. CORE PHILOSOPHY

The project should NOT attempt to train one enormous AI model that does everything.

Instead, create a modular AI system.

Each component has a specific responsibility.

```text
                ┌─────────────────┐
                │     LLM Brain   │
                └────────┬────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
      Vision           RAG             Memory
        │                │                │
     Eyes 👁️        Knowledge 📚     Experiences 🧠
        │                │                │
        └────────────────┼────────────────┘
                         │
                    AI Context
                         │
        ┌────────────────┼────────────────┐
        │                                 │
      Voice                           Computer
     Hearing 👂                       Control 🖥️
        │                                 │
      STT                               Tools
        │
      TTS 🔊
```

Do not confuse:

* RAG
* memory
* fine-tuning
* model training

They are different systems.

---

# 3. AI COMPONENTS

The system should contain at least these major components:

1. Speech-to-text
2. Voice activity detection
3. Vision-language model
4. Screen capture
5. Webcam processing
6. Event detection
7. Main LLM
8. RAG knowledge system
9. Short-term memory
10. Long-term memory
11. Session memory
12. Personality system
13. Text-to-speech
14. Audio playback
15. Computer-control tools
16. Game/plugin system
17. Desktop UI
18. Configuration system
19. Privacy system
20. Monitoring/diagnostics system

---

# 4. MODEL SELECTION

Before implementation, research currently available open-source models.

Do not blindly use old recommendations.

Evaluate models based on:

* VRAM usage
* quantization support
* Windows compatibility
* CUDA compatibility
* inference speed
* quality
* licensing
* local/offline capability
* model size
* community support

Select models realistically capable of running on an RTX 3070 8 GB.

Possible model categories include:

### STT

Evaluate:

* faster-whisper
* Whisper variants
* other efficient local STT models

### LLM

Evaluate:

* Qwen
* Llama
* Gemma
* other suitable 7B/8B-class models

### VLM

Evaluate:

* Qwen multimodal models
* Gemma multimodal models
* other lightweight vision-language models

### TTS

Evaluate:

* Kokoro
* Piper
* other modern open-source neural TTS models

Do not choose a model solely because it has the highest benchmark score.

A smaller model that runs quickly on an RTX 3070 is preferable to a theoretically better model that causes VRAM exhaustion.

---

# 5. SPEECH INPUT

The user should be able to talk naturally.

Pipeline:

```text
Microphone
    ↓
Audio stream
    ↓
Voice Activity Detection
    ↓
Speech-to-Text
    ↓
User message
    ↓
AI context
```

Use local STT.

The system should:

* detect when the user starts speaking
* detect when they stop
* ignore long periods of silence
* handle background game audio reasonably
* support conversational speech
* support interruption

Do not send raw microphone audio to the LLM.

Convert speech into text first.

---

# 6. SPEECH INTERRUPTION

The AI must support natural interruption.

Example:

AI:

> "I think you should probably—"

User:

> "WAIT WAIT WAIT"

The system should:

1. detect the user speaking
2. stop or fade out TTS
3. prioritize the user's speech
4. transcribe it
5. process it
6. respond

Do not force the user to wait until the AI finishes speaking.

---

# 7. SCREEN OBSERVATION

The AI must be capable of watching the game.

Use an efficient Windows screen-capture mechanism.

Potential technologies:

* DXGI/Desktop Duplication
* Windows Graphics Capture
* OBS capture
* another low-overhead implementation

Do NOT send every frame directly to the VLM.

Instead:

```text
Game
 ↓
High-FPS capture
 ↓
Cheap frame comparison
 ↓
Detect significant change
 ↓
Potential interesting frame
 ↓
VLM
```

The capture system should be independent from the vision inference system.

---

# 8. VISION-LANGUAGE MODEL

The VLM is responsible for interpreting visual information.

It may analyze:

* game screenshots
* HUD
* menus
* enemies
* bosses
* items
* player health
* game state
* important UI
* cinematics
* unusual events

The VLM should produce structured information.

Example:

```json
{
  "scene": "boss_fight",
  "important_event": true,
  "event": "player narrowly dodged boss attack",
  "player_health": "low",
  "enemy_health": "medium",
  "confidence": 0.89,
  "interestingness": 0.84
}
```

The schema can be improved during implementation.

Avoid generating long visual descriptions unless the user explicitly asks for them.

---

# 9. WEBCAM

The AI should optionally see the user.

Use OpenCV or an equivalent local camera interface.

The webcam can provide useful contextual information such as:

* smiling
* laughing
* surprise
* frustration
* excitement
* general reaction
* whether the user appears engaged with the game

The system must NOT attempt medical diagnosis or sensitive profiling.

Do not infer:

* medical conditions
* political beliefs
* religion
* race
* sexual orientation
* other sensitive personal characteristics

The webcam exists for gaming interaction.

---

# 10. WEBCAM PRIVACY

By default:

* webcam frames remain local
* frames are temporary
* no recording
* no permanent storage
* no cloud upload

The UI must clearly display:

```text
📷 CAMERA: ON
```

When camera access is disabled:

```text
📷 CAMERA: OFF
```

The user must always know when the camera is being processed.

---

# 11. EVENT DETECTION

The AI should not continuously ask the LLM:

"What is happening?"

Build a dedicated event detection system.

Pipeline:

```text
Screen
 ↓
Frame analysis
 ↓
Vision model
 ↓
Structured state
 ↓
Event detector
 ↓
Interestingness score
 ↓
AI decision
```

Events may include:

* death
* victory
* boss fight
* boss defeated
* rare item
* major enemy
* critical health
* unexpected event
* impressive move
* mistake
* funny event
* new area
* cinematic
* important dialogue
* menu
* game over
* achievement

Do not hard-code the system to a single game.

---

# 12. ATTENTION SYSTEM

The AI should behave like a person watching someone play.

It should NOT talk constantly.

Every event receives an importance score.

Example:

```text
0.00 - 0.30
Ignore.

0.30 - 0.60
Probably ignore.

0.60 - 0.80
Consider commenting.

0.80 - 1.00
Strong reason to comment.
```

Add configurable thresholds.

Also add speech cooldowns.

Example:

```text
minimum_speech_interval = 5 seconds
```

Direct user interaction overrides cooldowns.

The AI should prioritize:

1. direct user speech
2. major game events
3. funny/unusual events
4. important gameplay events
5. minor events

---

# 13. MAIN LLM

The LLM is the central reasoning engine.

Use a local model through a provider abstraction.

Initial provider:

```text
Ollama
```

But implement a provider interface so future providers can be added.

The LLM handles:

* reasoning
* conversation
* personality
* deciding whether to speak
* interpreting visual events
* combining RAG information
* combining memory
* generating responses
* deciding when tools are necessary

The LLM should not directly receive every raw frame.

It should receive structured context.

---

# 14. AI CONTEXT ENGINE

Create a central Context Engine.

It combines:

```text
User speech
+
Current game state
+
Vision events
+
Webcam context
+
Recent conversation
+
Relevant memory
+
RAG results
+
Game plugin information
+
AI personality
```

Example:

```text
CURRENT GAME:
Elden Ring

CURRENT EVENT:
Boss fight

PLAYER:
Health low

RECENT EVENTS:
Player almost defeated boss
Player died twice

MEMORY:
User usually uses a strength build

RAG:
Boss is weak to specific damage types

USER:
"Should I change my weapon?"
```

The context engine sends only relevant information to the LLM.

Do NOT dump the entire database into the prompt.

---

# 15. RAG SYSTEM

RAG stands for Retrieval-Augmented Generation.

RAG is NOT model training.

The RAG system provides external knowledge to the LLM when needed.

Create a local knowledge base.

Possible sources:

* game wikis
* game documentation
* strategy guides
* game mechanics
* item information
* boss information
* builds
* user-provided notes
* local documents

The knowledge should be stored locally.

---

# 16. RAG PIPELINE

Implement:

```text
Documents
 ↓
Text extraction
 ↓
Cleaning
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector database
 ↓
Retrieval
 ↓
Relevant chunks
 ↓
LLM context
```

The system should support semantic search.

Potential technologies:

* FAISS
* Chroma
* LanceDB
* SQLite-based vector storage
* another lightweight local vector database

Select the best practical option.

---

# 17. RAG CHUNKING

Do not blindly split every document into arbitrary fixed-size chunks.

Prefer semantic or structure-aware chunking when possible.

For example:

```text
Game
 └── Boss
      ├── Location
      ├── Attacks
      ├── Weaknesses
      ├── Rewards
      └── Strategy
```

Keep related information together when possible.

Store metadata:

```json
{
  "game": "Elden Ring",
  "category": "boss",
  "name": "example",
  "source": "local_document",
  "chunk_id": "..."
}
```

This allows filtering.

---

# 18. RAG RETRIEVAL

When the user asks:

> "What is this boss weak against?"

The system should:

```text
Question
 ↓
Query embedding
 ↓
Vector search
 ↓
Metadata filtering
 ↓
Top relevant chunks
 ↓
LLM
```

Do not retrieve unrelated information.

If the system does not know the answer, it should say so.

Never fabricate facts just because RAG returned weak results.

---

# 19. GAME-SPECIFIC RAG

RAG should understand the current game.

If the current game is:

```text
Elden Ring
```

prioritize:

```text
knowledge/elden_ring/
```

If:

```text
Minecraft
```

prioritize:

```text
knowledge/minecraft/
```

Do not mix unrelated games unless explicitly requested.

---

# 20. MEMORY SYSTEM

Memory is different from RAG.

RAG:

> "What does the game wiki say?"

Memory:

> "What happened to us previously?"

Implement three memory layers.

---

# 21. SHORT-TERM MEMORY

Contains:

* current conversation
* recent game events
* recent AI responses
* current game state

Example:

```text
10:30
Entered boss arena.

10:31
Player took heavy damage.

10:32
Player almost won.

10:33
Player died.
```

Short-term memory should be cleared or compressed when the session ends.

---

# 22. LONG-TERM MEMORY

Store useful persistent facts.

Examples:

```text
User prefers aggressive gameplay.

User frequently plays RPGs.

User prefers strength builds.

User dislikes excessive AI commentary.

User enjoys sarcastic humor.
```

Only store useful information.

Do not store every conversation message.

---

# 23. SESSION MEMORY

Every gaming session should have its own record.

Example:

```text
Session #42

Game:
Elden Ring

Duration:
2h 14m

Important events:
- 7 deaths
- 2 boss attempts
- 1 near victory
- 1 boss defeat

Memorable moments:
- successful dodge
- funny mistake
- boss victory
```

At the end of the session, the AI can generate a compact session summary.

---

# 24. MEMORY EXTRACTION

At appropriate times, run a memory extraction step.

For example:

```text
Conversation
+
Events
 ↓
Memory extractor
 ↓
Potential memories
 ↓
Importance filter
 ↓
Database
```

Only persist information that is actually useful.

Avoid saving trivial statements.

---

# 25. MEMORY DATABASE

Start with:

```text
SQLite
```

Possible tables:

```text
users
memories
sessions
session_events
conversations
game_profiles
documents
document_chunks
```

Add vector embeddings if required.

---

# 26. MEMORY RETRIEVAL

When generating a response:

```text
Current situation
 ↓
Memory search
 ↓
Relevant memories
 ↓
Context engine
 ↓
LLM
```

Example:

User:

> "Should I switch weapons?"

System retrieves:

```text
User usually uses strength builds.
```

Then the LLM can naturally respond:

> "You could, but you're running a strength build, so I'd probably keep..."

---

# 27. RAG VS MEMORY

Keep these concepts separate.

RAG:

```text
External knowledge
```

Memory:

```text
Personal/session knowledge
```

Do not mix the databases unnecessarily.

Architecture:

```text
             Context
                │
        ┌───────┴────────┐
        │                │
       RAG             Memory
        │                │
 Game knowledge     User experience
        │                │
        └───────┬────────┘
                ▼
               LLM
```

---

# 28. PERSONALITY

Default personality:

* playful
* sarcastic
* witty
* energetic
* conversational
* occasionally teasing
* supportive when appropriate
* excited by impressive gameplay
* amused by ridiculous mistakes
* quiet during boring moments

It should NOT constantly announce facts.

Avoid:

> "The player has successfully completed the action."

Prefer:

> "BRO THAT ACTUALLY WORKED 😭"

Avoid:

> "Would you like assistance?"

Prefer:

> "Okay, you're cooked. Want a strategy?"

The personality should be configurable.

Possible settings:

```text
sarcasm: 0-100
energy: 0-100
talkativeness: 0-100
humor: 0-100
supportiveness: 0-100
```

---

# 29. PERSONALITY TRAINING — FUTURE

Do NOT fine-tune the model initially.

First use:

* system prompts
* personality configuration
* memory
* RAG
* examples
* event logic

Later, optionally support fine-tuning.

Potential fine-tuning datasets could contain:

```text
Situation
Context
Desired response
```

Example:

```text
Situation:
Player dies to the same boss repeatedly.

Desired behavior:
Playfully tease the player without becoming genuinely insulting.
```

Fine-tuning is a future optimization, not Phase 1.

---

# 30. CUSTOM VOICE

Use modern neural TTS.

Evaluate:

* Kokoro
* Piper
* other current open-source local TTS models

The voice should sound:

* natural
* conversational
* expressive
* non-robotic

Support:

* voice selection
* speed
* pitch where supported
* interruption
* streaming

---

# 31. CUSTOM VOICE TRAINING

Do NOT train a TTS model from scratch.

Design the architecture so custom voice adaptation can be added later.

Potential future workflow:

```text
Voice recordings
 ↓
Cleaning
 ↓
Dataset
 ↓
Voice adaptation/fine-tuning
 ↓
Custom TTS model
```

Only use voices that the user has the right to use.

---

# 32. COMPUTER CONTROL

Implement a tool architecture.

Potential tools:

```text
take_screenshot()
open_application()
close_application()
move_mouse()
click()
press_key()
type_text()
read_clipboard()
```

However:

Computer control must be opt-in.

The AI must never silently control the computer.

Provide:

```text
Computer Control:
OFF
```

by default if appropriate.

Require confirmation for destructive or consequential actions.

Examples:

* deleting files
* executing shell commands
* changing security settings
* installing software
* sending messages
* purchases

---

# 33. GAME PLUGIN SYSTEM

Create a generic game plugin architecture.

Example:

```text
games/
    generic/
    plugins/
        elden_ring/
        minecraft/
        valorant/
```

Game plugins can optionally provide:

* game identification
* HUD parsing
* game-state information
* known events
* game-specific tools
* RAG filters

The AI must still function without a plugin.

---

# 34. OBSERVATION LOOP

The AI should have a continuous observation loop.

Conceptually:

```text
while running:

    capture_screen()

    detect_visual_change()

    if important_change:
        analyze_with_vision()

    capture_webcam_when_needed()

    detect_game_event()

    score_event()

    if event_is_interesting:
        send_context_to_agent()

    if user_is_speaking:
        prioritize_user()

    if AI_should_respond:
        generate_response()

    if response_ready:
        speak()
```

Do not implement this as a blocking infinite loop.

Use asynchronous workers and queues.

---

# 35. ASYNCHRONOUS ARCHITECTURE

Recommended architecture:

```text
Screen Capture Worker
        ↓
Observation Queue
        ↓
Vision Worker
        ↓
Event Queue
        ↓
Context Engine
        ↓
LLM Worker
        ↓
TTS Queue
        ↓
Audio Worker
```

Meanwhile:

```text
Microphone
    ↓
VAD
    ↓
STT
    ↓
User Event Queue
```

The system must remain responsive.

---

# 36. UI

Create a modern desktop interface.

Suggested dashboard:

```text
┌──────────────────────────────────────────────┐
│          AI GAMING COMPANION                 │
├──────────────────────────────────────────────┤
│                                              │
│ 🎤 Microphone       ● ACTIVE                 │
│ 📷 Webcam           ● ACTIVE                 │
│ 🖥 Screen            ● ACTIVE                │
│ 🧠 AI                ● READY                 │
│ 🔊 Voice             ● READY                 │
│                                              │
├──────────────────────────────────────────────┤
│ CURRENT GAME                                 │
│ Elden Ring                                   │
│                                              │
│ Boss Fight                                   │
│ Player HP: LOW                               │
│                                              │
├──────────────────────────────────────────────┤
│ RECENT EVENTS                                 │
│                                              │
│ ⚔ Boss attack detected                       │
│ 💀 Player died                               │
│ 🔥 Near victory                              │
│                                              │
├──────────────────────────────────────────────┤
│ MEMORY                                        │
│                                              │
│ 7 deaths this session                        │
│ Strength build                               │
│                                              │
├──────────────────────────────────────────────┤
│ CONVERSATION                                  │
│                                              │
│ You: am I cooked?                            │
│ AI: catastrophically 😭                      │
│                                              │
└──────────────────────────────────────────────┘
```

---

# 37. SETTINGS

Allow configuration of:

### AI

* LLM model
* vision model
* provider

### Voice

* STT model
* TTS model
* voice
* speed

### Personality

* sarcasm
* energy
* humor
* talkativeness
* supportiveness

### Vision

* screen monitoring
* webcam monitoring
* capture frequency
* resolution
* event sensitivity

### Memory

* enable/disable long-term memory
* session memory
* memory retention
* clear memory

### RAG

* knowledge directories
* vector database
* retrieval count
* similarity threshold

### Computer Control

* enabled/disabled
* confirmation requirements

---

# 38. PRIVACY

Core functionality must work locally.

Default behavior:

* microphone processed locally
* webcam processed locally
* screenshots processed locally
* no cloud uploads
* no permanent recording
* no automatic frame storage
* no automatic audio storage

Clearly show active sensors.

Provide buttons:

```text
Clear Session
Clear Memory
Delete Knowledge Base
Delete Stored Conversations
```

---

# 39. SECURITY

Treat computer-control tools as privileged operations.

The LLM must never be allowed to execute arbitrary commands without going through a permission layer.

Do not expose unrestricted shell execution to the LLM.

Use an allowlist/tool interface.

For example:

```text
LLM
 ↓
Tool request
 ↓
Permission manager
 ↓
Validation
 ↓
Execution
```

---

# 40. PERFORMANCE

Target:

* minimal gaming FPS impact
* low latency
* low VRAM usage
* asynchronous inference

Avoid analyzing every frame with a VLM.

Use:

* frame differencing
* adaptive sampling
* caching
* quantization
* asynchronous inference
* model persistence
* resolution scaling

Provide a performance monitor:

```text
GPU utilization
VRAM usage
CPU usage
RAM usage
capture FPS
vision latency
STT latency
LLM latency
TTS latency
```

---

# 41. LATENCY TARGETS

Aim for:

```text
Speech → STT:
< 1 second where possible

Visual event → analysis:
1-3 seconds

LLM:
2-4 seconds where practical

TTS:
begin speaking as soon as the first sentence is ready
```

These are targets, not guarantees.

Prioritize perceived responsiveness.

---

# 42. LOGGING

Use structured logging.

Example:

```text
[INFO] Application started
[INFO] GPU detected
[INFO] LLM loaded
[INFO] Vision model loaded
[INFO] STT loaded
[INFO] TTS loaded
[INFO] Screen capture started
[INFO] Webcam started

[EVENT] Boss fight detected
[EVENT] Player health critical
[EVENT] Player death

[AI] Response generated
[TTS] Speaking
```

Never log raw microphone recordings or webcam frames.

---

# 43. ERROR HANDLING

The application must degrade gracefully.

If webcam fails:

```text
Camera unavailable.
Continuing without webcam.
```

If TTS fails:

```text
Voice unavailable.
Text response remains available.
```

If VLM fails:

```text
Vision unavailable.
Continuing with game/audio context.
```

If LLM fails:

```text
AI brain unavailable.
Retrying...
```

If VRAM becomes insufficient:

* reduce workload
* unload optional models
* use CPU fallback if practical
* notify user

Do not crash the entire application.

---

# 44. PROJECT STRUCTURE

Suggested structure:

```text
gaming_ai/
│
├── app/
│   ├── main.py
│   ├── config.py
│   └── lifecycle.py
│
├── agent/
│   ├── agent.py
│   ├── personality.py
│   ├── decision.py
│   ├── context.py
│   └── prompts.py
│
├── vision/
│   ├── screen_capture.py
│   ├── webcam.py
│   ├── frame_analyzer.py
│   ├── vision_model.py
│   └── event_detector.py
│
├── speech/
│   ├── microphone.py
│   ├── vad.py
│   ├── stt.py
│   ├── tts.py
│   └── audio_player.py
│
├── memory/
│   ├── short_term.py
│   ├── long_term.py
│   ├── session.py
│   ├── database.py
│   └── retrieval.py
│
├── rag/
│   ├── ingestion.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   └── retriever.py
│
├── models/
│   ├── provider.py
│   ├── ollama.py
│   └── model_manager.py
│
├── computer/
│   ├── keyboard.py
│   ├── mouse.py
│   ├── applications.py
│   └── permissions.py
│
├── games/
│   ├── generic.py
│   └── plugins/
│
├── ui/
│
├── tests/
│
├── knowledge/
│
├── data/
│
└── main.py
```

You may change this architecture if you identify a substantially better design.

---

# 45. CONFIGURATION

Use YAML or TOML.

Example:

```yaml
ai:
  provider: ollama
  model: auto

vision:
  enabled: true
  model: auto
  capture_fps: 1
  resolution: "1280x720"

webcam:
  enabled: true
  fps: 1

speech:
  stt_model: auto
  tts_model: auto

personality:
  sarcasm: 70
  humor: 80
  energy: 70
  talkativeness: 40
  supportiveness: 70

memory:
  enabled: true
  long_term: true
  session_memory: true

rag:
  enabled: true
  top_k: 5

computer_control:
  enabled: false

privacy:
  save_webcam_frames: false
  save_screen_frames: false
  save_audio: false
```

Do not hard-code model names throughout the application.

---

# 46. KNOWLEDGE INGESTION

Create a system that lets the user add knowledge.

For example:

```text
knowledge/
    elden_ring/
    minecraft/
    general/
```

The application should be able to ingest:

* TXT
* Markdown
* PDF where practical
* HTML where practical
* user notes

The ingestion pipeline:

```text
Document
 ↓
Extract text
 ↓
Clean
 ↓
Chunk
 ↓
Generate embeddings
 ↓
Store
```

The UI should show ingestion progress.

---

# 47. RAG CITATION / SOURCE TRACKING

Every RAG chunk should retain source metadata.

Example:

```json
{
  "source": "elden_ring_boss_guide.md",
  "section": "Boss Weaknesses",
  "game": "elden_ring"
}
```

When the AI uses retrieved knowledge internally, it should know where that information came from.

If the UI displays factual RAG answers, optionally show:

```text
Source:
elden_ring_boss_guide.md
```

Never pretend retrieved information is certain when retrieval confidence is low.

---

# 48. SESSION SUMMARIZATION

At the end of each gaming session:

```text
Session events
+
Conversation
 ↓
Summarization model
 ↓
Session summary
 ↓
Memory extractor
 ↓
Important memories
```

Example:

```text
Session summary:

Played Elden Ring for 2h 14m.

Attempted Boss X seven times.

User nearly defeated the boss twice.

User prefers aggressive play.

User joked repeatedly about the boss.

Boss was eventually defeated.
```

Only persistent facts should be promoted to long-term memory.

---

# 49. FUTURE LEARNING

The system should eventually support optional learning from data.

Possible datasets:

### Personality dataset

```text
Context → preferred response
```

### Event dataset

```text
Screenshot → event label
```

### Voice dataset

```text
Audio → transcript
```

### Gaming behavior dataset

```text
Game state → event classification
```

However:

DO NOT implement expensive training during the initial version.

First build a strong inference system.

---

# 50. FINE-TUNING STRATEGY

When the system is mature:

1. Collect approved examples.
2. Clean data.
3. Remove sensitive/private information.
4. Label examples.
5. Evaluate baseline model.
6. Fine-tune a small adapter/LoRA.
7. Compare against baseline.
8. Keep fine-tuning only if it improves behavior.

Do not assume training automatically makes the AI better.

---

# 51. TESTING

Implement automated tests for:

* configuration
* model loading
* STT
* VAD
* TTS
* screen capture
* webcam
* vision parsing
* event detection
* RAG ingestion
* RAG retrieval
* memory
* session summaries
* personality
* permission system
* tool execution
* failure recovery

Create integration tests.

---

# 52. DIAGNOSTIC MODE

Provide a developer/diagnostic mode showing:

```text
GPU:
RTX 3070

VRAM:
X / 8192 MB

CPU:
X%

RAM:
X GB

Vision:
X ms

STT:
X ms

LLM:
X ms

TTS:
X ms

Capture:
X FPS

Events:
X / minute

AI responses:
X / minute
```

This is extremely important for optimizing the system.

---

# 53. DEVELOPMENT PHASES

Do NOT build the entire project in one step.

Use the following order.

## PHASE 0 — Research

Before writing the application:

1. Inspect hardware assumptions.
2. Research current open-source models.
3. Determine realistic RTX 3070-compatible models.
4. Estimate VRAM.
5. Identify Windows compatibility.
6. Select initial stack.
7. Explain the choices.

---

# PHASE 1 — Voice Prototype

Build:

```text
Microphone
 ↓
VAD
 ↓
Whisper
 ↓
LLM
 ↓
TTS
 ↓
Speaker
```

Verify natural conversation.

---

# PHASE 2 — Vision Prototype

Build:

```text
Screenshot
 ↓
VLM
 ↓
LLM
 ↓
TTS
```

I should be able to ask:

> "What is happening on my screen?"

and receive an answer.

---

# PHASE 3 — Webcam

Add:

```text
Webcam
 ↓
Vision
 ↓
Context
```

---

# PHASE 4 — Event Detection

Implement:

```text
Screen
 ↓
Change detection
 ↓
Vision
 ↓
Event classification
 ↓
Interestingness
```

---

# PHASE 5 — Autonomous Commentary

The AI can now decide:

```text
Something happened
 ↓
Is it interesting?
 ↓
Should I talk?
 ↓
Generate response
 ↓
TTS
```

This is where the companion begins to feel alive.

---

# PHASE 6 — RAG

Implement:

* document ingestion
* chunking
* embeddings
* vector database
* retrieval
* context integration

Test using one game first.

---

# PHASE 7 — Memory

Implement:

* short-term memory
* session memory
* long-term memory
* memory retrieval
* session summaries

---

# PHASE 8 — Personality

Implement configurable personality.

---

# PHASE 9 — Computer Tools

Implement permission-controlled computer interaction.

---

# PHASE 10 — Optimization

Optimize:

* VRAM
* latency
* FPS impact
* CPU usage
* RAM
* capture pipeline
* model loading
* RAG retrieval
* memory retrieval

---

# PHASE 11 — Optional Training

Only after the system works:

* collect datasets
* evaluate weaknesses
* fine-tune where useful
* experiment with custom voice
* experiment with specialized vision
* experiment with personality adapters

---

# 54. CRITICAL RULES

Follow these rules throughout development.

### Rule 1

Do not train a giant model from scratch.

### Rule 2

RAG is knowledge retrieval, not training.

### Rule 3

Memory is personal/session information, not model weights.

### Rule 4

Fine-tuning is optional and comes later.

### Rule 5

Do not sacrifice performance for unnecessary model size.

### Rule 6

Do not process every frame through a VLM.

### Rule 7

Do not make the AI talk constantly.

### Rule 8

Do not store webcam/microphone data by default.

### Rule 9

Do not give the LLM unrestricted shell access.

### Rule 10

Do not claim a feature works until it has been tested.

---

# 55. FINAL EXPERIENCE

The desired experience is:

I launch the AI.

I launch a game.

The AI detects the game.

I enable webcam and microphone.

The AI starts observing.

I play normally.

The AI stays quiet most of the time.

Something important happens.

The vision system detects it.

The event system determines it is interesting.

The context engine combines:

```text
Game event
+
Current screen
+
Webcam context
+
Conversation
+
Memory
+
RAG knowledge
+
Personality
```

The LLM generates a natural response.

TTS speaks it.

Example:

```text
Game:
Boss nearly defeated.

Memory:
Player has failed this boss 6 times.

Webcam:
Player appears excited.

AI:
"WAIT—YOU ACTUALLY GOT HIM THIS TIME. Don't you dare get greedy now 😭"
```

Then the AI becomes quiet again.

Later:

```text
User:
"How many times did I die?"

AI:
"Seven. I have unfortunately been keeping score."
```

The goal is for the AI to feel like a **gaming companion that is actually present**, rather than a chatbot with a microphone.

---

# 56. FIRST RESPONSE REQUIREMENT

Before writing large amounts of code, provide:

1. Recommended architecture.
2. Recommended models for an RTX 3070 8 GB.
3. Estimated VRAM usage.
4. Recommended STT.
5. Recommended VLM.
6. Recommended LLM.
7. Recommended TTS.
8. Recommended embedding model.
9. Recommended vector database.
10. Recommended memory database.
11. Recommended UI framework.
12. Recommended Python version.
13. Expected performance.
14. Biggest technical risks.
15. Phase 1 implementation plan.

Then implement **Phase 1 only**.

After Phase 1 works and is tested, proceed to Phase 2.

Do not skip phases.

The end goal is a fully local, modular, multimodal AI gaming companion with:

**Eyes 👁️ + Ears 👂 + Brain 🧠 + Voice 🔊 + Knowledge 📚 + Memory 🧠 + Tools 🖥️**
