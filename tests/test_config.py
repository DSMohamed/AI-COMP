"""Tests for configuration loading and validation."""

from pathlib import Path
import tempfile
import yaml
import pytest
from gaming_ai.app.config import AppConfig, get_config


def test_default_config() -> None:
    """Verify default configuration initialization."""
    cfg = AppConfig()
    assert cfg.ai.provider == "ollama"
    assert cfg.ai.model == "llama3.2:3b"
    assert cfg.personality.sarcasm == 75
    assert cfg.speech.sample_rate == 16000
    assert cfg.tts.rate == 185
    assert cfg.tts.interrupt_on_speech is True


def test_load_from_yaml(tmp_path: Path) -> None:
    """Verify YAML configuration loading and override."""
    test_yaml = {
        "ai": {
            "model": "qwen2.5-coder:7b",
            "temperature": 0.9,
        },
        "personality": {
            "name": "Cortana",
            "sarcasm": 90,
        },
    }
    file_path = tmp_path / "custom_config.yaml"
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(test_yaml, f)

    cfg = AppConfig.load_from_file(file_path)
    assert cfg.ai.model == "qwen2.5-coder:7b"
    assert cfg.ai.temperature == 0.9
    assert cfg.personality.name == "Cortana"
    assert cfg.personality.sarcasm == 90
    assert cfg.speech.sample_rate == 16000  # Fallback to default
