"""
TAPROOT EVENT BRIDGE
Connects NWU Protocol smart contracts to the Tree's central nervous system
"""
import json
import asyncio
import os
from web3 import Web3
from redis import Redis
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class TaprootBridge:
    def __init__(self):
        # Connect to Ethereum
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('SEPOLIA_RPC_URL')))
        
        # Connect to Redis (Context Stream)
        self.redis = Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Load contract
        self.contract_address = os.getenv('NWU_PROTOCOL_ADDRESS')
        self.contract = None
        
    async def initialize(self):
        """Load contract ABI and initialize connection"""
        print(f"🌱 Taproot initializing...")
        print(f"📍 Contract: {self.contract_address}")
        print(f"🔗 Network: {self.w3.eth.chain_id}")
        
        # Load ABI from compiled contracts
        abi_path = "../smart-contracts/artifacts/NWUProtocol.json"
        with open(abi_path) as f:
            contract_json = json.load(f)
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=contract_json['abi']
            )
        
        print("✅ Taproot connected to blockchain")
        
    async def sync_event_to_tree(self, event):
        """Push blockchain event to central Context Stream"""
        event_data = {
            'source': 'blockchain',
            'contract': 'NWUProtocol',
            'event_name': event['event'],
            'block_number': event['blockNumber'],
            'tx_hash': event['transactionHash'].hex(),
            'timestamp': datetime.utcnow().isoformat(),
            'args': dict(event['args'])
        }
        
        # Write to Context Stream (Redis Stream)
        stream_id = self.redis.xadd('context-stream', event_data)
        
        print(f"⚡ Event synced: {event['event']} → Stream ID: {stream_id}")
        
        # Trigger branch-specific actions
        await self.trigger_branches(event['event'], event_data)
        
    async def trigger_branches(self, event_name, event_data):
        """Wake up specific branches based on event type"""
        
        if event_name == 'ContributionSubmitted':
            # Trigger Verification Branch
            self.redis.publish('branch:verification:wake', json.dumps(event_data))
            print("🌿 Verification Branch activated")
            
        elif event_name == 'ContributionVerified':
            # Trigger Marketing Branch (celebrate success)
            self.redis.publish('branch:marketing:wake', json.dumps(event_data))
            # Trigger Wealth Branch (new NFT minted = new asset)
            self.redis.publish('branch:wealth:wake', json.dumps(event_data))
            print("🌿 Marketing & Wealth Branches activated")
            
        elif event_name == 'RewardDistributed':
            # Trigger Governance Branch (token circulation update)
            self.redis.publish('branch:governance:wake', json.dumps(event_data))
            print("🌿 Governance Branch activated")
    
    async def listen(self):
        """Main event loop - listen to all contract events"""
        print("👂 Taproot listening for events...")
        
        # Create filter for all events
        event_filter = self.contract.events.allEvents.create_filter(fromBlock='latest')
        
        while True:
            try:
                for event in event_filter.get_new_entries():
                    await self.sync_event_to_tree(event)
                    
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)

async def main():
    bridge = TaprootBridge()
    await bridge.initialize()
    await bridge.listen()

if __name__ == "__main__":
    print("🌳 ====================================")
    print("   TAPROOT EVENT BRIDGE")
    print("   Connecting Blockchain to Tree")
    print("====================================")
    asyncio.run(main())
