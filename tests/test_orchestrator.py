"""
Tests for the Master Orchestrator (trunk/orchestrator/main.py).
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from trunk.orchestrator.main import MasterOrchestrator


@pytest.fixture()
def orchestrator(redis_mock):
    with patch("trunk.orchestrator.main.Redis", return_value=redis_mock):
        orch = MasterOrchestrator()
    return orch


class TestMasterOrchestratorInit:
    def test_branches_registered(self, orchestrator):
        assert "verification" in orchestrator.branches
        assert "marketing" in orchestrator.branches
        assert "governance" in orchestrator.branches
        assert "wealth" in orchestrator.branches

    def test_stats_initial(self, orchestrator):
        stats = orchestrator.get_stats()
        assert stats["events_processed"] == 0
        assert stats["branches_activated"] == 0


class TestProcessEvent:
    @pytest.mark.asyncio
    async def test_contribution_submitted_routes_to_verification(self, orchestrator):
        event = {"event_name": "ContributionSubmitted", "source": "blockchain", "args": "{}"}
        await orchestrator.process_event(event)
        assert orchestrator.stats["branches_activated"] == 1

    @pytest.mark.asyncio
    async def test_contribution_verified_routes_to_marketing_and_wealth(self, orchestrator):
        event = {"event_name": "ContributionVerified", "source": "blockchain", "args": "{}"}
        await orchestrator.process_event(event)
        assert orchestrator.stats["branches_activated"] == 2

    @pytest.mark.asyncio
    async def test_unknown_event_does_not_crash(self, orchestrator):
        event = {"event_name": "UnknownEvent", "source": "test", "args": "{}"}
        await orchestrator.process_event(event)  # should not raise


class TestHandlers:
    @pytest.mark.asyncio
    async def test_handle_verification_publishes(self, orchestrator, redis_mock):
        await orchestrator.handle_verification({"args": json.dumps({"contributionId": "42"})})
        redis_mock.publish.assert_called_once()
        channel = redis_mock.publish.call_args[0][0]
        assert channel == "branch:verification:task"

    @pytest.mark.asyncio
    async def test_handle_marketing_publishes(self, orchestrator, redis_mock):
        await orchestrator.handle_marketing({})
        redis_mock.publish.assert_called_once()
        channel = redis_mock.publish.call_args[0][0]
        assert channel == "branch:marketing:task"

    @pytest.mark.asyncio
    async def test_handle_governance_publishes(self, orchestrator, redis_mock):
        await orchestrator.handle_governance({})
        redis_mock.publish.assert_called_once()
        channel = redis_mock.publish.call_args[0][0]
        assert channel == "branch:governance:task"

    @pytest.mark.asyncio
    async def test_handle_wealth_publishes(self, orchestrator, redis_mock):
        await orchestrator.handle_wealth({})
        redis_mock.publish.assert_called_once()
        channel = redis_mock.publish.call_args[0][0]
        assert channel == "branch:wealth:task"
