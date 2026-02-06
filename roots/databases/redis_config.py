"""
REDIS MEMORY CONFIGURATION
Central memory hub for the Tree's Context Stream
"""
import redis
import os
from dotenv import load_dotenv

load_dotenv()

class RedisMemory:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
    def create_context_stream(self):
        """Initialize the central context stream"""
        # Context Stream stores all events flowing through the tree
        self.client.xgroup_create('context-stream', 'orchestrator', id='0', mkstream=True)
        print("✅ Context Stream initialized")
        
    def health_check(self):
        """Check Redis connection"""
        try:
            self.client.ping()
            return True
        except:
            return False
