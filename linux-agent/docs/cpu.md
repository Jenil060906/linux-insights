# CPU Collector

`collectors/cpu.py` collects CPU-related metrics for the host via `collect_cpu_info()`, which returns a plain `dict`. Uses `psutil` (declared in `requirements.txt`); no threading, scheduling, or monitor integration.

## Overview

The CPU Collector reports live CPU utilization and hardware/load information (usage percentage, core counts, frequency, load averages, per-state times) as a single `dict`, using `psutil`. It follows the same conventions as the System Information Collector: a single public entry point (`collect_cpu_info()`), per-field graceful fallback instead of raising, no printing/CLI/threading.

## Purpose

Collects real-time CPU utilization and hardware/load information: overall usage percentage, physical/logical core counts, current frequency, system load averages, and per-state CPU time accounting.

## Metrics

| Key | Description |
|---|---|
| `cpu_usage_percent` | Overall CPU utilization percentage |
| `physical_cores` | Number of physical CPU cores |
| `logical_cores` | Number of logical CPU cores (includes SMT/hyper-threading siblings) |
| `cpu_frequency` | Dict with `current`, `min`, `max` CPU frequency in MHz |
| `cpu_load` | Dict with `1min`, `5min`, `15min` system load averages |
| `cpu_times` | Dict of accumulated CPU time (seconds) per state (user, system, idle, etc.) |

Any value that can't be determined falls back to `"unknown"` (or an empty dict for `cpu_times`) rather than raising.

## Python Modules Used

- `psutil` — third-party dependency, declared in `requirements.txt`.

## Functions Used

| Function | Populates |
|---|---|
| `psutil.cpu_percent(interval=0.1)` | `cpu_usage_percent` |
| `psutil.cpu_count(logical=False)` | `physical_cores` |
| `psutil.cpu_count(logical=True)` | `logical_cores` |
| `psutil.cpu_freq()` | `cpu_frequency` |
| `psutil.getloadavg()` | `cpu_load` |
| `psutil.cpu_times()` | `cpu_times` |

Internal helpers: `_get_cpu_frequency()`, `_get_cpu_load()`, `_get_cpu_times()`, `_safe_call()` (generic wrapper that maps exceptions/`None` to `"unknown"`).

## Expected Output

```python
{
    "cpu_usage_percent": 8.1,
    "physical_cores": 4,
    "logical_cores": 4,
    "cpu_frequency": {
        "current": 2419.2,
        "min": 0.0,
        "max": 0.0
    },
    "cpu_load": {
        "1min": 1.55,
        "5min": 0.92,
        "15min": 0.69
    },
    "cpu_times": {
        "user": 635.48,
        "nice": 3.38,
        "system": 599.42,
        "idle": 24275.81,
        "iowait": 59.29,
        "irq": 0.0,
        "softirq": 131.93,
        "steal": 0.0,
        "guest": 0.0,
        "guest_nice": 0.0
    }
}
```

## Design Notes

- **Blocking sample interval.** `psutil.cpu_percent(interval=0.1)` blocks for 100ms to compute a real usage delta. This is deliberate: calling `cpu_percent()` with no interval on the very first call always returns `0.0` (it needs a prior reference point), which would be misleading in a one-shot collector with no scheduler. A future scheduler-driven design could instead call `cpu_percent(interval=None)` on a fixed cadence and rely on the delta since the previous tick (see Future Enhancements).
- **Graceful degradation.** `psutil.cpu_freq()` returns `None` on some virtualized/containerized hosts instead of raising — handled explicitly rather than relying on `_safe_call()` alone. `psutil.getloadavg()` is not available on all platforms; it's wrapped separately so its absence doesn't affect the rest of the payload.
- **No side effects.** This collector has no threading, scheduling, or monitor integration by design — it is a pure, synchronous, single-call `collect_cpu_info()` function, matching the System Information Collector's shape.

## Future Enhancements

- Per-core (not just aggregate) usage percentages and frequencies.
- Non-blocking usage sampling (cache the previous `cpu_percent` call instead of a blocking `interval`), once a scheduler exists to call it periodically.
- CPU temperature, where the platform exposes it.
- Context-manager or interval-based sampling for more accurate usage percentages under sustained load.
