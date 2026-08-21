"""Tests for end-to-end GamingCompanionAgent pipeline."""

import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig
from gaming_ai.models.provider import MockLLMProvider


@pytest.mark.asyncio
async def test_agent_text_response_loop() -> None:
    """Verify companion processes text and responds using LLM without audio output."""
    cfg = AppConfig()
    mock_llm = MockLLMProvider(canned_response="Nice dodge! Now punish that boss.")
    agent = GamingCompanionAgent(config=cfg, llm_provider=mock_llm)

    response = await agent.respond_to_text("Did you see that dodge?", speak=False)
    assert response == "Nice dodge! Now punish that boss."
    assert len(agent.context._history) == 2
    assert agent.context._history[0].content == "Did you see that dodge?"
    assert agent.context._history[1].content == "Nice dodge! Now punish that boss."
