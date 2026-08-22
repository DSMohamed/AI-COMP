# 📚 Local AI Gaming Companion — Documentation

Welcome to the technical documentation for the **Local AI Gaming Companion**, a modular, local-first AI system designed to run alongside demanding games on consumer hardware (**NVIDIA GeForce RTX 3070 8 GB VRAM**).

---

## 📖 Documentation Index

| Section | Description |
|---|---|
| [🏗️ System Architecture](architecture.md) | High-level system architecture, decoupled async worker pipelines, and VRAM budgeting. |
| [🎙️ Speech & Voice Pipeline](speech_pipeline.md) | Microphone capture, VAD segmentation, `faster-whisper` STT, streaming TTS, and instant interruption. |
| [👁️ Vision & Screen Pipeline](vision_pipeline.md) | Screen capture, frame differencing, and VLM (`llava`/`qwen2-vl`) structured scene analysis. |
| [📷 Webcam & Reaction Pipeline](webcam_pipeline.md) | Privacy-safe player face, reaction, and engagement observation with zero disk storage. |
| [🎯 Event Detection & Attention](event_detection.md) | Game event classification, interestingness scoring, attention thresholds, and speech cooldowns. |
| [🎮 Autonomous Commentary Loop](autonomous_commentary.md) | Multimodal async observation loop, priority preemption, and live gaming dashboard. |
| [📚 Game-Specific RAG Knowledge](rag_knowledge.md) | ChromaDB vector storage, semantic markdown chunking, and grounded strategy retrieval. |
| [🧠 Multi-Layer Memory System](memory_system.md) | 4-tier memory hierarchy (Working, Session, Episodic, Semantic) with SQLite persistence. |
| [🖥️ Desktop Dashboard UI](dashboard_ui.md) | Glassmorphism web dashboard, live WebSocket telemetry, sensor badges, and sliders. |
| [🛠️ Sandboxed Computer Tools](computer_tools.md) | Safe tools framework, screenshot capture, timers, browser guides, and audit logging. |
| [⚡ Performance & VRAM Guard](performance_and_telemetry.md) | Latency targets, hardware monitoring, and dynamic 8 GB VRAM protection watchdog. |
| [🧪 Fine-Tuning & Custom Voice](fine_tuning_and_voice.md) | Synthetic dataset synthesis, 8GB QLoRA training scripts, and Ollama Modelfile packaging. |
| [🧠 Models & Providers](models_and_providers.md) | Ollama LLM provider abstraction, model configuration (`llama3.2:3b`, `qwen2.5:7b`), and custom provider guide. |
| [🎭 Personality & Agent](personality_and_agent.md) | Gaming companion persona, tone sliders (sarcasm, humor, energy, slang), and context aggregation. |
| [⚙️ Configuration Guide](configuration.md) | Detailed schema reference for `config.yaml` and runtime customization. |
| [⚡ Hardware & Optimization](hardware_and_optimization.md) | RTX 3070 8GB VRAM budgeting, CUDA configuration, latency benchmarks, and game coexistence. |
| [📚 API Reference](api_reference.md) | Python class and function reference across all core modules. |

---

## 🚀 Quick Navigation

* **Source Code**: [`gaming_ai/`](../gaming_ai/)
* **Configuration Template**: [`config.example.yaml`](../config.example.yaml)
* **Phases Checklist**: [Development Checklist](../CHECKLIST.md)
* **Open Source License**: [MIT License](../LICENSE)
* **Contributing**: [Contribution Guidelines](../CONTRIBUTING.md)
