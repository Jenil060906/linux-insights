# CPU Collector

`collectors/cpu.py` — implemented, Linux-only dynamic CPU metrics collector.

## Overview

The CPU Collector gathers dynamic, point-in-time CPU metrics for the host machine — utilization, frequency, load, and cumulative counters — as opposed to the static identity facts covered by the [System Information Collector](system-info.md). It is exposed through a single public function, `collect_cpu_info()`, which returns a plain `dict` and takes no arguments.

Like the System Information Collector, this collector is **Linux-only by design**. Rather than approximating or partially collecting on another operating system, it detects the host OS up front and returns a clearly-flagged `"unsupported_platform"` response if it isn't Linux.

## Responsibilities

`collect_cpu_info()` is responsible for, and only for:

- Detecting whether the current host operating system is Linux before collecting anything.
- Collecting logical and physical CPU core counts.
- Collecting current, minimum, and maximum CPU frequency.
- Sampling overall and per-core CPU usage percentage.
- Reading the 1/5/15-minute system load average.
- Collecting cumulative CPU time-in-state and CPU statistics counters (context switches, interrupts, syscalls) since boot.
- Degrading a single unavailable field to `"Unknown"` (or an empty `dict` for the counter fields), recording why in `errors`, instead of letting one missing value fail the whole collection.
- Returning everything as one dictionary — no side effects.

It is explicitly **not** responsible for: static host identity (hostname, OS/distribution, kernel — see [`system-info.md`](system-info.md)), scheduling repeated/periodic sampling, printing/logging output, or sending data anywhere (no network or API calls).

## Linux Dependencies

| Module / Call | Used for | Why |
|---|---|---|
| `psutil` | Core counts, CPU frequency, usage percentage (overall and per-core), and CPU time/statistics counters. | Provides a consistent, already-battle-tested cross-platform API over `/proc/cpuinfo`, `/proc/stat`, and `/sys/devices/system/cpu/` internals, so the collector doesn't need to parse those files itself. |
| `os.getloadavg()` | The 1/5/15-minute load average. | Load average is a Linux/Unix kernel concept with no meaningful cross-platform equivalent, so it's read directly from `os` rather than through a cross-platform wrapper. It's used deliberately instead of `psutil`'s own `getloadavg()` shim, and is **not emulated** on unsupported platforms — the collector already exits with `"unsupported_platform"` before this call would ever be reached on a non-Linux host. |
| `platform.system()` | The Linux-only gate at the top of `collect_cpu_info()`. | Determines whether to proceed with collection at all. |

> **Note:** No raw Linux files (e.g. `/proc/stat`, `/proc/cpuinfo`) are read directly by this collector — `psutil` and `os.getloadavg()` already cover every metric it needs. Direct file reads are reserved for cases where `psutil` doesn't expose the data (see [`system-info.md`](system-info.md#linux-dependencies) for an example: the `/proc/cpuinfo` processor-name fallback).

## Returned Metrics

