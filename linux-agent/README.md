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

## Status

Project skeleton only. No monitoring code has been written.

# Detailed Documentation

In-depth, per-collector documentation lives under [`docs/`](docs/) so this README can stay a short entry point:

- [System Information Collector](docs/system-info.md)
- [CPU Collector](docs/cpu.md)
- [Memory Collector](docs/memory.md)
- [Disk Collector](docs/disk.md)
- [Network Collector](docs/network.md)
- [Process Collector](docs/process.md)
- [Monitor](docs/monitor.md)
