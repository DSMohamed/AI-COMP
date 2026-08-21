# 📚 API Reference

Comprehensive class and module reference for the **Local AI Gaming Companion** core package (`gaming_ai`).

---

## 📦 `gaming_ai.agent`

### `GamingCompanionAgent`
`gaming_ai.agent.agent.GamingCompanionAgent(config=None, llm_provider=None, stt=None, tts=None)`
* Central orchestrator connecting voice input, STT, LLM reasoning, TTS, and interruption handling.
* **Methods**:
  * `async respond_to_text(user_text: str, speak: bool = True) -> str`: Process player text query, stream LLM completion, and optionally speak via TTS.
  * `async run_voice_loop(on_transcription=None, on_response=None) -> None`: Start continuous asynchronous voice listening loop.
  * `start_microphone() -> None`: Begin recording audio from microphone.
  * `stop_microphone() -> None`: Stop microphone audio capture.

### `PersonalityEngine`
`gaming_ai.agent.personality.PersonalityEngine(config=None)`
* Builds gaming companion system prompts dynamically from personality sliders.
* **Methods**:
  * `build_system_prompt(current_game: Optional[str] = None) -> str`: Returns the formatted system prompt.

### `ContextEngine`
`gaming_ai.agent.context.ContextEngine(personality_engine=None, history_limit=10)`
* Maintains conversation history and compiles message payload for LLMs.
* **Methods**:
  * `add_user_message(text: str) -> None`
  * `add_assistant_message(text: str) -> None`
  * `build_context(current_user_input: Optional[str] = None) -> List[Message]`
  * `clear_history() -> None`

---

## 🎙️ `gaming_ai.speech`

### `VoiceActivityDetector`
`gaming_ai.speech.vad.VoiceActivityDetector(energy_threshold=0.015, silence_duration_threshold=0.8, sample_rate=16000)`
* Frame-by-frame speech detection and dynamic ambient noise floor tracking.
* **Methods**:
  * `calculate_energy(audio_chunk: np.ndarray) -> float`: Returns RMS energy.
  * `process_chunk(audio_chunk: np.ndarray) -> Tuple[bool, bool, bool]`: Returns `(is_speaking, speech_started, speech_ended)`.

### `MicrophoneStream`
`gaming_ai.speech.microphone.MicrophoneStream(sample_rate=16000, chunk_size=512, device=None, on_speech_started=None)`
* Continuous audio recording using `sounddevice` with rolling pre-roll buffer.
* **Methods**:
  * `start() -> None`: Start recording stream.
  * `stop() -> None`: Stop stream and release audio device.
  * `get_utterance(timeout=0.1) -> Optional[np.ndarray]`: Returns full audio utterance on speech completion.

### `SpeechToText`
`gaming_ai.speech.stt.SpeechToText(model_size="base.en", device="auto", compute_type="int8")`
* Speech-to-text transcription engine powered by `faster-whisper`.
* **Methods**:
  * `transcribe(audio: np.ndarray, language="en") -> Tuple[str, float]`: Returns `(transcription_text, latency_ms)`.

### `InterruptibleAudioPlayer`
`gaming_ai.speech.audio_player.InterruptibleAudioPlayer()`
* Thread-safe audio playback queue with instant interrupt cancellation.
* **Methods**:
  * `play(play_fn: Callable[[], None]) -> None`: Enqueue speech audio playback task.
  * `interrupt() -> None`: Immediately cancel playing speech and drain queue.

### `TextToSpeechEngine`
`gaming_ai.speech.tts.TextToSpeechEngine(engine_type="pyttsx3", rate=185, volume=1.0, voice_index=0, player=None)`
* Synthesizes speech with sentence-level streaming.
* **Methods**:
  * `speak(text: str) -> None`: Enqueue single speech string.
  * `async speak_stream(token_stream: AsyncIterator[str]) -> str`: Stream tokens, synthesize sentences as soon as completed, and return full response text.

---

## 🧠 `gaming_ai.models`

### `BaseLLMProvider`
`gaming_ai.models.provider.BaseLLMProvider(model_name, **kwargs)`
* Abstract base class for all LLM backend providers.

### `OllamaProvider`
`gaming_ai.models.ollama.OllamaProvider(model_name="llama3.2:3b", host="http://127.0.0.1:11434", timeout=30.0)`
* Async HTTP streaming client for local Ollama instances.

### `MockLLMProvider`
`gaming_ai.models.provider.MockLLMProvider(model_name="mock-model", canned_response="...")`
* Deterministic mock LLM for unit tests and CI.
