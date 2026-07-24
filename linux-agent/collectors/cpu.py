"""CPU collector.

Collects dynamic CPU metrics for the current machine — logical and
physical core counts, current/minimum/maximum frequency, overall and
per-core usage percentage, system load average, and cumulative CPU
time/statistics counters. This collector is Linux-only: on any other
operating system, ``collect_cpu_info()`` returns an
``"unsupported_platform"`` response instead of attempting to collect
data.

Uses ``psutil`` for the metrics it already exposes reliably, and reads
the Linux-specific ``os.getloadavg()`` directly for load average
(deliberately not emulated on unsupported platforms). No Linux files
are read directly, since ``psutil`` already surfaces everything this
collector needs. Fully self-contained: no printing, logging,
scheduling, threading, or network/API calls.
"""

import os
import platform
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import psutil

_COLLECTOR_NAME = "cpu"


def collect_cpu_info() -> Dict[str, object]:
    """Collect dynamic CPU metrics for the current host.

    Linux-only: if the host operating system is not Linux, an
    ``"unsupported_platform"`` response is returned instead of
    attempting collection.

    Returns:
        On Linux, a dictionary shaped like::

            {
                "collector": "cpu",
                "status": "success",
                "timestamp": "2026-07-24T12:00:00+00:00",
                "platform": "Linux",
                "data": {
                    "logical_cpu_count": 4,
                    "physical_cpu_count": 4,
                    "current_frequency_mhz": 2419.2,
                    "minimum_frequency_mhz": 0.0,
                    "maximum_frequency_mhz": 0.0,
                    "cpu_usage_percent": 8.1,
                    "per_core_usage_percent": [7.0, 9.0, 8.5, 7.9],
                    "load_average": {"1min": 1.55, "5min": 0.92, "15min": 0.69},
                    "cpu_times": {...},
                    "cpu_stats": {...},
                },
                "errors": [],
            }

        On any non-Linux platform::

            {
                "collector": "cpu",
                "status": "unsupported_platform",
                "platform": "...",
                "data": {},
                "errors": ["Linux Insight Agent supports Linux only."],
            }

        A field that cannot be individually determined is set to
        "Unknown" and a corresponding message is appended to
        "errors", rather than the whole collection failing.
    """
    current_platform = platform.system()
    if current_platform != "Linux":
        return {
            "collector": _COLLECTOR_NAME,
            "status": "unsupported_platform",
            "platform": current_platform,
            "data": {},
            "errors": ["Linux Insight Agent supports Linux only."],
        }

    errors: List[str] = []
    cpu_usage_percent, per_core_usage_percent = _get_cpu_usage(errors)
    current_freq, minimum_freq, maximum_freq = _get_cpu_frequency(errors)

    data = {
        "logical_cpu_count": _safe_get(
            lambda: psutil.cpu_count(logical=True), "logical CPU count", errors
        ),
        "physical_cpu_count": _safe_get(
            lambda: psutil.cpu_count(logical=False), "physical CPU count", errors
        ),
        "current_frequency_mhz": current_freq,
        "minimum_frequency_mhz": minimum_freq,
        "maximum_frequency_mhz": maximum_freq,
        "cpu_usage_percent": cpu_usage_percent,
        "per_core_usage_percent": per_core_usage_percent,
        "load_average": _get_load_average(errors),
        "cpu_times": _get_cpu_times(errors),
        "cpu_stats": _get_cpu_stats(errors),
    }

    return {
        "collector": _COLLECTOR_NAME,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": current_platform,
        "data": data,
        "errors": errors,
    }


def _safe_get(func, field_name: str, errors: List[str]) -> object:
    """Call a zero-argument ``psutil``/``os`` accessor, guarding failure.

    Args:
        func: A zero-argument callable returning the metric value.
        field_name: Human-readable name of the field being collected,
            used in the error message if the call fails.
        errors: Shared list that failure messages are appended to.

    Returns:
        The callable's return value, or "Unknown" if the call raises
        an exception or returns ``None``.
    """
    try:
        value = func()
    except (OSError, RuntimeError, ValueError, AttributeError) as error:
        errors.append(f"Unable to determine {field_name}: {error}")
        return "Unknown"
    if value is None:
        errors.append(f"Unable to determine {field_name}.")
        return "Unknown"
    return value


