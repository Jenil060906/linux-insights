"""CPU collector.

Collects CPU-related metrics from the host using ``psutil``: overall
utilization, physical/logical core counts, current frequency, system
load averages, and per-state CPU time accounting. For static host
identity information (hostname, OS, architecture, etc.), see
``system_info.py``.
"""

from typing import Any, Dict

import psutil


def collect_cpu_info() -> Dict[str, Any]:
    """Collect CPU-related metrics for the current host.

    Returns:
        A dictionary with the following keys:
            - "cpu_usage_percent": Overall CPU utilization percentage,
              sampled over a short blocking interval.
            - "physical_cores": Number of physical CPU cores.
            - "logical_cores": Number of logical CPU cores (includes
              SMT/hyper-threading siblings).
            - "cpu_frequency": Dict with "current", "min", and "max"
              CPU frequency in MHz.
            - "cpu_load": Dict with "1min", "5min", and "15min" system
              load averages.
            - "cpu_times": Dict of accumulated CPU time, in seconds,
              per state (user, system, idle, etc.).

        Any field that cannot be determined is set to "unknown"
        instead of raising, so a single unavailable value never
        prevents the rest of the CPU information from being
        collected.

    Raises:
        OSError: If none of the CPU information sources are reachable
            at all, indicating a broader environment failure.
    """
    try:
        return {
            "cpu_usage_percent": _safe_call(
                lambda: psutil.cpu_percent(interval=0.1)
            ),
            "physical_cores": _safe_call(
                lambda: psutil.cpu_count(logical=False)
            ),
            "logical_cores": _safe_call(
                lambda: psutil.cpu_count(logical=True)
            ),
            "cpu_frequency": _get_cpu_frequency(),
            "cpu_load": _get_cpu_load(),
            "cpu_times": _get_cpu_times(),
        }
    except OSError as error:
        raise OSError(f"Failed to collect CPU information: {error}") from error


def _get_cpu_frequency() -> Dict[str, Any]:
    """Read the current, minimum, and maximum CPU frequency.

    Returns:
        A dictionary with "current", "min", and "max" keys (MHz), or
        "unknown" for each if the host does not expose frequency
        scaling information (common in some virtualized/containerized
        environments, where ``psutil.cpu_freq()`` returns ``None``).
    """
    try:
        frequency = psutil.cpu_freq()
    except (OSError, RuntimeError, NotImplementedError):
        frequency = None

    if frequency is None:
        return {"current": "unknown", "min": "unknown", "max": "unknown"}
    return {
        "current": frequency.current,
        "min": frequency.min,
        "max": frequency.max,
    }


def _get_cpu_load() -> Dict[str, Any]:
    """Read the 1/5/15-minute system load averages.

    Returns:
        A dictionary with "1min", "5min", and "15min" keys, or
        "unknown" for each if load averages are not available on this
        platform.
    """
    try:
        load_1min, load_5min, load_15min = psutil.getloadavg()
    except (OSError, AttributeError):
        return {"1min": "unknown", "5min": "unknown", "15min": "unknown"}
    return {"1min": load_1min, "5min": load_5min, "15min": load_15min}


def _get_cpu_times() -> Dict[str, Any]:
    """Read accumulated CPU time per state.

    Returns:
        A dictionary of CPU time in seconds per state (e.g. "user",
        "system", "idle", "iowait" on Linux — the exact set of states
        is platform-dependent), or an empty dictionary if CPU times
        are not available.
    """
    try:
        return dict(psutil.cpu_times()._asdict())
    except (OSError, RuntimeError):
        return {}


def _safe_call(func) -> Any:
    """Call a zero-argument info function, falling back to "unknown".

    Args:
        func: A zero-argument callable (e.g. a ``psutil`` accessor).

    Returns:
        The callable's return value, or "unknown" if the call raises
        an exception or returns ``None``.
    """
    try:
        value = func()
        return value if value is not None else "unknown"
    except (OSError, RuntimeError, ValueError, AttributeError):
        return "unknown"
