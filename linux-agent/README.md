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

## Configuration Manager

`config/config_loader.py` and `config/validator.py` implement the Configuration Manager — reading `config.yaml` into a `Config` object and validating the values the rest of the agent depends on. Full details (structure, loading process, validation rules) live in [`docs/configuration.md`](docs/configuration.md).

**Why configuration is externalized.** Things like an agent's identity, how often it monitors the host, and which collectors it runs vary per deployment — they shouldn't require editing Python source to change. Externalizing them into `config.yaml` means an operator can change that behavior per host, and gives every component one shared place to get its settings from, instead of each one hardcoding its own.

**Current configuration options.**

| Option | Required | Description |
|---|---|---|
| `agent.id` | Yes | Stable, unique identifier for this agent instance. |
| `agent.hostname` | No | Network hostname of the monitored host; auto-detected via `socket.gethostname()` at load time if left blank. |
| `agent.location` | No | Free-form, human-readable label for this host's location. |
| `scheduler.refresh_interval` | Yes | Seconds between the end of one monitoring cycle and the start of the next. |
| `monitoring.enabled_collectors` | Yes | Which collectors the Monitor runs; every name must match an existing collector. |

**How the Scheduler uses the refresh interval.** Configuration is loaded and validated once, at application startup — not inside the Scheduler itself. The resulting `scheduler.refresh_interval` value is then passed into `Scheduler`'s `interval_seconds` constructor argument via dependency injection, the same way its `Monitor` and `SnapshotManager` are supplied. The Scheduler never reads `config.yaml` or hardcodes an interval of its own — it only knows the number it was given.

**How the Monitor's collector list is selected.** `monitoring.enabled_collectors` is honored the same way, one step removed from the Monitor itself: `core/collector_selection.py` resolves the configured names into the actual collector functions (preserving the Monitor's fixed execution order, not configuration's), and `core/engine.py` injects that resolved list into `Monitor`'s constructor. The Monitor never reads `config.yaml`, never imports anything from `config/`, and has no idea the list it's running was filtered from configuration — it only ever sees plain collector functions. A collector left out of `enabled_collectors` never runs and never appears in the resulting snapshot. Full details live in [`docs/monitor.md`](docs/monitor.md#collector-selection).

**How future components will use the same configuration system.** Any future component that needs configurable behavior follows the same pattern: load `config.yaml` through `config_loader.load_config()`, validate whatever it needs (via `validator.py`'s existing checks, or additional ones added the same way), and receive the resulting values through constructor injection at startup, just like the Scheduler does today. New top-level sections can be added to `config.yaml` for those components without needing to change the sections already there.

## Unified Monitoring Engine

`core/engine.py` implements `MonitoringEngine` — the composition layer that wires the Configuration Manager, Scheduler, Monitor, and Snapshot Manager together into one production entry point, without changing what any of them individually does. Full details (architecture, dependency flow, startup sequence, thread model) live in [`docs/unified-monitoring-engine.md`](docs/unified-monitoring-engine.md).

**The Configuration → Scheduler → Monitor → SnapshotManager workflow.** `MonitoringEngine.bootstrap()` loads and validates `config.yaml` first, then uses it to build the other three: `scheduler.refresh_interval` and the resolved `monitoring.enabled_collectors` list are both read from configuration once, up front, and injected into the `Scheduler` and `Monitor` constructors respectively. From there, the runtime flow is: `Scheduler` runs on its configured interval and calls `Monitor.run()` each cycle; `Monitor` runs only its configured collectors and returns a snapshot; `Scheduler` then hands that snapshot to `SnapshotManager`, which stores it as the latest reading. Configuration only ever flows in — nothing downstream reads it again or reaches back for more.

**Why responsibilities are separated.** Each component already had one clear job before the engine existed — read configuration, run collectors, pace repeated collection, hold the latest reading — and the engine is deliberately built to preserve that rather than collapse it into one class. Keeping them separate means each piece can be reasoned about, tested, and changed independently: the `Monitor` doesn't need to know configuration exists, the `Scheduler` doesn't need to know what a collector is, and `SnapshotManager` doesn't need to know either exists. `MonitoringEngine` is the one place that composition happens, via dependency injection, so that separation doesn't come at the cost of every caller needing to wire four objects together by hand.

**How this prepares the project for FastAPI and Windows Dashboard integration.** Because the engine already exposes everything through one small, synchronous facade — `start()`, `stop()`, `is_running()`, `get_latest_snapshot()`, `get_snapshot_timestamp()` — and `get_latest_snapshot()` already returns a plain, deep-copied, JSON-serializable dictionary, adding a way to serve that data (e.g. a future FastAPI endpoint, or a Windows-based dashboard client polling for the latest reading) would only mean building a thin new layer on top of this facade. No changes would be required to `Monitor`, `Scheduler`, `SnapshotManager`, or the Configuration Manager to support that — they stay exactly as decoupled from any future transport or client as they are from each other today.

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
