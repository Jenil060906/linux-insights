# Linux Agent

The Linux Agent is the host-side component of Linux Insight. It runs on a monitored Linux server, collects system metrics and logs, and reports them to the backend so the dashboard can display live data.

This package is mostly an **empty project skeleton** — collection logic is being implemented incrementally. The first collector, `collectors/system_info.py`, is now implemented; the rest of the agent (other collectors, config loading, core runtime) is still not implemented.

## Purpose

- Run as a lightweight background process on a monitored Linux host.
- Collect system-level data (CPU, memory, disk, network, processes, logs) — in progress.
- Send collected data to the Linux Insight backend for storage and display.

## Structure

```
linux-agent/
├── collectors/     # Individual metric/log collectors
│   └── system_info.py   # Implemented — static host/system identity info
├── config/         # Agent configuration loading (not yet implemented)
├── core/           # Core agent runtime (not yet implemented)
├── README.md
├── requirements.txt
└── main.py         # Entry point (placeholder — no logic yet)
```

## CPU Collector

`collectors/cpu.py` collects CPU-related metrics for the host via `collect_cpu_info()`, which returns a plain `dict`. Uses `psutil` (declared in `requirements.txt`); no threading, scheduling, or monitor integration.

Full details (metrics, `psutil` functions used, expected output, future enhancements) live in [`docs/cpu.md`](docs/cpu.md).

### Metrics

| Key | Description |
|---|---|
| `cpu_usage_percent` | Overall CPU utilization percentage |
| `physical_cores` | Number of physical CPU cores |
| `logical_cores` | Number of logical CPU cores (includes SMT/hyper-threading siblings) |
| `cpu_frequency` | Dict with `current`, `min`, `max` CPU frequency in MHz |
| `cpu_load` | Dict with `1min`, `5min`, `15min` system load averages |
| `cpu_times` | Dict of accumulated CPU time (seconds) per state (user, system, idle, etc.) |

Any value that can't be determined falls back to `"unknown"` (or an empty dict for `cpu_times`) rather than raising.

### `psutil` Functions Used

- `psutil.cpu_percent(interval=0.1)` — `cpu_usage_percent`
- `psutil.cpu_count(logical=False)` — `physical_cores`
- `psutil.cpu_count(logical=True)` — `logical_cores`
- `psutil.cpu_freq()` — `cpu_frequency`
- `psutil.getloadavg()` — `cpu_load`
- `psutil.cpu_times()` — `cpu_times`

### Future Enhancements

- Per-core (not just aggregate) usage percentages and frequencies.
- Non-blocking usage sampling (cache the previous `cpu_percent` call instead of a blocking `interval`), once a scheduler exists to call it periodically.
- CPU temperature, where the platform exposes it.
- Context-manager or interval-based sampling for more accurate usage percentages under sustained load.
## Implemented Collectors

### System Information Collector (`collectors/system_info.py`)

#### Purpose

Collects static, identity-level information about the host — data that stays constant between collection cycles (as opposed to volatile metrics like CPU load or memory usage, which live in the other collectors). Exposed via a single function, `collect_system_info()`, which returns a plain `dict`.

#### Collected Metrics

| Key | Description |
|---|---|
| `hostname` | Network hostname of the host |
| `os` | Operating system name (e.g. `Linux`) |
| `os_version` | Detailed OS release/version string |
| `kernel_version` | Kernel release version |
| `architecture` | Machine hardware architecture (e.g. `x86_64`) |
| `processor` | Processor model name, if available (see fallback below) |
| `platform` | Full platform identification string |
| `python_version` | Version of the running Python interpreter |

#### Python Modules Used

- `platform` — OS, kernel, architecture, processor, platform string, Python version.
- `socket` — hostname.
- `/proc/cpuinfo` (read directly, no extra import) — Linux-specific fallback for `processor`.

Standard library only — no third-party dependencies (e.g. no `psutil`).

**Processor fallback strategy:** on most Linux distributions, `platform.processor()` doesn't return a real CPU model — it reflects `uname -p`, which the kernel/libc typically leaves empty (surfaced as `""` or `"unknown"`/`"Unknown"`). To still report a meaningful value:

1. Try `platform.processor()` first.
2. If it's empty or `"unknown"`/`"Unknown"`, parse the `model name` field out of `/proc/cpuinfo`, which the kernel always populates on x86/x86_64.
3. Return that model name if found.
4. If both methods fail, return `"unknown"`.

#### Expected Output

```python
{
    "hostname": "alphaSenate",
    "os": "Linux",
    "os_version": "#28-Ubuntu SMP PREEMPT_DYNAMIC Sun Jun 21 01:01:36 UTC 2026",
    "kernel_version": "7.0.0-28-generic",
    "architecture": "x86_64",
    "processor": "Intel(R) Core(TM) i7-14650HX",
    "platform": "Linux-7.0.0-28-generic-x86_64-with-glibc2.43",
    "python_version": "3.14.4"
}
```

Any value that can't be determined falls back to `"unknown"` rather than raising, so one missing field never blocks the rest of the collection.

#### Future Improvements

- Add uptime / boot time.
- Detect virtualization/container context (bare metal vs. VM vs. container).
- Cache the result for the agent's lifetime, since this data is static per run.
- Add unit tests with mocked `platform`/`socket` calls to cover the `"unknown"` fallback path.

## Snapshot Manager

`core/snapshot.py` implements `SnapshotManager` — a thread-safe, in-memory holder for exactly one snapshot at a time. Full details (architecture, data flow, thread safety, lifecycle) live in [`docs/snapshot.md`](docs/snapshot.md).

**Why snapshots exist.** Collecting host metrics and reading them back are two different concerns happening on two different schedules — a `Monitor` cycle runs periodically in the background, while anything that wants "the current state of the host" needs it on demand, right now. A snapshot is the hand-off point between those two: one complete, self-sufficient, point-in-time reading of the whole host, so a reader never has to know how or when it was produced.

**How they interact with the Monitor.** A snapshot *is* whatever `Monitor.run()` returns — `SnapshotManager` doesn't build, transform, or reinterpret it in any way. It simply stores the exact dictionary it's given via `update_snapshot()` and hands back an identical copy on request.

**How the Scheduler updates them.** `SnapshotManager` is injected into the `Scheduler` at construction (the `Scheduler` never creates its own). After every monitoring cycle that completes without raising, the `Scheduler` calls `monitor.run()` and immediately passes the result to `snapshot_manager.update_snapshot(snapshot)` — so the stored snapshot is refreshed automatically on the same fixed interval the `Scheduler` already runs on, with no separate wiring required.

**Why only the latest snapshot is stored.** `SnapshotManager` models *current state*, not history — the same way a gauge shows its latest reading rather than a log of every past one. Each new snapshot fully replaces the previous one, which keeps memory usage constant no matter how long the agent runs, and matches how the rest of the agent already treats a snapshot: a complete reading in its own right, not one entry in a growing series.

## Status

Project skeleton only. No monitoring code has been written.

# Detailed Documentation

| Module | Documentation |
|---------|---------------|
| System Information | docs/system-info.md |
| CPU Collector | docs/cpu.md |
| Memory Collector | docs/memory.md |
| Disk Collector | docs/disk.md |
| Network Collector | docs/network.md |
| Process Collector | docs/process.md |
| Monitor | docs/monitor.md |
First collector (`system_info.py`) implemented. Everything else — remaining collectors, configuration loading, core runtime — is still a project skeleton with no code written.
