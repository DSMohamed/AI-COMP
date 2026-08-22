# Contributing to Local AI Gaming Companion

Thank you for your interest in contributing to the **Local AI Gaming Companion**! This project is open source and community-driven, built around modular AI systems optimized for local consumer hardware (RTX 3070 8GB).

## Code of Conduct
* Be respectful, collaborative, and constructive.
* Respect privacy: do not commit personal gaming logs, voice recordings, or proprietary keys.

## Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/DSMohamed/AI-COMP.git
   cd AI-COMP
   ```

2. **Set up Virtual Environment**:
   ```bash
   uv venv --python 3.12
   .venv\Scripts\activate   # Windows
   # or source .venv/bin/activate (Linux/macOS)
   ```

3. **Install Dependencies**:
   ```bash
   uv pip install -e . -r requirements-dev.txt
   ```

4. **Start Ollama Backend**:
   Ensure Ollama is installed and running with a compatible model:
   ```bash
   ollama serve
   ollama pull llama3.2:3b
   ```

5. **Run Tests**:
   ```bash
   pytest
   ```

## Development Guidelines

### Modular Architecture
Each subsystem is isolated in its respective directory:
* `gaming_ai/speech/`: Microphone, VAD, STT, and TTS.
* `gaming_ai/models/`: LLM providers and streaming backends.
* `gaming_ai/agent/`: Personality, prompt engine, and context orchestrator.
* `gaming_ai/memory/`: SQLite short-term, session, and long-term memory.
* `gaming_ai/rag/`: ChromaDB / LanceDB document chunking and vector retrieval.
* `gaming_ai/vision/`: Screen capture, webcam, and VLM event parsing.

### Adding a New Model Provider
To add a new LLM provider, inherit from `gaming_ai.models.provider.BaseLLMProvider` and implement the `generate_stream()` and `generate()` async methods.

### Code Style & Quality
* Format code with standard Python typing hints (`typing`).
* Follow PEP 8 guidelines.
* Include docstrings for public classes and functions.
* Add unit tests in `tests/` for all new features.
