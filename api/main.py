from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import os

from trunk.health_monitor.monitor import OrganismHealthMonitor, SUBSYSTEMS

app = FastAPI(
    title="Tree of Life Core",
    version="1.0.0",
    description="Unified NWU Protocol - 16 Systems, One Living Organism"
)

# Singleton health monitor (lazy-init, no background loop in API process)
_health_monitor = OrganismHealthMonitor()

# ---------------------------------------------------------------------------
# All 16 integrated systems
# ---------------------------------------------------------------------------
ALL_SYSTEMS = [
    {"id": "nwu_protocol",        "name": "NWU Protocol",              "value": "$98.5M",  "layer": "blockchain"},
    {"id": "ai_business",         "name": "AI Business Platform",      "value": "$946K",   "layer": "branches"},
    {"id": "ai_ops",              "name": "AI Ops Studio",             "value": "$600K",   "layer": "trunk"},
    {"id": "ai_orchestrator",     "name": "AI Orchestrator",           "value": "$490K",   "layer": "trunk"},
    {"id": "ai_wealth",           "name": "Autonomous AI Wealth",      "value": "$305K",   "layer": "branches"},
    {"id": "taproot_bridge",      "name": "Taproot Blockchain Bridge", "value": "core",    "layer": "roots"},
    {"id": "redis_memory",        "name": "Redis Context Stream",      "value": "core",    "layer": "roots"},
    {"id": "vector_memory",       "name": "Pinecone Vector Memory",    "value": "core",    "layer": "roots"},
    {"id": "master_orchestrator", "name": "Master Orchestrator",       "value": "core",    "layer": "trunk"},
    {"id": "context_stream_mgr",  "name": "Context Stream Manager",    "value": "core",    "layer": "trunk"},
    {"id": "task_planner",        "name": "Task Planner",              "value": "core",    "layer": "trunk"},
    {"id": "verification_agent",  "name": "Verification Agent",        "value": "core",    "layer": "branches"},
    {"id": "governance_agent",    "name": "Governance / DAO Agent",    "value": "core",    "layer": "branches"},
    {"id": "marketing_agent",     "name": "Marketing Content Agent",   "value": "core",    "layer": "branches"},
    {"id": "wealth_agent",        "name": "Wealth / Trading Agent",    "value": "core",    "layer": "branches"},
    {"id": "health_monitor",      "name": "Organism Health Monitor",   "value": "core",    "layer": "trunk"},
]


@app.get("/")
async def root():
    return {
        "name": "Tree of Life Core",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "dashboard": "/dashboard",
            "webhook": "/webhooks/linear",
            "staking": "/staking/status",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "systems": [s["name"] for s in ALL_SYSTEMS[:5]],
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ACTIVE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "online",
        "systems": {
            "api": "operational",
            "orchestrator": "standby",
            "blockchain_listeners": "standby",
            "database": "standby"
        },
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "deployment": "railway"
    }

@app.post("/webhooks/linear")
async def linear_webhook(request: Request):
    """
    Linear webhook handler - receives issue updates
    """
    try:
        payload = await request.json()
        action = payload.get("action")
        data = payload.get("data", {})

        identifier = data.get("identifier", "unknown")
        title = data.get("title", "N/A")
        state = data.get("state", {}).get("name", "unknown")

        print(f"[LINEAR WEBHOOK] Action: {action}")
        print(f"[LINEAR WEBHOOK] Issue: {identifier}")
        print(f"[LINEAR WEBHOOK] Title: {title}")
        print(f"[LINEAR WEBHOOK] State: {state}")

        webhook_log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "identifier": identifier,
            "title": title,
            "state": state
        }

        print(f"[LINEAR WEBHOOK] Full payload: {webhook_log}")

        return JSONResponse({
            "received": True,
            "processed": True,
            "action": action,
            "identifier": identifier,
            "message": f"Webhook processed for {identifier}"
        })

    except Exception as e:
        print(f"[LINEAR WEBHOOK ERROR] {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/status")
async def system_status():
    """
    Detailed system status endpoint
    """
    return {
        "deployment": "Railway",
        "framework": "FastAPI + Uvicorn",
        "python_version": "3.11+",
        "systems_integrated": len(ALL_SYSTEMS),
        "total_value": "$98.5M+",
        "architecture": {
            "roots": "Infrastructure & Memory (Blockchain, DBs, Vector)",
            "trunk": "Central Orchestration (Master, Context, Planner, Health, Bus)",
            "branches": "Business Logic (Verification, DAO, Marketing, Wealth)"
        }
    }

@app.get("/dashboard")
async def unified_dashboard():
    """
    Unified dashboard showing all 16 systems status, blockchain state,
    and organism health.
    """
    health = _health_monitor.snapshot()
    systems_out = []
    for sys in ALL_SYSTEMS:
        subsys_state = health["subsystems"].get(sys["id"], {})
        systems_out.append({
            **sys,
            "status": subsys_state.get("status", "unknown"),
            "layer": sys["layer"],
            "last_checked": subsys_state.get("last_checked"),
        })

    return {
        "dashboard": "Tree of Life – Unified NWU Protocol",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "organism_health": health["organism_health"],
        "healthy_systems": health["healthy_count"],
        "total_systems": health["total_systems"],
        "uptime_pct": health["uptime_pct"],
        "blockchain_state": {
            "network": os.getenv("BLOCKCHAIN_NETWORK", "sepolia"),
            "contract": os.getenv("NWU_PROTOCOL_ADDRESS", "not_configured"),
            "rpc_url_configured": bool(os.getenv("SEPOLIA_RPC_URL") or os.getenv("MAINNET_RPC_URL")),
        },
        "systems": systems_out,
    }

@app.get("/staking/status")
async def staking_status():
    """NWU token staking and reward mechanism status."""
    return {
        "staking": {
            "enabled": True,
            "contract": os.getenv("NWU_PROTOCOL_ADDRESS", "not_configured"),
            "network": os.getenv("BLOCKCHAIN_NETWORK", "sepolia"),
            "description": "Stake NWU tokens to earn rewards for contributing verified data.",
        },
        "rewards": {
            "mechanism": "proof-of-contribution",
            "distribution": "on-chain via NWU Protocol smart contract",
            "token": "NWU",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/staking/stake")
async def stake_tokens(request: Request):
    """Initiate a token staking request (delegates to on-chain contract)."""
    try:
        body = await request.json()
        amount = body.get("amount")
        wallet = body.get("wallet_address")
        if not amount or not wallet:
            raise HTTPException(status_code=422, detail="amount and wallet_address are required")
        return {
            "status": "pending",
            "action": "stake",
            "amount": amount,
            "wallet": wallet,
            "contract": os.getenv("NWU_PROTOCOL_ADDRESS", "not_configured"),
            "message": "Submit this transaction to the NWU Protocol contract to complete staking.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organism/health")
async def organism_health():
    """Living organism health snapshot across all 16 subsystems."""
    return _health_monitor.snapshot()
