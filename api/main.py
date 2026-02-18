from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import os

app = FastAPI(
    title="Tree of Life Core",
    version="1.0.0",
    description="Unified NWU Protocol - 16 Systems, One Living Organism"
)

@app.get("/")
async def root():
    return {
        "name": "Tree of Life Core",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhooks/linear",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "systems": [
            "NWU Protocol ($98.5M)",
            "AI Business Platform ($946K)",
            "AI Ops Studio ($600K)",
            "AI Orchestrator ($490K)",
            "Autonomous AI Wealth ($305K)"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ACTIVE",
        "timestamp": datetime.utcnow().isoformat(),
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
        
        # Log to Railway logs
        webhook_log = {
            "timestamp": datetime.utcnow().isoformat(),
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
        "python_version": "3.11.7",
        "systems_integrated": 16,
        "total_value": "$98.5M+",
        "architecture": {
            "roots": "Infrastructure & Memory (Blockchain, DBs, Vector)",
            "trunk": "Central Orchestration (Master, Context, Planner)",
            "branches": "Business Logic (Verification, DAO, Marketing, Wealth)"
        }
    }
