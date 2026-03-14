"""
Shared pytest fixtures for the Tree of Life test suite.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def redis_mock():
    """Return a MagicMock that mimics the redis.Redis interface."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.xadd.return_value = "1234567890-0"
    mock.xread.return_value = []
    mock.xreadgroup.return_value = []
    mock.xinfo_stream.return_value = {"length": 0, "first-entry": None, "last-entry": None}
    mock.publish.return_value = 1
    mock.set.return_value = True
    return mock


@pytest.fixture()
def api_client():
    """Return a FastAPI TestClient with a patched health monitor."""
    with patch("api.main._health_monitor") as mock_monitor:
        mock_monitor.snapshot.return_value = {
            "organism_health": "ALIVE",
            "healthy_count": 16,
            "total_systems": 16,
            "uptime_pct": 100.0,
            "timestamp": "2024-01-01T00:00:00",
            "subsystems": {},
        }
        from api.main import app
        yield TestClient(app)
