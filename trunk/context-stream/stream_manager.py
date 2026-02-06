"""
CONTEXT STREAM MANAGER
Manages the central event stream flowing through the tree
"""
import redis
import json
from datetime import datetime

class ContextStreamManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.stream_name = 'context-stream'
        
    def publish_event(self, source, event_type, payload):
        """Publish event to context stream"""
        event_data = {
            'source': source,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'payload': json.dumps(payload)
        }
        
        stream_id = self.redis.xadd(self.stream_name, event_data)
        return stream_id
    
    def read_stream(self, consumer_group, consumer_name, count=10):
        """Read from stream as part of a consumer group"""
        messages = self.redis.xreadgroup(
            groupname=consumer_group,
            consumername=consumer_name,
            streams={self.stream_name: '>'},
            count=count,
            block=1000
        )
        return messages
    
    def get_stream_info(self):
        """Get information about the context stream"""
        info = self.redis.xinfo_stream(self.stream_name)
        return {
            'length': info['length'],
            'first_entry': info['first-entry'],
            'last_entry': info['last-entry']
        }
