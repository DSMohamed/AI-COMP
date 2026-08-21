# 📋 Development Phases Checklist

This checklist tracks the implementation progress of the **Local AI Gaming Companion** according to the technical specification in [`local-ai-gaming-companion-spec.md`](local-ai-gaming-companion-spec.md).

---

## 📊 Summary Status

* **Total Phases**: 12 (Phases 0 through 11)
* **Completed Phases**: 2 / 12 (Phase 0, Phase 1 + Core Personality)
* **In Progress / Next Up**: Phase 2 (Vision Prototype)
* **Target Hardware**: NVIDIA GeForce RTX 3070 (8 GB VRAM) — Windows 10/11

---

## 🚀 Phase-by-Phase Breakdown

### ✅ Phase 0 — Research & Architecture (COMPLETED)
- [x] Inspect 8 GB VRAM hardware budget constraints for RTX 3070.
- [x] Research and select open-source models (`llama3.2:3b`, `faster-whisper int8`, `nomic-embed`, `qwen2-vl:2b`).
- [x] Design modular, decoupled async pipeline architecture.
- [x] Create open-source foundation (MIT License, `pyproject.toml`, `.gitignore`, `CONTRIBUTING.md`, `README.md`, `docs/`).

### ✅ Phase 1 — Voice Prototype (COMPLETED)
- [x] Audio capture stream (`sounddevice` with pre-roll buffering).
- [x] Voice Activity Detection (`VoiceActivityDetector` with adaptive noise floor).
- [x] Local Speech-to-Text (`faster-whisper` `base.en` with int8 quantization).
- [x] Async Ollama LLM provider client (`llama3.2:3b` with streaming support).
- [x] Sentence-level streaming TTS engine (`pyttsx3`).
- [x] Instant speech interruption ($<20\text{ms}$ audio cancellation when player speaks).
- [x] Configurable companion personality prompt engine (sarcasm, humor, energy, slang).
- [x] Interactive CLI runner supporting `--mode voice` and `--mode text`.
- [x] Automated test suite (12 passing unit & integration tests).

---

### ⏳ Phase 2 — Vision Prototype (NEXT UP)
- [ ] Low-overhead Windows screen capture (DXGI Desktop Duplication / Windows Graphics Capture / MSS).
- [ ] Image resizing and optimization pipeline (1280x720 downscaled frames).
- [ ] VLM integration (lightweight vision-language model e.g., `qwen2-vl:2b` or `moondream2` / `llava`).
- [ ] Visual query command (*"What is happening on my screen?"*).
- [ ] Automated tests for frame grabber and VLM parser.

---

### ⏳ Phase 3 — Webcam Integration (REMAINING)
- [ ] OpenCV webcam capture module with configurable FPS (default: 1 FPS).
- [ ] Player engagement & facial reaction parser (smiling, surprise, frustration).
- [ ] Privacy safeguards (strictly in-memory frames, zero disk storage, clear UI camera toggle).
- [ ] Integration into multimodal AI context.

---

### ⏳ Phase 4 — Event Detection & Interestingness (REMAINING)
- [ ] Fast frame differencing to avoid sending redundant frames to VLM.
- [ ] Structured game event classification (boss fights, low HP, deaths, victories, rare loot).
- [ ] Event interestingness scoring (0.0 to 1.0 thresholding).
- [ ] Dynamic event queue for the agent brain.

---

### ⏳ Phase 5 — Autonomous Commentary (REMAINING)
- [ ] Background observation loop without infinite blocking.
- [ ] Attention thresholding (ignore 0.0–0.6, consider 0.6–0.8, talk on 0.8–1.0).
- [ ] Speech cooldown timer (minimum interval between autonomous comments).
- [ ] Priority resolution (User Speech > Major Events > Minor Events).

---

### ⏳ Phase 6 — Game-Specific RAG Knowledge Base (REMAINING)
- [ ] Document ingestion pipeline (TXT, Markdown, Wiki guides).
- [ ] Semantic chunking preserving boss/item/mechanics metadata.
- [ ] Vector database integration (ChromaDB / LanceDB).
- [ ] Embeddings generation with `nomic-embed-text`.
- [ ] Game-filtered semantic retrieval into LLM prompt context with source citation.

---

### ⏳ Phase 7 — Multi-Layer Memory System (REMAINING)
- [ ] SQLite memory database schema (`sessions`, `memories`, `conversations`, `events`).
- [ ] Short-Term Memory (live session rolling history).
- [ ] Long-Term Memory (persistent user preferences, playstyle facts, build types).
- [ ] End-of-session summarizer and memory extraction pipeline.
- [ ] Semantic memory retrieval during active gameplay.

---

### ⏳ Phase 8 — Desktop Dashboard UI (REMAINING)
- [ ] Modern dark-mode GUI (CustomTkinter or Lightweight Webview Dashboard).
- [ ] Live sensor status badges (🎤 Mic, 📷 Webcam, 🖥️ Screen, 🧠 AI, 🔊 Voice).
- [ ] Real-time conversation & event transcript feed.
- [ ] Settings panel for live personality slider adjustments.
- [ ] One-click privacy controls (*Clear Session*, *Clear Memory*).

---

### ⏳ Phase 9 — Computer Control Tools (REMAINING)
- [ ] Opt-in privileged tool framework (disabled by default).
- [ ] Sandboxed actions (taking screenshots, reading clipboard, opening apps).
- [ ] Confirmation prompt layer for consequential actions.

---

### ⏳ Phase 10 — Performance Optimization & Diagnostics (REMAINING)
- [ ] Real-time telemetry overlay (GPU utilization, VRAM MB, CPU%, STT latency, LLM latency).
- [ ] Dynamic VRAM manager (automatic model unloading if VRAM exceeds 7.2 GB).
- [ ] Frame rate benchmarking to guarantee < 2% game FPS impact.

---

### ⏳ Phase 11 — Optional Fine-Tuning & Learning (FUTURE)
- [ ] Curated dataset collector for approved companion responses.
- [ ] LoRA adapter fine-tuning for specialized game banter.
- [ ] Custom neural voice cloning adaptation pipeline.