def _get_cpu_usage(errors: List[str]) -> Tuple[object, object]:
    """Sample overall and per-core CPU usage percentage.

    A single blocking, per-core sample (``psutil.cpu_percent(interval=0.1,
    percpu=True)``) is taken, and the overall percentage is derived as
    the average of the per-core values — this avoids a second blocking
    call (and the inconsistent measurement window that would come with
    it) just to also get the aggregate figure.

    Args:
        errors: Shared list that a failure message is appended to if
            usage percentage cannot be sampled.

    Returns:
        A ``(cpu_usage_percent, per_core_usage_percent)`` tuple. Both
        are "Unknown" if sampling fails.
    """
    try:
        per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to determine CPU usage percentage: {error}")
        return "Unknown", "Unknown"
    if not per_core:
        errors.append("Unable to determine CPU usage percentage.")
        return "Unknown", "Unknown"
    overall = round(sum(per_core) / len(per_core), 1)
    return overall, per_core


def _get_cpu_frequency(errors: List[str]) -> Tuple[object, object, object]:
    """Read the current, minimum, and maximum CPU frequency.

    Args:
        errors: Shared list that a failure message is appended to if
            frequency information is not available.

    Returns:
        A ``(current, minimum, maximum)`` tuple in MHz. All three are
        "Unknown" if the host does not expose frequency scaling
        information (common in some virtualized/containerized
        environments, where ``psutil.cpu_freq()`` returns ``None``).
    """
    try:
        frequency = psutil.cpu_freq()
    except (OSError, RuntimeError, NotImplementedError) as error:
        errors.append(f"Unable to determine CPU frequency: {error}")
        return "Unknown", "Unknown", "Unknown"
    if frequency is None:
        errors.append("CPU frequency information is not available on this host.")
        return "Unknown", "Unknown", "Unknown"
    return frequency.current, frequency.min, frequency.max


def _get_load_average(errors: List[str]) -> Dict[str, object]:
    """Read the 1/5/15-minute system load average via ``os.getloadavg()``.

    Deliberately uses the Linux-specific ``os.getloadavg()`` rather
    than a cross-platform ``psutil`` equivalent, and is not emulated
    on unsupported platforms — this collector already returns
    ``"unsupported_platform"`` before reaching this point on any
    non-Linux host.

    Args:
        errors: Shared list that a failure message is appended to if
            the load average cannot be read.

    Returns:
        A dictionary with "1min", "5min", and "15min" keys, each
        "Unknown" if ``os.getloadavg()`` raises.
    """
    try:
        load_1min, load_5min, load_15min = os.getloadavg()
    except OSError as error:
        errors.append(f"Unable to determine load average: {error}")
        return {"1min": "Unknown", "5min": "Unknown", "15min": "Unknown"}
    return {"1min": load_1min, "5min": load_5min, "15min": load_15min}


def _get_cpu_times(errors: List[str]) -> Dict[str, object]:
    """Read cumulative CPU time per state via ``psutil.cpu_times()``.

    Args:
        errors: Shared list that a failure message is appended to if
            CPU times are not available.

    Returns:
        A dictionary of accumulated CPU time in seconds per state
        (e.g. "user", "system", "idle", "iowait" on Linux), or an
        empty dictionary if unavailable.
    """
    try:
        return dict(psutil.cpu_times()._asdict())
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to determine CPU times: {error}")
        return {}


def _get_cpu_stats(errors: List[str]) -> Dict[str, object]:
    """Read CPU statistics counters via ``psutil.cpu_stats()``.

    Args:
        errors: Shared list that a failure message is appended to if
            CPU statistics are not available.

    Returns:
        A dictionary with counters such as "ctx_switches",
        "interrupts", "soft_interrupts", and "syscalls" (since boot),
        or an empty dictionary if unavailable.
    """
    try:
        return dict(psutil.cpu_stats()._asdict())
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to determine CPU statistics: {error}")
        return {}
