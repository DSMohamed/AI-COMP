"""Configuration management with Pydantic and YAML support."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """Configuration for LLM reasoning brain."""
    provider: str = Field(default="ollama", description="LLM provider: 'ollama' or 'mock'")
    host: str = Field(default="http://127.0.0.1:11434", description="Ollama API base URL")
    model: str = Field(default="llama3.2:3b", description="Model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=150, ge=1, le=4096)
    request_timeout: float = Field(default=30.0, ge=1.0)


class SpeechConfig(BaseModel):
    """Configuration for speech input and recognition."""
    input_device: Optional[int] = Field(default=None, description="Audio input device index")
    sample_rate: int = Field(default=16000, description="Whisper target sample rate")
    stt_model: str = Field(default="base.en", description="faster-whisper model name")
    device: str = Field(default="auto", description="'cuda' or 'cpu'")
    compute_type: str = Field(default="int8", description="'int8' or 'float16'")
    vad_mode: str = Field(default="hybrid", description="'energy', 'silero', or 'hybrid'")
    vad_silence_duration: float = Field(default=0.8, ge=0.1, le=5.0)
    vad_energy_threshold: float = Field(default=0.015, ge=0.0001, le=1.0)


class TTSConfig(BaseModel):
    """Configuration for Text-to-Speech output."""
    engine: str = Field(default="pyttsx3", description="TTS backend: 'pyttsx3', 'piper', etc.")
    rate: int = Field(default=185, ge=50, le=400, description="Speech rate in WPM")
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    voice_index: int = Field(default=0, ge=0)
    interrupt_on_speech: bool = Field(default=True, description="Cut off TTS when user starts speaking")


class PersonalityConfig(BaseModel):
    """Configuration for gaming companion personality."""
    name: str = Field(default="Glitch", description="Companion name")
    sarcasm: int = Field(default=75, ge=0, le=100)
    humor: int = Field(default=80, ge=0, le=100)
    energy: int = Field(default=75, ge=0, le=100)
    talkativeness: int = Field(default=50, ge=0, le=100)
    supportiveness: int = Field(default=65, ge=0, le=100)
    game_slang: bool = Field(default=True)
    custom_system_prompt: str = Field(default="")


class MemoryConfig(BaseModel):
    """Configuration for memory database."""
    enabled: bool = Field(default=True)
    database_path: str = Field(default="data/memory.sqlite")
    short_term_history_limit: int = Field(default=10, ge=1)


class VisionConfig(BaseModel):
    """Configuration for screen and webcam perception."""
    enabled: bool = Field(default=False)
    model: str = Field(default="qwen2-vl:2b")
    capture_fps: int = Field(default=1, ge=1, le=60)
    resolution: str = Field(default="1280x720")
    webcam_enabled: bool = Field(default=False)


class PrivacyConfig(BaseModel):
    """Configuration for privacy safeguards."""
    save_audio_recordings: bool = Field(default=False)
    save_screen_frames: bool = Field(default=False)
    save_webcam_frames: bool = Field(default=False)


class AppConfig(BaseModel):
    """Root application configuration."""
    ai: AIConfig = Field(default_factory=AIConfig)
    speech: SpeechConfig = Field(default_factory=SpeechConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)

    @classmethod
    def load_from_file(cls, config_path: str | Path) -> AppConfig:
        """Load configuration from a YAML file, falling back to defaults if missing."""
        path = Path(config_path)
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

    def save_to_file(self, config_path: str | Path) -> None:
        """Serialize configuration to a YAML file."""
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


_global_config: Optional[AppConfig] = None


def get_config(config_path: Optional[str | Path] = None) -> AppConfig:
    """Retrieve global configuration singleton or load from custom path."""
    global _global_config
    if _global_config is None:
        if config_path:
            _global_config = AppConfig.load_from_file(config_path)
        else:
            # Check for config.yaml, then config.example.yaml, else defaults
            if Path("config.yaml").exists():
                _global_config = AppConfig.load_from_file("config.yaml")
            elif Path("config.example.yaml").exists():
                _global_config = AppConfig.load_from_file("config.example.yaml")
            else:
                _global_config = AppConfig()
    return _global_config
