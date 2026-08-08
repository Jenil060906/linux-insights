"""FastAPI dependency providers for the Linux Insight Agent API.

Defines the dependency-injectable accessor functions route handlers
use to reach the agent's shared `SnapshotManager` and `Config` — via
FastAPI's `Depends()` mechanism, never by constructing either object
themselves.

Neither provider constructs, owns, or mutates the object it returns.
Both are expected to already exist as attributes on `request.app.state`
— attached once, elsewhere, during application startup (see
`api/app.py`). This module holds no state of its own: each call simply
reads whatever is already attached to the running application
instance, so there is nothing here that can drift out of sync with the
single, real `SnapshotManager`/`Config` the rest of the agent is
actually using.

Only `SnapshotManager` and `Config` are exposed here. This module has
no knowledge of `Monitor`, `Scheduler`, or any collector, and never
imports them.
"""

from typing import Annotated, Type, TypeVar

from fastapi import Depends, Request

from config.config_loader import Config
from core.snapshot import SnapshotManager

_StateValue = TypeVar("_StateValue")


def get_snapshot_manager(request: Request) -> SnapshotManager:
    """Provide the application's shared `SnapshotManager`.

    Intended for use with FastAPI's dependency injection, e.g.::

        @router.get("/snapshot")
        def read_snapshot(
            snapshot_manager: SnapshotManagerDependency,
        ) -> ...:
            ...

    Route handlers should always obtain a `SnapshotManager` this way
    rather than constructing one themselves — a handler-constructed
    `SnapshotManager` would be empty and disconnected from the one the
    agent's Scheduler is actually updating.

    Args:
        request: The current request, injected automatically by
            FastAPI. Used only to reach `request.app.state`, where the
            application's `SnapshotManager` is expected to already be
            attached.

    Returns:
        The application's single, shared `SnapshotManager` instance.

    Raises:
        RuntimeError: If no `SnapshotManager` instance is attached to
            `request.app.state` — meaning the application was not
            started correctly.
    """
    return _get_state_value(request, "snapshot_manager", SnapshotManager)


def get_config(request: Request) -> Config:
    """Provide the application's loaded, validated `Config`.

    Intended for use with FastAPI's dependency injection, the same way
    as `get_snapshot_manager`. Route handlers should always obtain
    configuration this way rather than calling
    `config.config_loader.load_config` themselves — doing so per
    request would re-read and re-parse `config.yaml` on every call
    instead of reusing the single `Config` the application was started
    with.

    Args:
        request: The current request, injected automatically by
            FastAPI. Used only to reach `request.app.state`, where the
            application's `Config` is expected to already be attached.

    Returns:
        The application's loaded `Config`.

    Raises:
        RuntimeError: If no `Config` instance is attached to
            `request.app.state` — meaning the application was not
            started correctly.
    """
    return _get_state_value(request, "config", Config)


def _get_state_value(
    request: Request, attribute_name: str, expected_type: Type[_StateValue]
) -> _StateValue:
    """Read one required attribute off `request.app.state`, or raise clearly.

    Shared by every provider in this module so each one stays a
    one-line accessor, and so a missing or wrongly-typed attribute
    always fails the same, explicit way rather than surfacing as a
    bare `AttributeError` from deep inside Starlette's `State` object.

    Args:
        request: The current request.
        attribute_name: The `request.app.state` attribute to read.
        expected_type: The type `request.app.state.<attribute_name>`
            is expected to be an instance of.

    Returns:
        `request.app.state.<attribute_name>`, typed as `expected_type`.

    Raises:
        RuntimeError: If the attribute is missing, or is not an
            instance of `expected_type`.
    """
    value = getattr(request.app.state, attribute_name, None)
    if not isinstance(value, expected_type):
        found = "nothing" if value is None else type(value).__name__
        raise RuntimeError(
            f"Application state is missing a valid '{attribute_name}' "
            f"({expected_type.__name__} expected, found {found}). It "
            "must be attached to app.state during application startup "
            "before any request can be served."
        )
    return value


# `Annotated` dependency aliases, for routers to use directly as a
# parameter type (the current recommended FastAPI style) instead of
# repeating `Depends(get_snapshot_manager)` / `Depends(get_config)` at
# every call site:
#
#     def read_snapshot(snapshot_manager: SnapshotManagerDependency): ...
SnapshotManagerDependency = Annotated[SnapshotManager, Depends(get_snapshot_manager)]
ConfigDependency = Annotated[Config, Depends(get_config)]
