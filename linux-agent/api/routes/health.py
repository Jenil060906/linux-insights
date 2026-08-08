"""Health check route for the Linux Insight Agent API.

Defines `GET /health`: a minimal liveness endpoint reporting that the
API process itself is running and able to respond. It deliberately
never touches collectors, the Monitor, or the SnapshotManager — those
describe the state of the monitored host and the agent's own
monitoring loop, which is a separate concern from "is this API
process up".
"""

from datetime import datetime, timezone

from fastapi import APIRouter, status

from api.schemas.health import HealthResponse

router = APIRouter(tags=["health"])

# Fixed response values for this endpoint. `_API_VERSION` mirrors the
# FastAPI application's own `version` (see `api/app.py`) and should be
# kept in sync with it.
_SERVICE_NAME = "Linux Insight Agent"
_API_VERSION = "1.0.0"


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
)
def get_health() -> HealthResponse:
    """Report that the API process is running.

    A liveness check only, deliberately kept lightweight: it performs
    no I/O, queries no collector, and reads nothing from the
    `SnapshotManager` — it only confirms that this API process itself
    is up and can handle a request. A `200 OK` response with this
    body is the only outcome this endpoint ever produces; if the
    process itself is down or unresponsive, no response is returned
    at all, which is exactly what a liveness check is meant to
    detect.

    Returns:
        A `HealthResponse` reporting a fixed "healthy" status, the
        service name, the running API version, and the current UTC
        timestamp.
    """
    return HealthResponse(
        status="healthy",
        service=_SERVICE_NAME,
        version=_API_VERSION,
        timestamp=datetime.now(timezone.utc),
    )
