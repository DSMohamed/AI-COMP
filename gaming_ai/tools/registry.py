"""Tool registry, sandbox safety verification, and audit logging engine."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional

from gaming_ai.tools.base import BaseTool, ToolResult

logger = logging.getLogger("gaming_ai.tools.registry")


@dataclass
class ToolAuditLog:
    """Immutable audit record of a tool invocation."""
    timestamp: float = field(default_factory=time.time)
    tool_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    output: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class ToolRegistry:
    """Manages available tools, enforces permission constraints, and logs actions."""

    def __init__(self, enabled: bool = True, allow_privileged: bool = False) -> None:
        self.enabled = enabled
        self.allow_privileged = allow_privileged
        self._tools: Dict[str, BaseTool] = {}
        self.audit_log: List[ToolAuditLog] = []

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        self._tools[tool.name.lower()] = tool
        logger.debug("Registered tool: '%s'", tool.name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by name."""
        return self._tools.get(name.lower())

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools and their schemas."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "requires_confirmation": t.requires_confirmation,
                "is_privileged": t.is_privileged,
            }
            for t in self._tools.values()
        ]

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """
        Execute a registered tool safely within sandbox boundaries and log the outcome.
        """
        start_time = time.perf_counter()
        name = tool_name.lower()

        if not self.enabled:
            err = "Computer control tools are disabled in configuration."
            logger.warning(err)
            return ToolResult(success=False, output="", error=err)

        tool = self._tools.get(name)
        if not tool:
            err = f"Tool '{tool_name}' not found."
            logger.error(err)
            return ToolResult(success=False, output="", error=err)

        if tool.is_privileged and not self.allow_privileged:
            err = f"Tool '{tool_name}' requires elevated privileges which are currently disabled."
            logger.warning(err)
            return ToolResult(success=False, output="", error=err)

        try:
            result = await tool.execute(**kwargs)
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"Tool execution error: {e}"
            logger.error("Error executing '%s': %s", tool_name, e)
            result = ToolResult(success=False, output="", error=err_msg, execution_time_ms=elapsed)

        elapsed = (time.perf_counter() - start_time) * 1000.0
        result.execution_time_ms = round(elapsed, 2)

        # Record audit log
        log_entry = ToolAuditLog(
            timestamp=time.time(),
            tool_name=tool.name,
            parameters=kwargs,
            success=result.success,
            output=result.output,
            error=result.error,
            execution_time_ms=result.execution_time_ms,
        )
        self.audit_log.append(log_entry)
        logger.info(
            "🛠️ Tool Invoked: [%s] (Success: %s, Latency: %.1fms) -> %s",
            tool.name,
            result.success,
            result.execution_time_ms,
            result.output if result.success else result.error,
        )

        return result
