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
from datetime import datetime, timezone

load_dotenv()

# Minimal ABI covering the events the bridge listens to
MINIMAL_NWU_ABI = [
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "contributionId", "type": "uint256"},
                   {"indexed": True, "name": "contributor", "type": "address"}],
        "name": "ContributionSubmitted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "contributionId", "type": "uint256"},
                   {"indexed": False, "name": "nftTokenId", "type": "uint256"}],
        "name": "ContributionVerified",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "recipient", "type": "address"},
                   {"indexed": False, "name": "amount", "type": "uint256"}],
        "name": "RewardDistributed",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "staker", "type": "address"},
                   {"indexed": False, "name": "amount", "type": "uint256"}],
        "name": "Staked",
        "type": "event"
    },
]


class TaprootBridge:
    def __init__(self):
        # Connect to Ethereum
        rpc_url = os.getenv('SEPOLIA_RPC_URL') or os.getenv('MAINNET_RPC_URL', '')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

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
        print("🌱 Taproot initializing...")
        print(f"📍 Contract: {self.contract_address}")

        # Try to load ABI from compiled artifacts; fall back to minimal ABI
        abi = MINIMAL_NWU_ABI
        abi_paths = [
            os.path.join(os.path.dirname(__file__), "../../smart-contracts/artifacts/NWUProtocol.json"),
            "smart-contracts/artifacts/NWUProtocol.json",
        ]
        for abi_path in abi_paths:
            if os.path.exists(abi_path):
                try:
                    with open(abi_path) as f:
                        contract_json = json.load(f)
                        abi = contract_json.get('abi', MINIMAL_NWU_ABI)
                    print(f"📄 Loaded ABI from {abi_path}")
                    break
                except (json.JSONDecodeError, KeyError) as exc:
                    print(f"⚠️  Could not parse ABI from {abi_path}: {exc}")

        if self.contract_address and self.w3.is_connected():
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=abi
            )
            print(f"🔗 Network chain_id: {self.w3.eth.chain_id}")
            print("✅ Taproot connected to blockchain")
        else:
            print("⚠️  Blockchain not connected – running in offline mode")
        
    async def sync_event_to_tree(self, event_name, event_args, block_number, tx_hash):
        """Push blockchain event to central Context Stream"""
        event_data = {
            'source': 'blockchain',
            'contract': 'NWUProtocol',
            'event_name': event_name,
            'block_number': str(block_number),
            'tx_hash': tx_hash if isinstance(tx_hash, str) else tx_hash.hex(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'args': json.dumps(event_args),
        }

        # Write to Context Stream (Redis Stream)
        stream_id = self.redis.xadd('context-stream', event_data)

        print(f"⚡ Event synced: {event_name} → Stream ID: {stream_id}")

        # Trigger branch-specific actions
        await self.trigger_branches(event_name, event_data)
        
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
        """Main event loop - listen to specific contract events via polling"""
        if self.contract is None:
            print("⚠️  No contract configured – event listener inactive")
            return

        print("👂 Taproot listening for events...")

        # Known NWU Protocol event names to poll
        event_names = [
            'ContributionSubmitted',
            'ContributionVerified',
            'RewardDistributed',
            'Staked',
        ]

        # Build per-event filters for the events we care about
        filters = {}
        for name in event_names:
            try:
                event_obj = getattr(self.contract.events, name, None)
                if event_obj is not None:
                    filters[name] = event_obj.create_filter(fromBlock='latest')
            except Exception as exc:
                print(f"⚠️  Could not create filter for {name}: {exc}")

        while True:
            try:
                for event_name, event_filter in filters.items():
                    for entry in event_filter.get_new_entries():
                        await self.sync_event_to_tree(
                            event_name=event_name,
                            event_args={k: str(v) for k, v in dict(entry['args']).items()},
                            block_number=entry['blockNumber'],
                            tx_hash=entry['transactionHash'],
                        )

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
