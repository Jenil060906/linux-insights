"""Response schema for the health check endpoint.

Defines `HealthResponse`, the response body `GET /health` returns
(see `api/routes/health.py`). This module defines data shape only —
it has no logic, and no dependency on `Monitor`, `SnapshotManager`,
or any other agent-internal component.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response body for `GET /health`.

    Represents a liveness signal only: that the API process itself is
    up and able to respond. It says nothing about whether the
    underlying agent (its Monitor, Scheduler, or SnapshotManager) is
    healthy or has ever produced a snapshot — other endpoints are
    responsible for reporting that.
    """

    status: Literal["healthy"] = Field(
        description=(
            'Always "healthy" — this endpoint performs no dependency '
            "checks, so any response it returns reports this same "
            "fixed status; only the absence of a response indicates "
            "the service is not live."
        ),
    )
    service: str = Field(
        description="Human-readable name of the service being checked.",
    )
    version: str = Field(
        description=(
            "The running API's version, matching the FastAPI "
            "application's own `version` (see `api/app.py`)."
        ),
    )
    timestamp: datetime = Field(
        description="UTC timestamp of when this response was generated.",
    )
