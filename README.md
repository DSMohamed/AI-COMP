# 🎮 Local AI Gaming Companion

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Hardware: RTX 3070 8GB](https://img.shields.io/badge/Target%20GPU-RTX%203070%208GB-green.svg)](https://nvidia.com)
[![Local First](https://img.shields.io/badge/AI-100%25%20Local-purple.svg)](https://ollama.com)

A local-first, privacy-respecting, modular AI gaming companion designed to run completely offline on consumer hardware (**NVIDIA RTX 3070 8 GB VRAM**).

The companion acts like a real friend watching you play: listening via microphone, responding with witty neural voice commentary, observing gameplay events, and remembering your gaming journey across sessions.

---

## 🌟 Key Features

* 👂 **Real-time Local STT**: Instant speech recognition via `faster-whisper` and Voice Activity Detection (VAD).
* ⚡ **Natural Interruption**: Speak at any time to immediately cut off the AI's speech output.
* 🧠 **Modular LLM Brain**: Powered by local models (`llama3.2:3b`, `qwen2.5:7b`) via Ollama provider abstraction.
* 🎭 **Expressive Gaming Personality**: Configurable sarcasm, energy, humor, and natural gaming commentary.
* 🔒 **100% Privacy by Design**: Zero cloud uploads; all audio and frames are processed strictly in RAM/local GPU.
* 🎯 **8 GB VRAM Optimized**: Built specifically to leave GPU headroom for running demanding 3D games smoothly.

---

## 📐 Architecture

```
Microphone  ──► [ VAD Engine ] ──► [ faster-whisper STT ]
                                           │
                                           ▼
[ Personality Engine ] ────────► [ AI Context Aggregator ]
                                           │
                                           ▼
                                 [ Ollama LLM Stream ]
                                           │
                                           ▼
                                 [ Neural TTS Engine ] ──► Speakers
                                           ▲
                                           │ (Instant Cutoff)
                                [ Interruption Handler ]
```

---

## 🚀 Quick Start

### 1. Prerequisites
* **OS**: Windows 10/11 or Linux
* **GPU**: NVIDIA GPU with CUDA support (e.g., RTX 3070 8GB or compatible)
* **Python**: 3.10 – 3.12
* **Ollama**: [Download Ollama](https://ollama.com) and pull your preferred model:
  ```bash
  ollama pull llama3.2:3b
  ```

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/DSMohamed/AI-COMP.git
cd AI-COMP

# Create virtual environment
uv venv --python 3.12
.venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### 3. Launching the Companion
```bash
# Interactive Voice & Console Companion
python -m gaming_ai.main
```

---

## ⚙️ Configuration

Copy `config.example.yaml` to `config.yaml` to customize your companion's voice, personality, or AI model:

```yaml
ai:
  model: "llama3.2:3b"
  temperature: 0.7

personality:
  name: "Glitch"
  sarcasm: 75
  humor: 80
  energy: 75
  game_slang: true

speech:
  stt_model: "base.en"
  compute_type: "int8"
```

---

## 🧪 Running Tests

```bash
pytest -v
```

---

## 📚 Documentation

Detailed guides and API references are available in the [`docs/`](docs/index.md) folder:
* [🏗️ System Architecture](docs/architecture.md)
* [🎙️ Speech & Voice Pipeline](docs/speech_pipeline.md)
* [🧠 Models & Provider Guide](docs/models_and_providers.md)
* [🎭 Personality & Context Engine](docs/personality_and_agent.md)
* [⚙️ Configuration Reference](docs/configuration.md)
* [⚡ Hardware & Optimization Guide](docs/hardware_and_optimization.md)
* [📚 API Reference](docs/api_reference.md)

---

## 🗺️ Roadmap & Phases

See [`CHECKLIST.md`](CHECKLIST.md) for the detailed status of all 12 development phases.

- [x] **Phase 0**: Research, VRAM budgeting, and architecture design.
- [x] **Phase 1**: Voice Prototype (Microphone + VAD + faster-whisper + Ollama + TTS + Interruption).
- [x] **Phase 2**: Vision Prototype (Screen capture + FrameAnalyzer + Ollama VLM).
- [x] **Phase 3**: Webcam reaction & player engagement monitoring.
- [ ] **Phase 4**: Event detection & interestingness scoring.
- [ ] **Phase 5**: Autonomous gameplay commentary.
- [ ] **Phase 6**: Game-specific RAG knowledge base (ChromaDB).
- [ ] **Phase 7**: SQLite persistent multi-session memory.
- [ ] **Phase 8**: Dynamic personality tuning & desktop dashboard UI.
- [ ] **Phase 9**: Sandboxed computer control tools.
- [ ] **Phase 10**: Real-time telemetry overlay & VRAM optimization.
- [ ] **Phase 11**: Optional LoRA fine-tuning & voice cloning.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](file:///e:/MohamedWorks/AI/LICENSE) for more information.
