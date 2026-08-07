"""Collector selection.

Resolves configured collector names (`monitoring.enabled_collectors`)
into the concrete `(name, function)` pairs `Monitor` should run. This
is the one place that configuration value is actually consulted —
`Monitor` itself never reads it, never reads configuration at all,
and never knows this module exists. The resolved list is handed to
`Monitor` from the composition layer (`core.engine.MonitoringEngine`)
through plain constructor injection (`Monitor(collectors=...)`).

This module performs no I/O and holds no state: it takes a list of
names and `Monitor`'s own collector registry, and returns a filtered,
correctly-ordered subset — or raises if the names don't resolve to a
usable, non-empty set of collectors.
"""

from typing import Sequence, Tuple

from config.validator import InvalidEnabledCollectorsError, UnknownCollectorError
from core.monitor import CollectorFunction, Monitor


def resolve_enabled_collectors(
    enabled_collector_names: Sequence[str],
) -> Tuple[Tuple[str, CollectorFunction], ...]:
    """Resolve configured collector names into ordered `(name, function)` pairs.

    Args:
        enabled_collector_names: Collector names from
            `monitoring.enabled_collectors`, in whatever order
            configuration happens to list them.

    Returns:
        The subset of `Monitor`'s full collector registry
        (`Monitor._COLLECTORS`) whose name appears in
        `enabled_collector_names` — in `Monitor`'s own fixed execution
        order (system_info -> cpu -> memory -> disk -> network ->
        process), never the order `enabled_collector_names` happens to
        list them in. A name appearing more than once in
        `enabled_collector_names` still resolves to a single entry.

    Raises:
        UnknownCollectorError: If any name in `enabled_collector_names`
            does not match a collector that exists.
        InvalidEnabledCollectorsError: If no collectors remain once
            resolved — e.g. `enabled_collector_names` is empty. A
            monitoring cycle with zero collectors would silently do
            nothing, which is treated as a configuration error rather
            than allowed to run.
    """
    requested_names = set(enabled_collector_names)
    known_names = {name for name, _ in Monitor._COLLECTORS}

    unknown_names = sorted(requested_names - known_names)
    if unknown_names:
        raise UnknownCollectorError(
            "Configuration error: 'monitoring.enabled_collectors' names "
            f"unknown collector(s) {unknown_names!r}; known collectors "
            f"are {sorted(known_names)!r}."
        )

    resolved_collectors = tuple(
        (name, function)
        for name, function in Monitor._COLLECTORS
        if name in requested_names
    )

    if not resolved_collectors:
        raise InvalidEnabledCollectorsError(
            "Configuration error: 'monitoring.enabled_collectors' does not "
            "enable any collectors; at least one must be enabled."
        )

    return resolved_collectors
