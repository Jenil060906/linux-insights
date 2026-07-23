# System Information Collector

`collectors/system_info.py` — static host identity information.

> **Note:** Design documented here ahead of/alongside implementation. Check `collectors/system_info.py` in the branch you're working from for the current code state.

## Overview

The System Information Collector reports static host-identity data (hostname, OS, kernel, architecture, processor, platform string, Python version) as a single `dict`, using only the Python standard library. It is the first collector implemented in `linux-agent/collectors/` and establishes the conventions (per-field `"unknown"` fallback, no printing/CLI, single public entry point) the other collectors follow.

## Purpose

Collects static, identity-level information about the host — data that stays constant between collection cycles, as opposed to volatile metrics like CPU load or memory usage (which live in the other collectors). Exposed via a single function, `collect_system_info()`, which returns a plain `dict`.

## Metrics

| Key | Description |
|---|---|
| `hostname` | Network hostname of the host |
| `os` | Operating system name (e.g. `Linux`) |
| `os_version` | Detailed OS release/version string |
| `kernel_version` | Kernel release version |
| `architecture` | Machine hardware architecture (e.g. `x86_64`) |
| `processor` | Processor model name, if available (see Design Notes for the fallback strategy) |
| `platform` | Full platform identification string |
| `python_version` | Version of the running Python interpreter |

Any value that can't be determined falls back to `"unknown"` rather than raising, so one missing field never blocks the rest of the collection.

## Python Modules Used

- `platform` — standard library
- `socket` — standard library

Standard library only — no third-party dependencies (e.g. no `psutil`).

## Functions Used

| Function | Populates |
|---|---|
| `socket.gethostname()` | `hostname` |
| `platform.system()` | `os` |
| `platform.version()` | `os_version` |
| `platform.release()` | `kernel_version` |
| `platform.machine()` | `architecture` |
| `platform.processor()` | `processor` (primary attempt — see Design Notes) |
| `platform.platform()` | `platform` |
| `platform.python_version()` | `python_version` |
| Direct read of `/proc/cpuinfo` (`model name` field) | `processor` (fallback — see Design Notes) |

Internal helpers: `_get_processor_name()` (processor + fallback logic), `_safe_call()` (generic wrapper that maps exceptions/empty values to `"unknown"`).

## Expected Output

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

## Design Notes

**Processor fallback strategy.** On most Linux distributions, `platform.processor()` doesn't return a real CPU model — it reflects `uname -p`, which the kernel/libc typically leaves empty (surfaced as `""` or `"unknown"`/`"Unknown"`). To still report a meaningful value:

1. Try `platform.processor()` first.
2. If it's empty or `"unknown"`/`"Unknown"`, parse the `model name` field out of `/proc/cpuinfo`, which the kernel always populates on x86/x86_64.
3. Return that model name if found.
4. If both methods fail, return `"unknown"`.

> **Warning:** the `/proc/cpuinfo` fallback is Linux-specific. On non-Linux platforms (or containers without `/proc` mounted), the collector still degrades gracefully to `"unknown"` rather than raising.

## Future Enhancements

- Add uptime / boot time.
- Detect virtualization/container context (bare metal vs. VM vs. container).
- Cache the result for the agent's lifetime, since this data is static per run.
- Add unit tests with mocked `platform`/`socket` calls to cover the `"unknown"` fallback path.
