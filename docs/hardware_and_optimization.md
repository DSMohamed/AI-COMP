# ⚡ Hardware & VRAM Optimization Guide

This guide details how the system is engineered to run seamlessly alongside modern 3D games on an **NVIDIA GeForce RTX 3070 (8 GB VRAM)**.

---

## 🛑 The 8 GB VRAM Challenge

Modern PC gaming requires 4–6 GB of VRAM. If an AI assistant consumes too much memory, Windows will either page VRAM to system RAM (causing severe frame rate drops) or trigger a CUDA Out-Of-Memory (OOM) crash.

---

## 🎯 5 Core Optimization Strategies

### 1. 3B Parameter Class LLMs (`llama3.2:3b`)
* Consumes only **~2.0 GB VRAM** in 4-bit quantization (Q4_K_M).
* Generates tokens at **> 120 tokens/second** on RTX 3070 CUDA cores.
* Response latency is instantaneous ($< 250\text{ms}$ to first token).

### 2. Int8 Quantization for STT (`faster-whisper`)
* Running `faster-whisper base.en` in `int8` uses less than **300 MB of VRAM** (or can run on CPU with zero VRAM impact).

### 3. CPU Offloading for VAD & TTS
* Voice Activity Detection (RMS energy / Silero ONNX) runs entirely on CPU threads.
* TTS audio synthesis runs on CPU via native Windows SAPI5 / ONNX runtime, conserving all GPU compute and memory for graphics rendering.

### 4. Dynamic Frame Throttling (Phases 2-5)
* Screen capture does NOT send every 60/144 FPS game frame to the vision model.
* A cheap frame-differencing algorithm only invokes the vision model when significant visual changes occur (e.g. death screen, boss health bar appearance, victory banner).

### 5. Unified Local Inference Backend
* Running models through **Ollama** ensures optimized CUDA memory management and unified GGUF weight caching.
