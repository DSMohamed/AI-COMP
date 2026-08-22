"""Base class and result definitions for sandboxed tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Standardized output of a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all sandboxed companion tools."""

    name: str
    description: str
    requires_confirmation: bool = False
    is_privileged: bool = False

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool logic within safety bounds."""
        pass
