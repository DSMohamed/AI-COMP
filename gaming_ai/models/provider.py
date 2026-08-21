"""Abstract base classes and dataclasses for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any


@dataclass
class Message:
    """Chat message object."""
    role: str  # 'system', 'user', 'assistant'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Full completion response from an LLM."""
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[float] = None


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends."""

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        self.model_name = model_name
        self.kwargs = kwargs

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether the model provider and endpoint are reachable."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete text response asynchronously."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream generated response tokens asynchronously."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for unit tests and offline testing."""

    def __init__(
        self,
        model_name: str = "mock-model",
        canned_response: str = "BRO YOU'RE ACTUALLY COOKED 😭 Don't get greedy!",
        **kwargs: Any,
    ) -> None:
        super().__init__(model_name=model_name, **kwargs)
        self.canned_response = canned_response

    async def is_available(self) -> bool:
        return True

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> LLMResponse:
        return LLMResponse(
            content=self.canned_response,
            model=self.model_name,
            prompt_tokens=10,
            completion_tokens=len(self.canned_response.split()),
            latency_ms=5.0,
        )

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        words = self.canned_response.split(" ")
        for i, word in enumerate(words):
            yield word if i == 0 else " " + word

