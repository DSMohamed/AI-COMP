"""Built-in safe tools for gaming assistance, screenshots, timers, and browser guides."""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Callable, Dict, Optional
import webbrowser

from gaming_ai.tools.base import BaseTool, ToolResult
from gaming_ai.vision.screen_capture import ScreenCapture

logger = logging.getLogger("gaming_ai.tools.builtin")


class ScreenshotTool(BaseTool):
    """Takes a game screenshot and saves it to the local output directory."""

    name = "take_screenshot"
    description = "Capture a high-resolution screenshot of the active gaming display and save it locally."
    requires_confirmation = False
    is_privileged = False

    def __init__(self, output_dir: str | Path = "data/screenshots") -> None:
        self.output_dir = Path(output_dir)
        self.screen_capture = ScreenCapture()

    async def execute(self, filename: Optional[str] = None, **kwargs: Any) -> ToolResult:
        """Capture screen and save to disk."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        img = await asyncio.to_thread(self.screen_capture.capture_frame)
        if img is None:
            return ToolResult(success=False, output="", error="Failed to capture screen.")

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = filename or f"screenshot_{timestamp_str}.png"
        out_path = self.output_dir / out_name

        await asyncio.to_thread(img.save, str(out_path), "PNG")
        logger.info("Screenshot saved: %s", out_path)
        return ToolResult(
            success=True,
            output=f"Screenshot saved successfully to {out_path.name}",
            metadata={"path": str(out_path)},
        )


class TimerTool(BaseTool):
    """Sets a non-blocking background countdown timer with an alert."""

    name = "set_timer"
    description = "Set a background gameplay countdown timer (e.g. boss respawn, item buff expiry, or cooldown)."
    requires_confirmation = False
    is_privileged = False

    def __init__(self, on_timer_expired: Optional[Callable[[str], None]] = None) -> None:
        self.on_timer_expired = on_timer_expired

    async def execute(self, seconds: int = 60, label: str = "Timer", **kwargs: Any) -> ToolResult:
        """Spawn an asynchronous countdown task."""
        seconds = max(1, min(3600, int(seconds)))  # Clamp between 1s and 1 hour

        async def _timer_worker(dur: int, lbl: str) -> None:
            await asyncio.sleep(dur)
            logger.info("⏰ Timer Alert: '%s' has expired after %ds!", lbl, dur)
            if self.on_timer_expired:
                self.on_timer_expired(lbl)

        asyncio.create_task(_timer_worker(seconds, label))
        return ToolResult(
            success=True,
            output=f"Timer set for {seconds} seconds ({label}).",
            metadata={"seconds": seconds, "label": label},
        )


class BrowserGuideTool(BaseTool):
    """Safely opens a validated guide or wiki page in the default web browser."""

    name = "open_guide"
    description = "Open a game wiki or strategy guide URL safely in the default web browser."
    requires_confirmation = False
    is_privileged = False

    async def execute(self, url: str, **kwargs: Any) -> ToolResult:
        """Validate URL scheme and open in browser."""
        if not (url.startswith("https://") or url.startswith("http://")):
            return ToolResult(
                success=False,
                output="",
                error="Invalid URL scheme. Only HTTP and HTTPS URLs are permitted.",
            )

        # Disallow malicious schemes or localhost probes
        if "127.0.0.1" in url or "localhost" in url or "file://" in url:
            return ToolResult(
                success=False,
                output="",
                error="Access to local loopback addresses is restricted.",
            )

        await asyncio.to_thread(webbrowser.open, url)
        logger.info("Opened browser guide: %s", url)
        return ToolResult(
            success=True,
            output=f"Opened guide in browser: {url}",
            metadata={"url": url},
        )


class VolumeControlTool(BaseTool):
    """Adjusts companion / system volume level."""

    name = "set_volume"
    description = "Adjust or mute audio playback volume (0 to 100)."
    requires_confirmation = False
    is_privileged = False

    def __init__(self) -> None:
        self.current_volume: int = 80

    async def execute(self, volume: int = 80, **kwargs: Any) -> ToolResult:
        """Set volume level."""
        vol = max(0, min(100, int(volume)))
        self.current_volume = vol
        logger.info("Companion volume adjusted to %d%%", vol)
        return ToolResult(
            success=True,
            output=f"Volume set to {vol}%.",
            metadata={"volume": vol},
        )


class ClipboardTool(BaseTool):
    """Safely reads text content from the system clipboard."""

    name = "read_clipboard"
    description = "Read plain text currently copied to the system clipboard (e.g. game invite code or coordinate string)."
    requires_confirmation = False
    is_privileged = False

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Read clipboard content."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            content = root.clipboard_get()
            root.destroy()
            return ToolResult(
                success=True,
                output=f"Clipboard content: '{content[:200]}'",
                metadata={"length": len(content)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Could not access clipboard: {e}",
            )
