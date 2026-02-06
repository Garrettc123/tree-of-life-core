"""
MASTER ORCHESTRATOR - The Tree's Central Nervous System
Receives events from Context Stream and delegates to branches
"""
import asyncio
import json
from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()

class MasterOrchestrator:
    def __init__(self):
        self.redis = Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.branches = {
            'verification': self.handle_verification,
            'marketing': self.handle_marketing,
            'governance': self.handle_governance,
            'wealth': self.handle_wealth
        }
        
        self.stats = {
            'events_processed': 0,
            'branches_activated': 0,
            'uptime_start': None
        }
        
    async def read_context_stream(self):
        """Read from the central Context Stream"""
        print("📡 Listening to Context Stream...")
        
        # Read from Redis Stream
        last_id = '0-0'
        
        while True:
            try:
                # Read new messages from stream
                messages = self.redis.xread(
                    {'context-stream': last_id},
                    count=10,
                    block=1000
                )
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        await self.process_event(data)
                        last_id = message_id
                        self.stats['events_processed'] += 1
                        
            except Exception as e:
                print(f"❌ Stream error: {e}")
                await asyncio.sleep(1)
    
    async def process_event(self, event_data):
        """Process event and delegate to appropriate branch"""
        event_name = event_data.get('event_name')
        source = event_data.get('source')
        
        print(f"🔄 Processing: {event_name} from {source}")
        
        # Delegate to branches based on event type
        if event_name == 'ContributionSubmitted':
            await self.branches['verification'](event_data)
            self.stats['branches_activated'] += 1
        elif event_name == 'ContributionVerified':
            await self.branches['marketing'](event_data)
            await self.branches['wealth'](event_data)
            self.stats['branches_activated'] += 2
    
    async def handle_verification(self, data):
        """Verification Branch Handler"""
        print("✓ Verification Branch: Analyzing contribution...")
        contribution_id = data.get('args', {}).get('contributionId')
        # TODO: Trigger verification agents
        # For now, publish to verification branch's listener
        self.redis.publish('branch:verification:task', json.dumps({
            'task': 'verify_contribution',
            'contribution_id': contribution_id,
            'data': data
        }))
        
    async def handle_marketing(self, data):
        """Marketing Branch Handler"""
        print("📢 Marketing Branch: Creating success story...")
        # TODO: Trigger content generation agents
        self.redis.publish('branch:marketing:task', json.dumps({
            'task': 'create_success_story',
            'data': data
        }))
        
    async def handle_governance(self, data):
        """Governance Branch Handler"""
        print("🏛️ Governance Branch: Updating DAO state...")
        self.redis.publish('branch:governance:task', json.dumps({
            'task': 'update_dao_state',
            'data': data
        }))
        
    async def handle_wealth(self, data):
        """Wealth Management Branch Handler"""
        print("💰 Wealth Branch: Updating portfolio...")
        self.redis.publish('branch:wealth:task', json.dumps({
            'task': 'portfolio_update',
            'data': data
        }))
    
    def get_stats(self):
        """Return orchestrator statistics"""
        return self.stats

async def main():
    print("🌳 ====================================")
    print("   MASTER ORCHESTRATOR")
    print("   Central Nervous System Active")
    print("====================================")
    
    orchestrator = MasterOrchestrator()
    await orchestrator.read_context_stream()

if __name__ == "__main__":
    asyncio.run(main())
