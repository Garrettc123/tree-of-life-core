"""
Tests for the Inter-System Message Bus (trunk/message_bus/bus.py).
"""
import json
from unittest.mock import MagicMock, call

import pytest

from trunk.message_bus.bus import MessageBus


@pytest.fixture()
def bus(redis_mock):
    return MessageBus(redis_mock)


class TestPublish:
    def test_publish_calls_redis_publish(self, bus, redis_mock):
        bus.publish("test:channel", {"key": "value"})
        redis_mock.publish.assert_called_once()
        channel_arg = redis_mock.publish.call_args[0][0]
        assert channel_arg == "test:channel"

    def test_publish_serialises_payload(self, bus, redis_mock):
        payload = {"hello": "world"}
        bus.publish("test:channel", payload)
        raw = redis_mock.publish.call_args[0][1]
        parsed = json.loads(raw)
        assert parsed == payload


class TestBroadcast:
    def test_broadcast_uses_system_channel(self, bus, redis_mock):
        bus.broadcast({"event": "restart"})
        channel_arg = redis_mock.publish.call_args[0][0]
        assert channel_arg == "nwu:broadcast"


class TestEmit:
    def test_emit_calls_xadd(self, bus, redis_mock):
        redis_mock.xadd.return_value = b"1234567890-0"
        stream_id = bus.emit("api_gateway", "HEALTH_CHECK", {})
        redis_mock.xadd.assert_called_once()
        assert stream_id == "1234567890-0"

    def test_emit_entry_structure(self, bus, redis_mock):
        redis_mock.xadd.return_value = b"1-0"
        bus.emit("orchestrator", "TEST_EVENT", {"x": 1})
        entry = redis_mock.xadd.call_args[0][1]
        assert entry["source"] == "orchestrator"
        assert entry["event_type"] == "TEST_EVENT"
        assert "timestamp" in entry
        assert "id" in entry


class TestReadStream:
    def test_empty_stream_returns_empty_list(self, bus, redis_mock):
        redis_mock.xread.return_value = []
        results = bus.read_stream()
        assert results == []

    def test_messages_are_parsed(self, bus, redis_mock):
        redis_mock.xread.return_value = [
            (b"context-stream", [(b"1-0", {b"source": b"test"})])
        ]
        results = bus.read_stream()
        assert len(results) == 1
        assert results[0]["id"] == b"1-0"


class TestSubscribeDispatch:
    def test_subscribe_registers_handler(self, bus, redis_mock):
        handler = MagicMock()
        # Provide a minimal pubsub mock
        pubsub_mock = MagicMock()
        redis_mock.pubsub.return_value = pubsub_mock
        bus.subscribe("test:channel", handler)
        assert "test:channel" in bus._handlers

    def test_dispatch_calls_handler(self, bus, redis_mock):
        received = []
        bus._handlers["test:channel"] = [lambda d: received.append(d)]
        bus._dispatch({"channel": "test:channel", "data": json.dumps({"msg": "hi"})})
        assert received == [{"msg": "hi"}]

    def test_dispatch_bad_json_does_not_crash(self, bus):
        bus._handlers["test:channel"] = [lambda d: None]
        bus._dispatch({"channel": "test:channel", "data": "not-json"})
