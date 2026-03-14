"""
LIVING ORGANISM HEALTH MONITOR
Monitors all 16 subsystems and auto-restarts any that die.
"""
import asyncio
import subprocess
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Subsystem registry
# Each entry describes one of the 16 logical subsystems.
# ---------------------------------------------------------------------------

SUBSYSTEMS: Dict[str, Dict] = {
    # Roots
    "taproot_bridge": {
        "display_name": "Taproot Blockchain Bridge",
        "layer": "roots",
        "cmd": ["python3", "roots/blockchain-listeners/taproot.py"],
    },
    "redis_memory": {
        "display_name": "Redis Context Stream",
        "layer": "roots",
        "cmd": None,  # Infrastructure service (Docker), not a Python process
    },
    "vector_memory": {
        "display_name": "Pinecone Vector Memory",
        "layer": "roots",
        "cmd": None,
    },
    # Trunk
    "master_orchestrator": {
        "display_name": "Master Orchestrator",
        "layer": "trunk",
        "cmd": ["python3", "trunk/orchestrator/main.py"],
    },
    "context_stream_mgr": {
        "display_name": "Context Stream Manager",
        "layer": "trunk",
        "cmd": None,
    },
    "task_planner": {
        "display_name": "Task Planner",
        "layer": "trunk",
        "cmd": None,
    },
    # Branches
    "verification_agent": {
        "display_name": "Verification Agent",
        "layer": "branches",
        "cmd": ["python3", "branches/verification/verify_agent.py"],
    },
    "governance_agent": {
        "display_name": "Governance / DAO Agent",
        "layer": "branches",
        "cmd": ["python3", "branches/governance/dao_agent.py"],
    },
    "marketing_agent": {
        "display_name": "Marketing Content Agent",
        "layer": "branches",
        "cmd": ["python3", "branches/marketing/content_agent.py"],
    },
    "wealth_agent": {
        "display_name": "Wealth / Trading Agent",
        "layer": "branches",
        "cmd": ["python3", "branches/wealth/trading_agent.py"],
    },
    # API / Platform
    "api_gateway": {
        "display_name": "Unified API Gateway",
        "layer": "api",
        "cmd": ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
    },
    "nwu_staking": {
        "display_name": "NWU Token Staking & Rewards",
        "layer": "api",
        "cmd": None,
    },
    # Monitoring / Infra
    "prometheus": {
        "display_name": "Prometheus Metrics",
        "layer": "infra",
        "cmd": None,
    },
    "grafana_dashboard": {
        "display_name": "Grafana Dashboard",
        "layer": "infra",
        "cmd": None,
    },
    "message_bus": {
        "display_name": "Inter-System Message Bus",
        "layer": "trunk",
        "cmd": None,
    },
    "health_monitor": {
        "display_name": "Living Organism Health Monitor",
        "layer": "trunk",
        "cmd": None,  # Self-referential – managed externally
    },
}


class SubsystemState:
    def __init__(self, name: str, meta: Dict):
        self.name = name
        self.meta = meta
        self.status: str = "unknown"       # unknown / healthy / degraded / dead
        self.process: Optional[subprocess.Popen] = None
        self.last_checked: Optional[str] = None
        self.restart_count: int = 0
        self.last_error: Optional[str] = None


class OrganismHealthMonitor:
    """
    Monitors subsystem health and automatically restarts failed processes.

    Usage::

        monitor = OrganismHealthMonitor()
        await monitor.run()          # blocking loop
        snapshot = monitor.snapshot()  # instant status dict
    """

    MAX_RESTARTS = 5
    CHECK_INTERVAL = 30  # seconds between health sweeps

    def __init__(self, check_interval: int = CHECK_INTERVAL):
        self.check_interval = check_interval
        self.states: Dict[str, SubsystemState] = {
            k: SubsystemState(k, v) for k, v in SUBSYSTEMS.items()
        }
        self._custom_checks: Dict[str, Callable] = {}
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_check(self, subsystem_name: str, check_fn: Callable) -> None:
        """Register a custom health-check callable for a subsystem.

        ``check_fn`` must return a bool (True = healthy).
        """
        self._custom_checks[subsystem_name] = check_fn

    def snapshot(self) -> Dict:
        """Return a JSON-serialisable health snapshot."""
        healthy = sum(1 for s in self.states.values() if s.status == "healthy")
        total = len(self.states)
        return {
            "organism_health": "ALIVE" if healthy > total // 2 else "DEGRADED",
            "healthy_count": healthy,
            "total_systems": total,
            "uptime_pct": round(healthy / total * 100, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subsystems": {
                name: {
                    "display_name": s.meta["display_name"],
                    "layer": s.meta["layer"],
                    "status": s.status,
                    "restart_count": s.restart_count,
                    "last_checked": s.last_checked,
                    "last_error": s.last_error,
                }
                for name, s in self.states.items()
            },
        }

    async def run(self) -> None:
        """Blocking health-monitor loop."""
        self._running = True
        print("🫀 Living Organism Health Monitor started")
        while self._running:
            await self._sweep()
            await asyncio.sleep(self.check_interval)

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _sweep(self) -> None:
        """One pass over all subsystems."""
        for name, state in self.states.items():
            await self._check_and_heal(name, state)

    async def _check_and_heal(self, name: str, state: SubsystemState) -> None:
        state.last_checked = datetime.now(timezone.utc).isoformat()

        healthy = await self._is_healthy(name, state)

        if healthy:
            state.status = "healthy"
            state.last_error = None
        else:
            if state.status == "healthy":
                print(f"💔 Subsystem degraded: {name}")
            state.status = "dead"
            await self._attempt_restart(name, state)

    async def _is_healthy(self, name: str, state: SubsystemState) -> bool:
        # Run a registered custom check first
        if name in self._custom_checks:
            try:
                result = self._custom_checks[name]()
                return bool(result)
            except Exception as exc:
                state.last_error = str(exc)
                return False

        # For managed processes: check if the subprocess is still running
        if state.process is not None:
            if state.process.poll() is None:
                return True
            state.last_error = f"Process exited with code {state.process.returncode}"
            return False

        # Infrastructure services (cmd=None) are assumed healthy by default
        # (they're managed by Docker / external systems)
        if state.meta["cmd"] is None:
            state.status = "healthy"
            return True

        # Process hasn't been started yet – not healthy
        return False

    async def _attempt_restart(self, name: str, state: SubsystemState) -> None:
        cmd = state.meta.get("cmd")
        if cmd is None:
            return  # Can't restart infra services
        if state.restart_count >= self.MAX_RESTARTS:
            print(f"🚨 {name} has exceeded max restarts ({self.MAX_RESTARTS})")
            state.status = "dead"
            return

        state.restart_count += 1
        print(f"♻️  Restarting {name} (attempt {state.restart_count}/{self.MAX_RESTARTS})")
        try:
            state.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            # Give the process a moment to fail fast
            await asyncio.sleep(2)
            if state.process.poll() is None:
                state.status = "healthy"
                state.last_error = None
                print(f"✅ {name} restarted successfully (PID {state.process.pid})")
            else:
                state.last_error = f"Process died immediately (rc={state.process.returncode})"
                state.status = "dead"
                print(f"❌ {name} failed to restart")
        except Exception as exc:
            state.last_error = str(exc)
            state.status = "dead"
            print(f"❌ Could not restart {name}: {exc}")


async def main():
    monitor = OrganismHealthMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
