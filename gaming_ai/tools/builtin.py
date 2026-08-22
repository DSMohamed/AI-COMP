"""Built-in safe tools for daily assistance, gaming, apps, notes, timers, and browser searches."""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Dict, Optional
import webbrowser

from gaming_ai.tools.base import BaseTool, ToolResult
from gaming_ai.vision.screen_capture import ScreenCapture

logger = logging.getLogger("gaming_ai.tools.builtin")


class ScreenshotTool(BaseTool):
    """Takes a screenshot of the active display and saves it to disk."""

    name = "take_screenshot"
    description = "Capture a high-resolution screenshot of the active display and save it locally."
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
    """Sets a non-blocking background countdown timer or reminder."""

    name = "set_timer"
    description = "Set a background timer or reminder (e.g. coffee break, focus timer, or gaming respawn)."
    requires_confirmation = False
    is_privileged = False

    def __init__(self, on_timer_expired: Optional[Callable[[str], None]] = None) -> None:
        self.on_timer_expired = on_timer_expired

    async def execute(self, seconds: int = 60, label: str = "Timer", **kwargs: Any) -> ToolResult:
        """Spawn an asynchronous countdown task."""
        seconds = max(1, min(86400, int(seconds)))

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
    """Safely opens a validated URL or web search in the default web browser."""

    name = "open_guide"
    description = "Open a URL or search query safely in the default web browser."
    requires_confirmation = False
    is_privileged = False

    async def execute(self, url: str, **kwargs: Any) -> ToolResult:
        """Validate URL scheme and open in browser."""
        if not (url.startswith("https://") or url.startswith("http://")):
            # If plain text query, search with DuckDuckGo
            url = f"https://duckduckgo.com/?q={url.replace(' ', '+')}"

        if "127.0.0.1" in url or "localhost" in url or "file://" in url:
            return ToolResult(
                success=False,
                output="",
                error="Access to local loopback addresses is restricted.",
            )

        await asyncio.to_thread(webbrowser.open, url)
        logger.info("Opened URL in browser: %s", url)
        return ToolResult(
            success=True,
            output=f"Opened in browser: {url}",
            metadata={"url": url},
        )


class AppLauncherTool(BaseTool):
    """Safely launches common desktop applications."""

    name = "launch_app"
    description = "Launch an approved desktop application (e.g. notepad, calculator, vscode, spotify, browser)."
    requires_confirmation = False
    is_privileged = False

    ALLOWED_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "code": "code",
        "vscode": "code",
        "browser": "msedge.exe",
        "edge": "msedge.exe",
        "chrome": "chrome.exe",
        "spotify": "spotify.exe",
        "terminal": "wt.exe",
        "cmd": "cmd.exe",
    }

    async def execute(self, app_name: str, **kwargs: Any) -> ToolResult:
        """Launch the specified desktop app."""
        key = app_name.lower().strip()
        cmd = self.ALLOWED_APPS.get(key)
        if not cmd:
            return ToolResult(
                success=False,
                output="",
                error=f"App '{app_name}' is not in the approved whitelist: {list(self.ALLOWED_APPS.keys())}",
            )

        try:
            subprocess.Popen(cmd, shell=True)
            return ToolResult(
                success=True,
                output=f"Launched {app_name} successfully.",
                metadata={"app": key, "cmd": cmd},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to launch {app_name}: {e}",
            )


class NoteTakingTool(BaseTool):
    """Takes quick notes and adds items to the daily todo/notes file."""

    name = "take_note"
    description = "Save a quick personal note or todo item to the daily notes file."
    requires_confirmation = False
    is_privileged = False

    def __init__(self, notes_file: str | Path = "data/daily_notes.txt") -> None:
        self.notes_file = Path(notes_file)

    async def execute(self, note: str, **kwargs: Any) -> ToolResult:
        """Append note with timestamp."""
        self.notes_file.parent.mkdir(parents=True, exist_ok=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        line = f"[{now_str}] {note.strip()}\n"

        def _append():
            with open(self.notes_file, "a", encoding="utf-8") as f:
                f.write(line)

        await asyncio.to_thread(_append)
        return ToolResult(
            success=True,
            output=f"Note saved: '{note.strip()}'",
            metadata={"note": note},
        )


class TimeDateTool(BaseTool):
    """Reports the current local time, date, and day of the week."""

    name = "get_time"
    description = "Get the current local time and date."
    requires_confirmation = False
    is_privileged = False

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Return formatted time string."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p on %A, %B %d, %Y")
        return ToolResult(
            success=True,
            output=f"The current time is {time_str}.",
            metadata={"iso": now.isoformat()},
        )


class VolumeControlTool(BaseTool):
    """Adjusts companion audio volume level."""

    name = "set_volume"
    description = "Adjust audio volume level (0 to 100)."
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
    description = "Read plain text currently copied to the system clipboard."
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
