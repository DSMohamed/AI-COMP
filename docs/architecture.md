# 🏗️ System Architecture

## Overview
The **Local AI Gaming Companion** is engineered as a **modular, decoupled, event-driven system** to maintain high responsiveness while minimizing CPU and GPU contention during active PC gaming.

```
                                  ┌────────────────────────────────┐
                                  │      Ollama Local LLM Brain    │
                                  │     (llama3.2:3b / qwen2.5:7b) │
                                  └───────────────┬────────────────┘
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                ▼                                 ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│     Perception Engine         │ │       Context Aggregator      │ │      Actuation Engine         │
│  - Microphone (sounddevice)   │ │  - Persona system prompt      │ │  - Sentence Streaming TTS     │
│  - Energy & VAD segmentation  │ │  - Short-term turn history    │ │  - Non-blocking Audio Player  │
│  - faster-whisper STT (int8)  │ │  - Game context & state       │ │  - <20ms Instant Interruption │
└───────────────┬───────────────┘ └───────────────┬───────────────┘ └───────────────▲───────────────┘
                │                                 │                                 │
                └────────────────(Spoken Turn)────┴───────────(Speech Trigger)──────┘
```

---

## 🔄 The Turn Lifecycle (Voice Pipeline)

1. **Audio Capture**: `MicrophoneStream` continuously captures 16 kHz mono float32 audio via `sounddevice.InputStream` in 512-sample blocks (~32ms).
2. **Pre-roll Ring Buffer**: The stream continuously maintains a rolling 15-chunk buffer (~500ms) of pre-speech audio.
3. **Voice Activity Detection**:
   * `VoiceActivityDetector` measures RMS energy against an adaptive noise floor.
   * When speech onset is detected, it immediately fires the `on_speech_started` callback.
4. **Instant Interruption**:
   * If the companion is currently speaking, `tts.interrupt()` immediately signals `InterruptibleAudioPlayer` to stop speaker output, clear pending sentence synthesis queues, and reset audio buffers within $<20\text{ms}$.
5. **Speech Segmentation & Transcription**:
   * When silence reaches `vad_silence_duration` (default: 0.8s), the complete utterance is sent to `SpeechToText` (`faster-whisper base.en int8`).
   * Transcription completes in $\sim 150 - 250\text{ms}$.
6. **Context Construction**:
   * `ContextEngine` combines the personality system prompt, past conversation history, and user utterance into a clean message sequence.
7. **Streaming LLM Generation**:
   * `OllamaProvider` streams tokens via HTTP POST to `/api/chat`.
8. **Sentence-Level TTS Synthesis**:
   * `TextToSpeechEngine` splits the token stream into complete sentences by punctuation boundaries (`.`, `!`, `?`, `\n`) and synthesizes them asynchronously so audio starts playing before the LLM finishes generating the full response.

---

## 🎯 Concurrency & Threading Model

To ensure zero UI freezing and smooth game frame rates:
* **Audio Input Thread**: Driven by PortAudio native callback, pushing chunks to a thread-safe `queue.Queue`.
* **Audio Playback Worker**: Dedicated background daemon thread executing sequential speech chunks from `InterruptibleAudioPlayer`.
* **Main Asyncio Event Loop**: Orchestrates network I/O, LLM token streaming, and async agent turn processing without blocking the operating system.

---

## 📊 VRAM Budget Allocation (RTX 3070 8 GB)

| Component | Technology | Target Device | Allocated VRAM |
|---|---|---|---|
| Windows OS & Desktop DWM | Windows Display Driver | GPU | ~1.8 GB |
| Main LLM | `llama3.2:3b` (Q4_K_M) | GPU (CUDA) | ~2.0 GB |
| STT Engine | `faster-whisper base.en` | CPU / GPU (int8) | ~0.3 GB |
| Vision / VLM (Phases 2-5) | `qwen2-vl:2b` / `moondream2` | GPU (CUDA) | ~1.8 GB |
| Safety & CUDA Overhead | PyTorch / CUDA Runtime | GPU | ~1.1 GB |
| **Total Memory Footprint** | | | **~7.0 / 8.0 GB** |
