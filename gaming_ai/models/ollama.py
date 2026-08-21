"""Ollama LLM Provider implementation using async HTTP API."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from gaming_ai.models.provider import BaseLLMProvider, LLMResponse, Message

logger = logging.getLogger("gaming_ai.models.ollama")


class OllamaProvider(BaseLLMProvider):
    """Async client for local Ollama instances."""

    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        host: str = "http://127.0.0.1:11434",
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(model_name=model_name, **kwargs)
        self.host = host.rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if Ollama server is running and the model exists."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.host}/api/tags")
                if res.status_code != 200:
                    return False
                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                # Check for exact or base name match (e.g. 'llama3.2:3b' vs 'llama3.2:3b-instruct')
                return any(self.model_name in m or m.startswith(self.model_name.split(":")[0]) for m in models)
        except Exception as e:
            logger.warning("Ollama availability check failed: %s", e)
            return False

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format domain Message objects into Ollama chat payload format."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate full completion from Ollama."""
        payload = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(f"{self.host}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
                content = data.get("message", {}).get("content", "")
                latency = (time.perf_counter() - start_time) * 1000.0

                return LLMResponse(
                    content=content.strip(),
                    model=self.model_name,
                    prompt_tokens=data.get("prompt_eval_count"),
                    completion_tokens=data.get("eval_count"),
                    latency_ms=latency,
                )
            except Exception as e:
                logger.error("Error communicating with Ollama: %s", e)
                raise

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream tokens asynchronously from Ollama."""
        payload = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", f"{self.host}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done", False):
                            break
            except Exception as e:
                logger.error("Streaming error with Ollama: %s", e)
                raise
