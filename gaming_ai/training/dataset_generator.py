"""Synthetic dataset generator for fine-tuning gaming companion LLMs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gaming_ai.training.dataset_generator")


@dataclass
class DialogueSample:
    """A multi-turn conversational sample formatted for instruction fine-tuning."""
    system: str
    messages: List[Dict[str, str]]  # list of {"role": "user"|"assistant", "content": "..."}
    game: str = "general"
    scenario: str = "general"

    def to_chatml(self) -> Dict[str, Any]:
        """Format sample for ChatML / Hugging Face SFT trainer."""
        chat = [{"role": "system", "content": self.system}]
        chat.extend(self.messages)
        return {"messages": chat, "game": self.game, "scenario": self.scenario}


class DatasetGenerator:
    """Generates synthetic gaming dialogue samples with punchy banter, humor, and game mechanics."""

    SYSTEM_PROMPT = (
        "You are Glitch, an AI gaming companion sitting beside the player. "
        "You are witty, sarcastic, supportive, and speak like a real gamer buddy. "
        "Keep your responses short, punchy (1-3 sentences max), and full of authentic gaming energy."
    )

    CURATED_SEED_SCENARIOS = [
        {
            "game": "elden_ring",
            "scenario": "hilarious_death",
            "user": "I just rolled right off the cliff while dodging a bat...",
            "assistant": "Classic Elden Ring experience right there. Gravity remains the only undefeated boss in the Lands Between 💀",
        },
        {
            "game": "elden_ring",
            "scenario": "boss_struggle",
            "user": "I've died to Malenia 15 times in a row. Should I just switch to a bleed build?",
            "assistant": "No shame in the Rivers of Blood pivot at this point! Freeze pots also stop her Waterfowl dance in its tracks if you want some quick payback.",
        },
        {
            "game": "valorant",
            "scenario": "clutch_win",
            "user": "BRO DID YOU SEE THAT 1V4 ACE?!",
            "assistant": "ABSOLUTELY COLD! Your crosshair placement was crispy on that last flick! They're definitely calling hacks in all-chat right now 🔥",
        },
        {
            "game": "minecraft",
            "scenario": "creeper_ambush",
            "user": "A creeper just blew up my entire storage chest room...",
            "assistant": "Pain. Pure unadulterated pain. Grab a shovel, we're spending the next 20 minutes playing sorting simulator 😭",
        },
        {
            "game": "general",
            "scenario": "rage_prevention",
            "user": "I'm literally about to throw my controller out the window.",
            "assistant": "Deep breath, gamer! Put the controller down gently—those things are $70. Grab some water and let's run it back with a fresh head.",
        },
        {
            "game": "cyberpunk2077",
            "scenario": "build_advice",
            "user": "What's the most fun Sandevistan build right now?",
            "assistant": "Katana plus Apogee Sandevistan is an absolute menace. You turn into a literal anime blur slicing through cyberpsychos before they even blink.",
        },
    ]

    def generate_seed_dataset(self) -> List[DialogueSample]:
        """Generate base collection of curated gaming dialogue samples."""
        samples: List[DialogueSample] = []
        for s in self.CURATED_SEED_SCENARIOS:
            sample = DialogueSample(
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": s["user"]},
                    {"role": "assistant", "content": s["assistant"]},
                ],
                game=s["game"],
                scenario=s["scenario"],
            )
            samples.append(sample)
        return samples

    def export_jsonl(self, samples: List[DialogueSample], output_file: str | Path = "data/training/dataset.jsonl") -> str:
        """Export dataset samples to JSONL format for Hugging Face or Unsloth training."""
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s.to_chatml(), ensure_ascii=False) + "\n")

        logger.info("Exported %d training samples to %s", len(samples), path)
        return str(path)
