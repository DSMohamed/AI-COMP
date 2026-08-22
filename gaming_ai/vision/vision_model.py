"""Vision-Language Model (VLM) provider abstractions and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("gaming_ai.vision.vision_model")


@dataclass
class VisionAnalysisResult:
    """Structured perception output from the VLM."""
    description: str
    scene: str = "in_game"
    important_event: bool = False
    player_state: str = "normal"
    confidence: float = 0.85
    latency_ms: float = 0.0
    raw_response: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseVisionModel(ABC):
    """Abstract interface for local Vision-Language Models."""

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        self.model_name = model_name
        self.kwargs = kwargs

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if vision model is loaded and reachable."""
        pass

    @abstractmethod
    async def analyze(
        self,
        image_base64: str,
        prompt: Optional[str] = None,
        structured: bool = True,
    ) -> VisionAnalysisResult:
        """Analyze a base64 encoded image and return structured perception results."""
        pass


class OllamaVisionModel(BaseVisionModel):
    """VLM client using local Ollama vision backends (e.g., llava, qwen2-vl, moondream)."""

    def __init__(
        self,
        model_name: str = "llava:latest",
        host: str = "http://127.0.0.1:11434",
        timeout: float = 45.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(model_name=model_name, **kwargs)
        self.host = host.rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if Ollama server is running and the VLM model is installed."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.host}/api/tags")
                if res.status_code != 200:
                    return False
                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(self.model_name in m or m.startswith(self.model_name.split(":")[0]) for m in models)
        except Exception as e:
            logger.warning("VLM availability check failed: %s", e)
            return False

    async def analyze(
        self,
        image_base64: str,
        prompt: Optional[str] = None,
        structured: bool = True,
    ) -> VisionAnalysisResult:
        """Perform vision analysis on an image."""
        if structured:
            system_instruction = (
                "You are an AI gaming vision engine. Analyze this video game screenshot concisely.\n"
                "Return a valid JSON object with EXACTLY these keys:\n"
                '{\n'
                '  "scene": "boss_fight|combat|exploration|menu|death_screen|victory|loading|cutscene",\n'
                '  "important_event": true or false,\n'
                '  "player_state": "normal|low_health|critical|dead|winning",\n'
                '  "summary": "1 to 2 sentence gaming description of what is visible"\n'
                '}\n'
                "DO NOT wrap in markdown code blocks. Output ONLY raw JSON."
            )
            actual_prompt = prompt or system_instruction
        else:
            actual_prompt = prompt or "Briefly describe what is happening in this game screenshot in 1-2 punchy sentences."

        payload = {
            "model": self.model_name,
            "prompt": actual_prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.2 if structured else 0.7,
                "num_predict": 120,
            },
        }

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(f"{self.host}/api/generate", json=payload)
                res.raise_for_status()
                data = res.json()
                raw_text = data.get("response", "").strip()
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                if structured:
                    # Clean markdown codeblocks if model returned them
                    clean_json = raw_text
                    if "```json" in clean_json:
                        clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                    elif "```" in clean_json:
                        clean_json = clean_json.split("```")[1].split("```")[0].strip()

                    try:
                        parsed = json.loads(clean_json)
                        return VisionAnalysisResult(
                            description=parsed.get("summary", raw_text),
                            scene=parsed.get("scene", "in_game"),
                            important_event=bool(parsed.get("important_event", False)),
                            player_state=parsed.get("player_state", "normal"),
                            confidence=0.9,
                            latency_ms=latency_ms,
                            raw_response=raw_text,
                        )
                    except json.JSONDecodeError:
                        logger.warning("VLM output was not valid JSON, using raw text: %s", raw_text)

                return VisionAnalysisResult(
                    description=raw_text,
                    scene="in_game",
                    important_event=False,
                    player_state="normal",
                    confidence=0.85,
                    latency_ms=latency_ms,
                    raw_response=raw_text,
                )

            except Exception as e:
                logger.error("VLM inference failed: %s", e)
                raise


class MockVisionModel(BaseVisionModel):
    """Deterministic mock vision model for offline unit tests and CI."""

    def __init__(
        self,
        model_name: str = "mock-vision",
        canned_result: Optional[VisionAnalysisResult] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model_name=model_name, **kwargs)
        self.canned_result = canned_result or VisionAnalysisResult(
            description="Player is facing an Elden Ring boss with low health.",
            scene="boss_fight",
            important_event=True,
            player_state="low_health",
            confidence=0.95,
            latency_ms=12.0,
        )

    async def is_available(self) -> bool:
        return True

    async def analyze(
        self,
        image_base64: str,
        prompt: Optional[str] = None,
        structured: bool = True,
    ) -> VisionAnalysisResult:
        return self.canned_result
