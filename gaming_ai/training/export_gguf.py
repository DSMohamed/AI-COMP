"""Ollama Modelfile generator and LoRA export pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gaming_ai.training.export_gguf")


def export_ollama_modelfile(
    base_model: str = "llama3.2:3b",
    adapter_path: Optional[str] = "models/gaming_companion_lora",
    companion_name: str = "Glitch",
    system_prompt: Optional[str] = None,
    output_path: str | Path = "Modelfile",
) -> str:
    """
    Generate a ready-to-use Ollama Modelfile for packaging the fine-tuned companion model.
    """
    default_prompt = (
        f"You are {companion_name}, a friendly, funny, and skilled AI gaming companion sitting beside the player. "
        "You react authentically to gameplay events, banter with sarcasm, offer concise tactical tips, "
        "and celebrate clutch victories. Keep responses concise (1-3 sentences max)."
    )
    sys_prompt = system_prompt or default_prompt

    lines = [
        f"FROM {base_model}",
    ]

    if adapter_path and Path(adapter_path).exists():
        lines.append(f"ADAPTER {adapter_path}")

    lines.extend([
        "PARAMETER temperature 0.7",
        "PARAMETER top_p 0.9",
        "PARAMETER top_k 40",
        'PARAMETER stop "<|eot_id|>"',
        'PARAMETER stop "<|end_of_text|>"',
        f'SYSTEM """{sys_prompt}"""',
    ])

    content = "\n".join(lines) + "\n"
    out = Path(output_path)
    out.write_text(content, encoding="utf-8")

    logger.info("Ollama Modelfile generated at %s", out)
    return content
