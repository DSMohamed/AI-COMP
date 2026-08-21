"""Tests for Ollama and Mock LLM providers."""

import pytest
from gaming_ai.models.ollama import OllamaProvider
from gaming_ai.models.provider import Message, MockLLMProvider


def test_ollama_format_messages() -> None:
    """Verify message conversion to Ollama JSON payload."""
    provider = OllamaProvider(model_name="llama3.2:3b")
    messages = [
        Message(role="system", content="You are Glitch"),
        Message(role="user", content="Am I cooked?"),
    ]
    formatted = provider._format_messages(messages)
    assert len(formatted) == 2
    assert formatted[0] == {"role": "system", "content": "You are Glitch"}
    assert formatted[1] == {"role": "user", "content": "Am I cooked?"}


@pytest.mark.asyncio
async def test_mock_llm_provider_generation() -> None:
    """Verify deterministic generation from MockLLMProvider."""
    provider = MockLLMProvider(canned_response="BRO YOU'RE COOKED 😭")
    messages = [Message(role="user", content="help me")]

    response = await provider.generate(messages=messages)
    assert response.content == "BRO YOU'RE COOKED 😭"
    assert response.latency_ms is not None


@pytest.mark.asyncio
async def test_mock_llm_provider_streaming() -> None:
    """Verify token streaming from MockLLMProvider."""
    provider = MockLLMProvider(canned_response="BRO YOU'RE COOKED 😭")
    messages = [Message(role="user", content="help me")]

    tokens = []
    async for token in provider.generate_stream(messages=messages):
        tokens.append(token)

    assert "".join(tokens) == "BRO YOU'RE COOKED 😭"
