"""FastAPI application foundation for the Linux Insight Agent API.

Creates and configures the `FastAPI` application: sets its title,
version, and description, and assembles the routers that expose the
actual endpoints — currently the health check (`api/routes/health.py`)
and agent information (`api/routes/agent.py`) routers, both mounted
under the `/api/v1` prefix. This module defines no endpoints itself
and never modifies a router's own route definitions — it only creates
the application and includes routers defined elsewhere, with a prefix
applied at inclusion time. It does not access `Monitor`, any collector,
or any other agent-internal component directly, and it implements no
authentication; those all remain the responsibility of the routers
(and their own dependencies) that get registered here.
"""

from typing import Optional, Sequence, Tuple

from fastapi import APIRouter, FastAPI

from api.routes.agent import router as agent_router
from api.routes.health import router as health_router

# Project-level API metadata, shown in the generated OpenAPI schema
# and interactive docs (/docs, /redoc).
_TITLE = "Linux Insight Agent API"
_VERSION = "1.0.0"
_DESCRIPTION = (
    "Exposes monitoring data collected by the Linux Insight Agent — "
    "host metrics gathered by its collectors and assembled into "
    "snapshots by the agent's Monitor, Scheduler, and Snapshot "
    "Manager — over HTTP."
)

# Common path prefix every router is mounted under, so every endpoint
# this API exposes is versioned from the start (e.g. `/health` becomes
# `/api/v1/health`). Applied once, here, at inclusion time — never
# baked into an individual router's own path definitions.
_API_PREFIX = "/api/v1"

# Every router registered on the application, in the order they're
# included. Each entry must be a fully-formed `APIRouter` defined
# under `api/routes/` — this module never defines endpoints itself,
# only assembles routers that do.
_ROUTERS: Tuple[APIRouter, ...] = (
    health_router,
    agent_router,
)


def create_app(routers: Optional[Sequence[APIRouter]] = None) -> FastAPI:
    """Build and return a configured `FastAPI` application.

    This is an application factory rather than a single module-level
    instance built implicitly on import: it lets a caller (e.g. a
    test suite) construct an app with a substituted or reduced set of
    routers without needing to modify this module, which is also how
    router registration is injected rather than hardcoded.

    Args:
        routers: The routers to register on the application, via
            `FastAPI.include_router`. Defaults to `_ROUTERS` — every
            router currently registered for this API — when not
            given. Every router, whether given explicitly or taken
            from `_ROUTERS`, is mounted under `_API_PREFIX`.

    Returns:
        A `FastAPI` instance with its title, version, and description
        set, and every given router included under `_API_PREFIX`
        (e.g. `/health` becomes `/api/v1/health`). No endpoints are
        defined directly on the returned application — only whatever
        each included router itself contributes.
    """
    app = FastAPI(
        title=_TITLE,
        version=_VERSION,
        description=_DESCRIPTION,
    )

    for router in routers if routers is not None else _ROUTERS:
        app.include_router(router, prefix=_API_PREFIX)

    return app


# Module-level application instance, for ASGI servers (e.g.
# `uvicorn api.app:app`) that expect to import a ready-to-serve
# `FastAPI` object rather than call a factory themselves.
app = create_app()
