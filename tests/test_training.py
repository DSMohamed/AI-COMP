"""Tests for DatasetGenerator, LoRA training pipeline, and Ollama Modelfile export."""

from pathlib import Path
import pytest

from gaming_ai.training.dataset_generator import DatasetGenerator, DialogueSample
from gaming_ai.training.export_gguf import export_ollama_modelfile
from gaming_ai.training.train_lora import LoRATrainingConfig, build_training_pipeline


def test_dataset_generator() -> None:
    """Verify synthetic dataset generation and ChatML serialization."""
    gen = DatasetGenerator()
    samples = gen.generate_seed_dataset()

    assert len(samples) >= 5
    first = samples[0]
    assert isinstance(first, DialogueSample)
    assert first.game != ""
    assert len(first.messages) == 2

    chatml = first.to_chatml()
    assert "messages" in chatml
    assert chatml["messages"][0]["role"] == "system"
    assert chatml["messages"][1]["role"] == "user"
    assert chatml["messages"][2]["role"] == "assistant"


def test_dataset_jsonl_export(tmp_path: Path) -> None:
    """Verify exporting dataset to valid JSONL format."""
    gen = DatasetGenerator()
    samples = gen.generate_seed_dataset()

    out_file = tmp_path / "test_dataset.jsonl"
    path = gen.export_jsonl(samples, output_file=out_file)

    assert Path(path).exists()
    lines = Path(path).read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == len(samples)


def test_lora_training_script_builder() -> None:
    """Verify training script contains key 8GB VRAM QLoRA optimizations."""
    cfg = LoRATrainingConfig(
        base_model_name="meta-llama/Llama-3.2-3B-Instruct",
        lora_r=16,
        batch_size=2,
    )
    script = build_training_pipeline(cfg)

    assert "BitsAndBytesConfig" in script
    assert "load_in_4bit=True" in script
    assert "LoraConfig" in script
    assert "SFTTrainer" in script


def test_ollama_modelfile_export(tmp_path: Path) -> None:
    """Verify Ollama Modelfile structure and syntax."""
    out_modelfile = tmp_path / "Modelfile"
    content = export_ollama_modelfile(
        base_model="llama3.2:3b",
        companion_name="Glitch",
        output_path=out_modelfile,
    )

    assert out_modelfile.exists()
    assert "FROM llama3.2:3b" in content
    assert "SYSTEM" in content
    assert "Glitch" in content
