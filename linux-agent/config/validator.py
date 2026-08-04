"""Configuration validation.

Checks a parsed :class:`~config.config_loader.Config` for the handful
of properties the rest of the agent relies on being present and
well-formed, and raises a specific, descriptive exception the first
time one of them isn't. This module only inspects configuration data —
it never modifies the `Config`/values it's given, and it never
constructs or starts a `Monitor`, `Scheduler`, `SnapshotManager`, or
any other application component.
"""

from typing import FrozenSet

from config.config_loader import Config
from core.monitor import Monitor


class ValidationError(Exception):
    """Base class for all configuration validation failures."""


class MissingAgentIDError(ValidationError):
    """Raised when `agent.id` is missing, not a string, or empty.

    `agent.id` is the only mandatory field this module enforces —
    unlike `agent.hostname` (optional; see
    `config.config_loader._apply_hostname_default`) or
    `agent.location` (optional, never validated), an agent has no
    usable identity without it.
    """


class InvalidRefreshIntervalError(ValidationError):
    """Raised when `scheduler.refresh_interval` is not a positive integer."""


class InvalidEnabledCollectorsError(ValidationError):
    """Raised when `monitoring.enabled_collectors` is missing or malformed.

    Covers structural problems only (absent, not a list, empty, or
    containing non-string entries) — a well-formed list containing a
    name that isn't an actual project collector raises
    `UnknownCollectorError` instead.
    """


class UnknownCollectorError(ValidationError):
    """Raised when `monitoring.enabled_collectors` names a collector.

    Raised when that collector does not exist anywhere in the
    project (i.e. it is not one of the collectors `Monitor` knows how
    to run).
    """


def validate_config(config: Config) -> None:
    """Validate a parsed configuration, raising on the first problem found.

    Performs exactly three checks, in order, and stops at the first
    one that fails:

    1. `agent.id` is a non-empty string.
    2. `scheduler.refresh_interval` is a positive integer.
    3. Every name in `monitoring.enabled_collectors` corresponds to a
       collector that actually exists in the project.

    `agent.hostname` and `agent.location` are both optional and are
    not checked here — `agent.hostname` is always populated by
    `config.config_loader.load_config` before validation ever sees
    it (via `socket.gethostname()` if left blank), and
    `agent.location` is purely descriptive with no constraint to
    enforce.

    `config` itself, and the values within it, are only read — never
    modified.

    Args:
        config: The `Config` to validate, as returned by
            `config.config_loader.load_config`.

    Raises:
        MissingAgentIDError: If `agent.id` is missing, not a string,
            or empty (after stripping surrounding whitespace).
        InvalidRefreshIntervalError: If `scheduler.refresh_interval`
            is missing or is not a positive integer.
        InvalidEnabledCollectorsError: If
            `monitoring.enabled_collectors` is missing, is not a list,
            is empty, or contains a non-string entry.
        UnknownCollectorError: If `monitoring.enabled_collectors`
            names one or more collectors that don't exist in the
            project.
    """
    _validate_agent_id(config)
    _validate_refresh_interval(config)
    _validate_enabled_collectors(config)


def _validate_agent_id(config: Config) -> None:
    """Ensure `agent.id` is present and non-empty.

    Raises:
        MissingAgentIDError: If the value is missing, not a string, or
            empty (after stripping surrounding whitespace).
    """
    agent = config.get("agent")
    agent_id = agent.get("id") if isinstance(agent, dict) else None

    if not isinstance(agent_id, str) or not agent_id.strip():
        raise MissingAgentIDError(
            "Configuration error: 'agent.id' must be a non-empty string."
        )


def _validate_refresh_interval(config: Config) -> None:
    """Ensure `scheduler.refresh_interval` is a positive integer.

    `bool` is intentionally rejected even though it is technically a
    subclass of `int` in Python, since `true`/`false` are never a
    meaningful interval.

    Raises:
        InvalidRefreshIntervalError: If the value is missing, not an
            `int`, or not greater than zero.
    """
    scheduler = config.get("scheduler")
    refresh_interval = (
        scheduler.get("refresh_interval") if isinstance(scheduler, dict) else None
    )

    is_valid_integer = (
        isinstance(refresh_interval, int)
        and not isinstance(refresh_interval, bool)
        and refresh_interval > 0
    )
    if not is_valid_integer:
        raise InvalidRefreshIntervalError(
            "Configuration error: 'scheduler.refresh_interval' must be a "
            f"positive integer, got {refresh_interval!r}."
        )


def _validate_enabled_collectors(config: Config) -> None:
    """Ensure `monitoring.enabled_collectors` names only real collectors.

    Raises:
        InvalidEnabledCollectorsError: If the value is missing, is not
            a non-empty list, or contains a non-string entry.
        UnknownCollectorError: If one or more listed names are not
            among the collectors that exist in the project.
    """
    monitoring = config.get("monitoring")
    enabled_collectors = (
        monitoring.get("enabled_collectors") if isinstance(monitoring, dict) else None
    )

    if (
        not isinstance(enabled_collectors, list)
        or not enabled_collectors
        or not all(isinstance(name, str) for name in enabled_collectors)
    ):
        raise InvalidEnabledCollectorsError(
            "Configuration error: 'monitoring.enabled_collectors' must be a "
            f"non-empty list of collector names, got {enabled_collectors!r}."
        )

    known_collectors = _get_known_collector_names()
    unknown_collectors = [
        name for name in enabled_collectors if name not in known_collectors
    ]
    if unknown_collectors:
        raise UnknownCollectorError(
            "Configuration error: 'monitoring.enabled_collectors' names "
            f"unknown collector(s) {unknown_collectors!r}; known collectors "
            f"are {sorted(known_collectors)!r}."
        )


def _get_known_collector_names() -> FrozenSet[str]:
    """Return the names of every collector that actually exists.

    Sourced directly from `Monitor`'s own collector registry, so this
    module never maintains a second, separately-updated list of
    collector names that could drift out of sync with the project.

    Returns:
        The set of collector names `Monitor` knows how to run (e.g.
        `{"system_info", "cpu", "memory", "disk", "network",
        "process"}`).
    """
    return frozenset(name for name, _ in Monitor._COLLECTORS)
