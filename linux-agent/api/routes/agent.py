"""Agent information route for the Linux Insight Agent API.

Defines `GET /agent`: reports the agent's configured identity and a
small amount of state about its most recent monitoring cycle. Every
value comes from either the Configuration Manager (via `ConfigDependency`)
or the `SnapshotManager` (via `SnapshotManagerDependency`) — both
supplied through FastAPI dependency injection, never constructed here.
This module never imports a collector, `Monitor`, or `Scheduler`
directly; the only collector-produced data it reads (`platform`) comes
secondhand, through whatever the `SnapshotManager` already holds.
"""

from typing import Literal, Optional

from fastapi import APIRouter, status

from api.dependencies import ConfigDependency, SnapshotManagerDependency
from api.schemas.agent import AgentResponse
from core.snapshot import Snapshot

router = APIRouter(tags=["agent"])

# Mirrors the FastAPI application's own `version` (see `api/app.py`);
# kept as a local constant, the same way `api/routes/health.py` does,
# rather than reaching into that module's private `_VERSION`.
_API_VERSION = "1.0.0"


@router.get(
    "/agent",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent information",
)
def get_agent_info(
    config: ConfigDependency,
    snapshot_manager: SnapshotManagerDependency,
) -> AgentResponse:
    """Report the agent's configured identity and latest monitoring status.

    `agent_id`, `hostname`, and `scheduler_interval` are read directly
    from the already-loaded, already-validated `Config` — no
    monitoring cycle needs to have run for these to be available.
    `platform` and `agent_status`, however, can only be known from a
    completed monitoring cycle, so they're read from the
    `SnapshotManager`'s latest snapshot instead, and degrade
    gracefully (to `null` / `"unknown"`) if none exists yet.

    Args:
        config: The application's loaded `Config`, injected by
            FastAPI via `ConfigDependency`.
        snapshot_manager: The application's shared `SnapshotManager`,
            injected by FastAPI via `SnapshotManagerDependency`.

    Returns:
        An `AgentResponse` combining configured identity with the
        latest known platform string and monitoring status.
    """
    agent_settings = config.get("agent")
    scheduler_settings = config.get("scheduler")
    snapshot = snapshot_manager.get_latest_snapshot()

    return AgentResponse(
        agent_id=agent_settings["id"],
        hostname=agent_settings["hostname"],
        platform=_extract_platform(snapshot),
        api_version=_API_VERSION,
        scheduler_interval=scheduler_settings["refresh_interval"],
        status=_derive_agent_status(snapshot),
    )


def _extract_platform(snapshot: Optional[Snapshot]) -> Optional[str]:
    """Read the platform identification string out of a snapshot, if present.

    Args:
        snapshot: The latest snapshot from `SnapshotManager`, or
            `None` if no monitoring cycle has completed yet.

    Returns:
        `snapshot["collectors"]["system_info"]["data"]["platform_string"]`,
        or `None` if `snapshot` is `None`, the `system_info` collector
        wasn't enabled for that cycle, or its output isn't shaped as
        expected.
    """
    if snapshot is None:
        return None

    collectors = snapshot.get("collectors")
    if not isinstance(collectors, dict):
        return None

    system_info = collectors.get("system_info")
    if not isinstance(system_info, dict):
        return None

    data = system_info.get("data")
    if not isinstance(data, dict):
        return None

    platform_string = data.get("platform_string")
    return platform_string if isinstance(platform_string, str) else None


def _derive_agent_status(
    snapshot: Optional[Snapshot],
) -> Literal["success", "partial_success", "unknown"]:
    """Read the overall monitoring status out of a snapshot, if present.

    Args:
        snapshot: The latest snapshot from `SnapshotManager`, or
            `None` if no monitoring cycle has completed yet.

    Returns:
        `snapshot["monitoring"]["status"]` (`Monitor`'s own vocabulary
        — `"success"` or `"partial_success"`) if present and
        recognized, otherwise `"unknown"`.
    """
    if snapshot is None:
        return "unknown"

    monitoring = snapshot.get("monitoring")
    if not isinstance(monitoring, dict):
        return "unknown"

    reported_status = monitoring.get("status")
    if reported_status in ("success", "partial_success"):
        return reported_status
    return "unknown"
