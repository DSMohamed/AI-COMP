"""Tests for Sandboxed Computer Control Tools and Audit Logging."""

from pathlib import Path
import pytest
from gaming_ai.agent.agent import GamingCompanionAgent
from gaming_ai.app.config import AppConfig
from gaming_ai.models.provider import MockLLMProvider
from gaming_ai.tools.base import BaseTool, ToolResult
from gaming_ai.tools.builtin import (
    BrowserGuideTool,
    ScreenshotTool,
    TimerTool,
    VolumeControlTool,
)
from gaming_ai.tools.registry import ToolRegistry


class DummyPrivilegedTool(BaseTool):
    name = "privileged_cmd"
    description = "Dangerous test command."
    is_privileged = True

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="Executed dangerous cmd.")


@pytest.mark.asyncio
async def test_tool_registry_and_sandbox() -> None:
    """Verify registry execution, audit logging, and privilege enforcement."""
    registry = ToolRegistry(enabled=True, allow_privileged=False)
    registry.register(VolumeControlTool())
    registry.register(DummyPrivilegedTool())

    # Execute valid tool
    res = await registry.execute("set_volume", volume=50)
    assert res.success is True
    assert "50%" in res.output
    assert len(registry.audit_log) == 1
    assert registry.audit_log[0].tool_name == "set_volume"

    # Attempt to execute privileged tool when disabled
    res_priv = await registry.execute("privileged_cmd")
    assert res_priv.success is False
    assert "elevated privileges" in res_priv.error


@pytest.mark.asyncio
async def test_browser_guide_tool_safety() -> None:
    """Verify URL validation blocks dangerous schemes or loopback probes."""
    guide_tool = BrowserGuideTool()

    # Disallow file:// and local loopback
    res_bad = await guide_tool.execute(url="file:///C:/Windows/System32")
    assert res_bad.success is False

    res_loop = await guide_tool.execute(url="http://127.0.0.1:9000/attack")
    assert res_loop.success is False


@pytest.mark.asyncio
async def test_timer_tool() -> None:
    """Verify timer spawns background worker."""
    timer_tool = TimerTool()
    res = await timer_tool.execute(seconds=2, label="Boss Respawn")
    assert res.success is True
    assert res.metadata["seconds"] == 2


@pytest.mark.asyncio
async def test_agent_tool_intent_trigger() -> None:
    """Verify companion agent executes screenshot tool upon user voice intent."""
    cfg = AppConfig()
    mock_llm = MockLLMProvider(canned_response="Got it! I grabbed a screenshot for you.")
    agent = GamingCompanionAgent(
        config=cfg,
        llm_provider=mock_llm,
    )

    reply = await agent.respond_to_text("Take a screenshot please!", speak=False)
    assert "screenshot" in reply.lower()
    assert len(agent.tools.audit_log) >= 1
    assert agent.tools.audit_log[0].tool_name == "take_screenshot"