All metrics live under the top-level `data` key of the returned dictionary (see [Returned Dictionary Structure](#returned-dictionary-structure)).

| Metric | Description | Example |
|---|---|---|
| `logical_cpu_count` | Number of logical CPU cores (includes SMT/hyper-threading siblings) | `4` |
| `physical_cpu_count` | Number of physical CPU cores | `4` |
| `current_frequency_mhz` | Current CPU frequency, in MHz | `2419.198` |
| `minimum_frequency_mhz` | Minimum CPU frequency, in MHz | `0.0` |
| `maximum_frequency_mhz` | Maximum CPU frequency, in MHz | `0.0` |
| `cpu_usage_percent` | Overall CPU utilization percentage, averaged across cores | `36.2` |
| `per_core_usage_percent` | CPU utilization percentage per logical core | `[40.0, 42.9, 28.6, 33.3]` |
| `load_average` | 1/5/15-minute system load average | `{"1min": 1.35, "5min": 0.64, "15min": 0.65}` |
| `cpu_times` | Accumulated CPU time (seconds) per state since boot (`user`, `system`, `idle`, `iowait`, etc. — exact keys are kernel-dependent) | `{"user": 414.74, "system": 327.9, "idle": 10003.42, ...}` |
| `cpu_stats` | CPU statistics counters since boot (`ctx_switches`, `interrupts`, `soft_interrupts`, `syscalls`) | `{"ctx_switches": 8195586, "interrupts": 8903010, ...}` |

## Returned Dictionary Structure

`collect_cpu_info()` always returns a dictionary with exactly these top-level keys:

| Key | Type | Description |
|---|---|---|
| `collector` | `str` | Always `"cpu"` — identifies which collector produced this payload. |
| `status` | `str` | `"success"` on Linux, or `"unsupported_platform"` on any other OS. |
| `timestamp` | `str` | UTC timestamp of the collection, ISO 8601 format (e.g. `2026-07-24T08:25:56.662383+00:00`), from `datetime.now(timezone.utc).isoformat()`. |
| `platform` | `str` | The detected OS name from `platform.system()` (e.g. `"Linux"`, `"Windows"`, `"Darwin"`). |
| `data` | `dict` | The metrics described in [Returned Metrics](#returned-metrics). Empty (`{}`) when `status` is `"unsupported_platform"`. |
| `errors` | `list[str]` | Human-readable messages for any field that could not be determined. Empty when everything was collected successfully. |

## Error Handling

**Unsupported platform.** Before collecting anything, the collector checks `platform.system()`. If it is not `"Linux"`, collection is skipped entirely and it returns:

```python
{
    "collector": "cpu",
    "status": "unsupported_platform",
    "platform": "Windows",
    "data": {},
    "errors": ["Linux Insight Agent supports Linux only."],
}
```

**Graceful exception handling.** On a supported (Linux) host, each field is collected independently and defensively:

- `logical_cpu_count` / `physical_cpu_count` fall back to `"Unknown"` if `psutil.cpu_count()` raises or returns `None` (it can return `None` if the count is indeterminable).
- `current_frequency_mhz` / `minimum_frequency_mhz` / `maximum_frequency_mhz` fall back to `"Unknown"` if `psutil.cpu_freq()` raises, or returns `None` — which happens on some virtualized/containerized hosts with no exposed frequency-scaling information.
- `cpu_usage_percent` / `per_core_usage_percent` fall back to `"Unknown"` if the underlying `psutil.cpu_percent()` sample raises or comes back empty.
- `load_average` falls back to `{"1min": "Unknown", "5min": "Unknown", "15min": "Unknown"}` if `os.getloadavg()` raises `OSError`.
- `cpu_times` / `cpu_stats` fall back to an empty `dict` if the corresponding `psutil` call raises.

In every case, a descriptive message is appended to `errors` and `status` remains `"success"` — one failing field never prevents the rest of the dictionary from being returned. `errors` is additive context, not a failure signal on its own.

## Example Output

```python
{
    "collector": "cpu",
    "status": "success",
    "timestamp": "2026-07-24T08:25:56.662383+00:00",
    "platform": "Linux",
    "data": {
        "logical_cpu_count": 4,
        "physical_cpu_count": 4,
        "current_frequency_mhz": 2419.198,
        "minimum_frequency_mhz": 0.0,
        "maximum_frequency_mhz": 0.0,
        "cpu_usage_percent": 36.2,
        "per_core_usage_percent": [40.0, 42.9, 28.6, 33.3],
        "load_average": {
            "1min": 1.34619140625,
            "5min": 0.6435546875,
            "15min": 0.65478515625
        },
        "cpu_times": {
            "user": 414.74,
            "nice": 0.36,
            "system": 327.9,
            "idle": 10003.42,
            "iowait": 17.81,
            "irq": 0.0,
            "softirq": 86.25,
            "steal": 0.0,
            "guest": 0.0,
            "guest_nice": 0.0
        },
        "cpu_stats": {
            "ctx_switches": 8195586,
            "interrupts": 8903010,
            "soft_interrupts": 2715102,
            "syscalls": 0
        }
    },
    "errors": []
}
```

## Future Enhancements

- CPU temperature, where the platform exposes it (e.g. via `psutil.sensors_temperatures()`).
- CPU governor (e.g. `performance`, `powersave`), read from `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`.
- Turbo Boost / frequency-boost state, read from `/sys/devices/system/cpu/cpufreq/boost` or the equivalent MSR-based signal.
- NUMA awareness — per-node CPU and load breakdown on multi-socket/NUMA hosts.
- Non-blocking usage sampling (cache the previous `cpu_percent` call instead of a blocking `interval`), once a scheduler exists to call it periodically.
