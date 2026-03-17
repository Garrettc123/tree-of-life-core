"""
Tests for the FastAPI unified gateway (api/main.py).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client():
    from unittest.mock import MagicMock
    mock_monitor = MagicMock()
    mock_monitor.snapshot.return_value = {
        "organism_health": "ALIVE",
        "healthy_count": 16,
        "total_systems": 16,
        "uptime_pct": 100.0,
        "timestamp": "2024-01-01T00:00:00",
        "subsystems": {},
    }
    with patch("api.main._health_monitor", mock_monitor):
        from api.main import app
        return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    def test_returns_200(self):
        client = make_client()
        resp = client.get("/")
        assert resp.status_code == 200

    def test_contains_name(self):
        client = make_client()
        data = client.get("/").json()
        assert data["name"] == "Tree of Life Core"

    def test_contains_endpoints(self):
        client = make_client()
        data = client.get("/").json()
        assert "health" in data["endpoints"]
        assert "dashboard" in data["endpoints"]


class TestHealthEndpoint:
    def test_returns_200(self):
        client = make_client()
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_status_active(self):
        client = make_client()
        data = client.get("/health").json()
        assert data["status"] == "ACTIVE"

    def test_has_timestamp(self):
        client = make_client()
        data = client.get("/health").json()
        assert "timestamp" in data


class TestStatusEndpoint:
    def test_returns_200(self):
        client = make_client()
        resp = client.get("/status")
        assert resp.status_code == 200

    def test_systems_count(self):
        client = make_client()
        data = client.get("/status").json()
        assert data["systems_integrated"] == 16

    def test_architecture_keys(self):
        client = make_client()
        data = client.get("/status").json()
        arch = data["architecture"]
        assert "roots" in arch
        assert "trunk" in arch
        assert "branches" in arch


class TestDashboardEndpoint:
    def test_returns_200(self):
        client = make_client()
        resp = client.get("/dashboard")
        assert resp.status_code == 200

    def test_has_organism_health(self):
        client = make_client()
        data = client.get("/dashboard").json()
        assert "organism_health" in data

    def test_has_systems_list(self):
        client = make_client()
        data = client.get("/dashboard").json()
        assert isinstance(data["systems"], list)
        assert len(data["systems"]) == 16

    def test_has_blockchain_state(self):
        client = make_client()
        data = client.get("/dashboard").json()
        assert "blockchain_state" in data


class TestOrganismHealthEndpoint:
    def test_returns_200(self):
        client = make_client()
        resp = client.get("/organism/health")
        assert resp.status_code == 200

    def test_has_healthy_count(self):
        client = make_client()
        data = client.get("/organism/health").json()
        assert "healthy_count" in data
        assert "total_systems" in data


class TestStakingEndpoints:
    def test_staking_status_200(self):
        client = make_client()
        resp = client.get("/staking/status")
        assert resp.status_code == 200

    def test_staking_status_structure(self):
        client = make_client()
        data = client.get("/staking/status").json()
        assert "staking" in data
        assert "rewards" in data

    def test_stake_missing_body(self):
        client = make_client()
        resp = client.post("/staking/stake", json={})
        assert resp.status_code == 422

    def test_stake_valid_body(self):
        client = make_client()
        resp = client.post("/staking/stake", json={"amount": "100", "wallet_address": "0xABC"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        assert data["action"] == "stake"


class TestWebhookEndpoint:
    def test_webhook_valid_payload(self):
        client = make_client()
        payload = {
            "action": "update",
            "data": {
                "identifier": "NWU-1",
                "title": "Test issue",
                "state": {"name": "In Progress"}
            }
        }
        resp = client.post("/webhooks/linear", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["received"] is True
        assert data["identifier"] == "NWU-1"

    def test_webhook_empty_payload(self):
        client = make_client()
        resp = client.post("/webhooks/linear", json={})
        assert resp.status_code == 200
