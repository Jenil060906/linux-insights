"""Response schema for the agent information endpoint.

Defines `AgentResponse`, the response body `GET /agent` returns (see
`api/routes/agent.py`). This module defines data shape only — it has
no logic, and no dependency on `Monitor`, `Scheduler`, or any
collector.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """Response body for `GET /agent`.

    Combines the agent's configured identity (from the Configuration
    Manager) with a small amount of state drawn from its most recent
    monitoring snapshot (via the SnapshotManager), for the one field
    — `platform` — that configuration alone can't answer.
    """

    agent_id: str = Field(
        description="Stable, unique identifier configured for this agent instance (`agent.id`).",
    )
    hostname: str = Field(
        description=(
            "Network hostname of the monitored host (`agent.hostname`), "
            "as configured or auto-detected."
        ),
    )
    platform: Optional[str] = Field(
        description=(
            "Full platform identification string (e.g. "
            '"Linux-7.0.0-28-generic-x86_64-with-glibc2.43"), taken from '
            "the most recent snapshot's system_info collector output. "
            "`null` if no monitoring cycle has completed yet, or the "
            "system_info collector is not enabled."
        ),
    )
    api_version: str = Field(
        description=(
            "Version of the running Linux Insight Agent API, matching "
            "the FastAPI application's own `version`."
        ),
    )
    scheduler_interval: int = Field(
        description=(
            "Configured seconds between the end of one monitoring cycle "
            "and the start of the next (`scheduler.refresh_interval`)."
        ),
    )
    status: Literal["success", "partial_success", "unknown"] = Field(
        description=(
            "Overall status of the most recently completed monitoring "
            "cycle, mirroring the Monitor's own `monitoring.status` "
            'values. "unknown" if no monitoring cycle has completed yet.'
        ),
    )
