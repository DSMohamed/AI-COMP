"""FastAPI web server with WebSocket broadcasting for the companion dashboard."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from gaming_ai.ui.state import DashboardState

logger = logging.getLogger("gaming_ai.ui.web_server")


class PersonalityUpdateRequest(BaseModel):
    persona: Optional[str] = None
    sarcasm: Optional[int] = None
    humor: Optional[int] = None
    energy: Optional[int] = None
    talkativeness: Optional[int] = None
    gaming_slang: Optional[bool] = None


def create_dashboard_app(
    state: Optional[DashboardState] = None,
    agent: Optional[Any] = None,
) -> FastAPI:
    """Create and configure the FastAPI web application."""
    app = FastAPI(title="Local AI Gaming Companion Dashboard", version="1.0.0")
    dashboard_state = state or DashboardState()

    active_websockets: list[WebSocket] = []

    def broadcast_state(data: Dict[str, Any]) -> None:
        """Send state JSON to all connected clients."""
        payload = json.dumps(data)
        for ws in list(active_websockets):
            try:
                asyncio.create_task(ws.send_text(payload))
            except Exception:
                if ws in active_websockets:
                    active_websockets.remove(ws)

    dashboard_state.add_listener(broadcast_state)

    template_path = Path(__file__).parent / "templates" / "index.html"

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        """Render the desktop dashboard interface."""
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        return "<h1>Dashboard template not found</h1>"

    @app.get("/api/state")
    async def get_state() -> Dict[str, Any]:
        """Fetch current telemetry, sensors, and personality state."""
        return dashboard_state.to_dict()

    @app.post("/api/personality")
    async def update_personality(req: PersonalityUpdateRequest) -> Dict[str, Any]:
        """Update companion personality sliders in real time."""
        updates = {k: v for k, v in req.model_dump().items() if v is not None}
        dashboard_state.update_personality(**updates)
        if agent and hasattr(agent, "personality"):
            for k, v in updates.items():
                if hasattr(agent.personality.config, k):
                    setattr(agent.personality.config, k, v)
        return {"status": "ok", "personality": dashboard_state.personality}

    @app.post("/api/toggle/{sensor}")
    async def toggle_sensor(sensor: str) -> Dict[str, Any]:
        """Toggle hardware sensors (camera, mic)."""
        if sensor == "camera":
            new_val = "OFF" if dashboard_state.camera_status == "ON" else "ON"
            dashboard_state.set_sensors(camera=new_val)
        elif sensor == "mic":
            new_val = "MUTED" if dashboard_state.mic_status == "LISTENING" else "LISTENING"
            dashboard_state.set_sensors(mic=new_val)
        return {"status": "ok", "sensor": sensor, "state": dashboard_state.to_dict()["sensors"]}

    @app.post("/api/clear_memory")
    async def clear_memory() -> Dict[str, Any]:
        """Clear current session transcript and working context."""
        dashboard_state.transcript.clear()
        if agent and hasattr(agent, "context"):
            agent.context.clear_history()
        dashboard_state._notify()
        return {"status": "ok", "message": "Session memory cleared."}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Real-time bidirectional telemetry socket."""
        await websocket.accept()
        active_websockets.append(websocket)
        # Send initial state snapshot
        await websocket.send_text(json.dumps(dashboard_state.to_dict()))
        try:
            while True:
                data = await websocket.receive_text()
                # Handle client messages if any
        except WebSocketDisconnect:
            if websocket in active_websockets:
                active_websockets.remove(websocket)
        except Exception:
            if websocket in active_websockets:
                active_websockets.remove(websocket)

    return app
