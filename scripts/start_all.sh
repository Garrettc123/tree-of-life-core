#!/bin/bash
# START ALL TREE COMPONENTS

echo "🌳 Starting Tree of Life Architecture..."
echo ""

# 1. Start infrastructure
echo "1. Starting Docker infrastructure..."
docker-compose up -d
sleep 5

# 2. Start Taproot (Blockchain listener)
echo "2. Starting Taproot Bridge..."
python roots/blockchain-listeners/taproot.py &
TAPROOT_PID=$!

# 3. Start Master Orchestrator
echo "3. Starting Master Orchestrator..."
python trunk/orchestrator/main.py &
ORCHESTRATOR_PID=$!

# 4. Start Branch Agents
echo "4. Starting Branch Agents..."
python branches/verification/verify_agent.py &
python branches/governance/dao_agent.py &
python branches/marketing/content_agent.py &
python branches/wealth/trading_agent.py &

echo ""
echo "✅ All systems started!"
echo "Taproot PID: $TAPROOT_PID"
echo "Orchestrator PID: $ORCHESTRATOR_PID"
echo ""
echo "Monitor logs with: docker-compose logs -f"
echo "Health check: curl http://localhost:3000"
