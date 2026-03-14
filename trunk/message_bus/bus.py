"""
INTER-SYSTEM MESSAGE PASSING BUS
Unified pub/sub + request-reply bus built on Redis streams and channels.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import redis as redis_lib


STREAM_NAME = "context-stream"
SYSTEM_BROADCAST_CHANNEL = "nwu:broadcast"


class MessageBus:
    """
    Lightweight message bus that wraps Redis pub/sub and streams.

    Publish-subscribe::

        bus = MessageBus(redis_client)
        bus.subscribe("topic:example", handler_fn)
        bus.publish("topic:example", {"key": "value"})

    Broadcast to all systems::

        bus.broadcast({"event": "system_ready", "system": "api_gateway"})

    Append to shared event stream::

        bus.emit(source="api_gateway", event_type="health_check", payload={...})
    """

    def __init__(self, redis_client: redis_lib.Redis):
        self.redis = redis_client
        self._pubsub: Optional[redis_lib.client.PubSub] = None
        self._handlers: Dict[str, List[Callable]] = {}

    # ------------------------------------------------------------------
    # Pub / Sub
    # ------------------------------------------------------------------

    def subscribe(self, channel: str, handler: Callable) -> None:
        """Register a handler for a Redis pub/sub channel."""
        self._handlers.setdefault(channel, []).append(handler)
        if self._pubsub is None:
            self._pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self._pubsub.subscribe(**{channel: self._dispatch})

    def publish(self, channel: str, payload: Dict[str, Any]) -> int:
        """Publish a message to a pub/sub channel."""
        return self.redis.publish(channel, json.dumps(payload))

    def broadcast(self, payload: Dict[str, Any]) -> int:
        """Broadcast a message to all systems."""
        return self.publish(SYSTEM_BROADCAST_CHANNEL, payload)

    def listen(self) -> None:
        """Blocking listen loop – call in a dedicated thread/process."""
        if self._pubsub is None:
            return
        for _msg in self._pubsub.listen():
            pass  # dispatch happens via registered callbacks

    # ------------------------------------------------------------------
    # Event stream (append-only log)
    # ------------------------------------------------------------------

    def emit(self, source: str, event_type: str, payload: Dict[str, Any]) -> str:
        """Append an event to the shared context stream."""
        entry = {
            "id": str(uuid.uuid4()),
            "source": source,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": json.dumps(payload),
        }
        stream_id: bytes = self.redis.xadd(STREAM_NAME, entry)
        return stream_id.decode() if isinstance(stream_id, bytes) else stream_id

    def read_stream(self, last_id: str = "0-0", count: int = 10) -> List[Dict]:
        """Read messages from the event stream since ``last_id``."""
        raw = self.redis.xread({STREAM_NAME: last_id}, count=count, block=100)
        results = []
        if raw:
            for _stream, messages in raw:
                for msg_id, data in messages:
                    results.append({"id": msg_id, "data": data})
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dispatch(self, message: Dict) -> None:
        channel = message.get("channel", "")
        data_raw = message.get("data", "{}")
        try:
            data = json.loads(data_raw)
        except (json.JSONDecodeError, TypeError):
            data = {}
        for handler in self._handlers.get(channel, []):
            try:
                handler(data)
            except Exception as exc:
                print(f"[MessageBus] Handler error on {channel}: {exc}")


def create_bus(host: str = "localhost", port: int = 6379) -> MessageBus:
    """Convenience factory."""
    client = redis_lib.Redis(host=host, port=port, decode_responses=True)
    return MessageBus(client)
