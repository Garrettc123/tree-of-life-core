"""
Tests for the Context Stream Manager (trunk/context-stream/stream_manager.py).
"""
import json
from unittest.mock import MagicMock

import pytest

from trunk.context_stream.stream_manager import ContextStreamManager


@pytest.fixture()
def manager(redis_mock):
    return ContextStreamManager(redis_mock)


class TestPublishEvent:
    def test_calls_xadd(self, manager, redis_mock):
        stream_id = manager.publish_event("test_source", "TEST_EVENT", {"key": "value"})
        redis_mock.xadd.assert_called_once()
        assert stream_id == "1234567890-0"

    def test_event_structure(self, manager, redis_mock):
        manager.publish_event("orchestrator", "CONTRIBUTION", {"id": 1})
        call_args = redis_mock.xadd.call_args
        event_data = call_args[0][1]
        assert event_data["source"] == "orchestrator"
        assert event_data["event_type"] == "CONTRIBUTION"
        assert "timestamp" in event_data
        assert "payload" in event_data


class TestReadStream:
    def test_returns_empty_when_no_messages(self, manager, redis_mock):
        redis_mock.xreadgroup.return_value = []
        messages = manager.read_stream("orchestrator", "consumer-1")
        assert messages == []

    def test_calls_xreadgroup(self, manager, redis_mock):
        manager.read_stream("orchestrator", "consumer-1", count=5)
        redis_mock.xreadgroup.assert_called_once()


class TestGetStreamInfo:
    def test_returns_dict(self, manager, redis_mock):
        redis_mock.xinfo_stream.return_value = {
            "length": 3,
            "first-entry": "1-0",
            "last-entry": "3-0",
        }
        info = manager.get_stream_info()
        assert info["length"] == 3
