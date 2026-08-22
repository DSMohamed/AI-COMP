"""Tests for UI state management, API endpoints, and dashboard web server."""

import pytest
from httpx import ASGITransport, AsyncClient

from gaming_ai.ui.state import DashboardState
from gaming_ai.ui.web_server import create_dashboard_app


def test_dashboard_state_mutations() -> None:
    """Verify sensor toggling, transcript appending, and personality updates."""
    state = DashboardState()

    # Test sensor update
    state.set_sensors(mic="MUTED", camera="OFF")
    assert state.mic_status == "MUTED"
    assert state.camera_status == "OFF"

    # Test transcript item
    item = state.add_transcript(sender="player", text="What is this boss?", latency_ms=120.0)
    assert item.sender == "player"
    assert len(state.transcript) == 1

    # Test personality update
    state.update_personality(sarcasm=95)
    assert state.personality["sarcasm"] == 95

    # Test state dict serialization
    d = state.to_dict()
    assert d["sensors"]["mic"] == "MUTED"
    assert d["personality"]["sarcasm"] == 95
    assert len(d["transcript"]) == 1


@pytest.mark.asyncio
async def test_dashboard_api_endpoints() -> None:
    """Verify FastAPI routes for telemetry and personality control."""
    state = DashboardState()
    app = create_dashboard_app(state=state)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test index HTML
        res = await client.get("/")
        assert res.status_code == 200
        assert "Gaming Companion" in res.text

        # Test state API
        res_state = await client.get("/api/state")
        assert res_state.status_code == 200
        data = res_state.json()
        assert "sensors" in data
        assert "personality" in data

        # Test personality slider update
        res_p = await client.post("/api/personality", json={"humor": 90, "sarcasm": 85})
        assert res_p.status_code == 200
        assert state.personality["humor"] == 90

        # Test toggle camera
        res_cam = await client.post("/api/toggle/camera")
        assert res_cam.status_code == 200
        assert state.camera_status == "OFF"

        # Test clear memory
        state.add_transcript("player", "Hello")
        assert len(state.transcript) > 0
        res_clear = await client.post("/api/clear_memory")
        assert res_clear.status_code == 200
        assert len(state.transcript) == 0
