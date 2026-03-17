"""
Tests for the Living Organism Health Monitor.
"""
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from trunk.health_monitor.monitor import OrganismHealthMonitor, SUBSYSTEMS


@pytest.fixture()
def monitor():
    return OrganismHealthMonitor(check_interval=1)


class TestSnapshot:
    def test_snapshot_structure(self, monitor):
        snap = monitor.snapshot()
        assert "organism_health" in snap
        assert "healthy_count" in snap
        assert "total_systems" in snap
        assert "uptime_pct" in snap
        assert "subsystems" in snap

    def test_total_systems_matches_registry(self, monitor):
        snap = monitor.snapshot()
        assert snap["total_systems"] == len(SUBSYSTEMS)

    def test_sixteen_subsystems(self, monitor):
        assert len(monitor.states) == 16


class TestRegisterCheck:
    def test_custom_check_registered(self, monitor):
        check_fn = MagicMock(return_value=True)
        monitor.register_check("api_gateway", check_fn)
        assert "api_gateway" in monitor._custom_checks

    @pytest.mark.asyncio
    async def test_custom_check_healthy(self, monitor):
        monitor.register_check("api_gateway", lambda: True)
        state = monitor.states["api_gateway"]
        healthy = await monitor._is_healthy("api_gateway", state)
        assert healthy is True

    @pytest.mark.asyncio
    async def test_custom_check_unhealthy(self, monitor):
        monitor.register_check("api_gateway", lambda: False)
        state = monitor.states["api_gateway"]
        healthy = await monitor._is_healthy("api_gateway", state)
        assert healthy is False

    @pytest.mark.asyncio
    async def test_custom_check_exception_is_unhealthy(self, monitor):
        def bad_check():
            raise RuntimeError("oops")
        monitor.register_check("api_gateway", bad_check)
        state = monitor.states["api_gateway"]
        healthy = await monitor._is_healthy("api_gateway", state)
        assert healthy is False
        assert state.last_error == "oops"


class TestInfraServicesHealthy:
    @pytest.mark.asyncio
    async def test_infra_service_cmd_none_is_healthy(self, monitor):
        # redis_memory has cmd=None, so it's managed externally and healthy by default
        state = monitor.states["redis_memory"]
        healthy = await monitor._is_healthy("redis_memory", state)
        assert healthy is True


class TestRestartLogic:
    @pytest.mark.asyncio
    async def test_no_restart_when_cmd_is_none(self, monitor):
        state = monitor.states["redis_memory"]
        state.status = "dead"
        await monitor._attempt_restart("redis_memory", state)
        assert state.process is None  # no restart attempted

    @pytest.mark.asyncio
    async def test_max_restarts_respected(self, monitor):
        state = monitor.states["api_gateway"]
        state.restart_count = OrganismHealthMonitor.MAX_RESTARTS
        await monitor._attempt_restart("api_gateway", state)
        assert state.status == "dead"


class TestOrganismHealthLabel:
    def test_alive_when_majority_healthy(self, monitor):
        for s in monitor.states.values():
            s.status = "healthy"
        snap = monitor.snapshot()
        assert snap["organism_health"] == "ALIVE"

    def test_degraded_when_minority_healthy(self, monitor):
        states = list(monitor.states.values())
        for s in states:
            s.status = "dead"
        # Make only one healthy (< half)
        states[0].status = "healthy"
        snap = monitor.snapshot()
        assert snap["organism_health"] == "DEGRADED"
