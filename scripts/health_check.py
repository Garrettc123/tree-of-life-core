#!/usr/bin/env python3
"""
HEALTH CHECK SCRIPT
Verify all Tree components are running
"""
import redis
import os
from dotenv import load_dotenv

load_dotenv()

def check_redis():
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379))
        )
        r.ping()
        print("✅ Redis: ONLINE")
        return True
    except Exception:
        print("❌ Redis: OFFLINE")
        return False

def check_context_stream():
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        info = r.xinfo_stream('context-stream')
        print(f"✅ Context Stream: {info['length']} events")
        return True
    except Exception:
        print("❌ Context Stream: NOT INITIALIZED")
        return False

if __name__ == "__main__":
    print("🌳 Tree of Life Health Check")
    print("="*40)
    
    redis_ok = check_redis()
    stream_ok = check_context_stream()
    
    print("="*40)
    
    if redis_ok and stream_ok:
        print("✅ All systems healthy")
        exit(0)
    else:
        print("⚠️ Some systems need attention")
        exit(1)
