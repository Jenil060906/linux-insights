"""Linux Agent + API startup script — TEMPORARY, for local API testing.

Unlike earlier versions of this script (which ran the agent for
exactly three monitoring cycles and then stopped automatically, purely
to test `core.engine.MonitoringEngine` in isolation), this version
runs the agent and the FastAPI API together, in the same process, for
as long as the API server is up: it loads and validates configuration,
builds a `MonitoringEngine`, attaches its `SnapshotManager` and
`Config` to the FastAPI application's state (see
`api/dependencies.py`, whose dependency providers read them from
there), starts the Scheduler running indefinitely, and then serves the
API with Uvicorn until the process is stopped (e.g. Ctrl+C).

Everything runs in one process deliberately: the Scheduler's
background thread and the API's request handlers need to share the
exact same `SnapshotManager` instance for the API to ever reflect a
real monitoring cycle, and in-memory objects can't be shared across
separate processes. This script never constructs its own FastAPI
application, adds routes, or otherwise duplicates `api/app.py`'s job
— it only imports the application `api/app.py` already builds
(title, version, routers, and all) and hands it to Uvicorn to serve.

If configuration is missing required values (e.g. a blank `agent.id`
or `agent.hostname`), loading/validation raises and this script exits
with that exception rather than proceeding with unusable
configuration — validation failures are intentionally not caught or
suppressed here.
"""

import uvicorn
from fastapi import FastAPI

from api.app import app as fastapi_app
from core.engine import MonitoringEngine

# Local-testing defaults only. Not read from configuration — config.yaml
# has no API host/port section (see docs/configuration.md) — since this
# script exists solely for manual API testing during development.
_API_HOST = "127.0.0.1"
_API_PORT = 8000


def main() -> None:
    """Start the agent and serve the API together until interrupted."""
    engine = _startup()
    _inject_dependencies(fastapi_app, engine)

    engine.start()
    print("Scheduler Started")

    try:
        _serve_api(fastapi_app)
    finally:
        engine.stop()
        print("Scheduler Stopped")


def _startup() -> MonitoringEngine:
    """Load configuration, validate it, and build a wired MonitoringEngine.

    Delegates the actual work to `MonitoringEngine.bootstrap()`, which
    performs, in order: Configuration Manager loads settings, the
    Configuration Manager validates them, then a `Monitor`, a
    `SnapshotManager`, and a `Scheduler` are created and wired
    together via dependency injection (the `Scheduler` receives the
    `Monitor`, the `SnapshotManager`, and the configured refresh
    interval — it never constructs or looks up any of them itself).

    Returns:
        A `MonitoringEngine` ready to be started.
    """
    engine = MonitoringEngine.bootstrap()
    print("Configuration Loaded")

    agent = engine.config.get("agent")
    scheduler_settings = engine.config.get("scheduler")
    print(f"{'Agent ID':<18}: {agent['id']}")
    print(f"{'Hostname':<18}: {agent['hostname']}")
    print(f"{'Refresh Interval':<18}: {scheduler_settings['refresh_interval']}")

    return engine


def _inject_dependencies(fastapi_app: FastAPI, engine: MonitoringEngine) -> None:
    """Attach the engine's SnapshotManager and Config to the FastAPI app.

    This is the one place configuration and the live `SnapshotManager`
    reach the API: `api/dependencies.py`'s `get_snapshot_manager` and
    `get_config` providers read exactly these two attributes off
    `request.app.state`. Route handlers never construct either
    themselves.

    Args:
        fastapi_app: The FastAPI application to attach state to — the
            same instance Uvicorn will go on to serve.
        engine: The `MonitoringEngine` whose `SnapshotManager` and
            `Config` should be exposed to the API.
    """
    fastapi_app.state.snapshot_manager = engine.snapshot_manager
    fastapi_app.state.config = engine.config


def _serve_api(fastapi_app: FastAPI) -> None:
    """Serve the FastAPI application with Uvicorn until interrupted.

    Blocks the calling thread for as long as the server runs. The
    Scheduler keeps running independently on its own background
    thread the entire time, continuing to update the `SnapshotManager`
    the API reads from on every request — this is what makes the API
    reflect live monitoring data rather than a single static snapshot.

    Args:
        fastapi_app: The FastAPI application to serve — built entirely
            by `api/app.py`. This function only hands it to Uvicorn;
            it never builds or modifies the application itself.
    """
    uvicorn.run(fastapi_app, host=_API_HOST, port=_API_PORT)


if __name__ == "__main__":
    main()
