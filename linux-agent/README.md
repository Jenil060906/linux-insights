# Linux Agent

The Linux Agent is the host-side component of Linux Insight. It runs on a monitored Linux server, collects system metrics and logs, and reports them to the backend so the dashboard can display live data.

This package is currently an **empty project skeleton** — no collection or monitoring logic has been implemented yet. It exists to establish the project's structure ahead of Week 2 development.

## Purpose

- Run as a lightweight background process on a monitored Linux host.
- Collect system-level data (CPU, memory, disk, network, processes, logs) — to be implemented.
- Send collected data to the Linux Insight backend for storage and display.

## Structure

```
linux-agent/
├── collectors/     # Individual metric/log collectors (not yet implemented)
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
