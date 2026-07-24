# System Information Collector

`collectors/system_info.py` — implemented, Linux-only static host identity collector.

## Overview

The System Information Collector gathers static, identity-level facts about the host machine — the kind of data that does not change between collection cycles, as opposed to volatile metrics like CPU load or memory usage (covered by the other collectors). It is exposed through a single public function, `collect_system_info()`, which returns a plain `dict` and takes no arguments.

This collector is **Linux-only by design**: Linux Insight targets Linux hosts, so rather than silently returning partial or incorrect data on another operating system, the collector detects the host OS up front and returns a clearly-flagged `"unsupported_platform"` response if it isn't Linux.

## Responsibilities

`collect_system_info()` is responsible for, and only for:

- Detecting whether the current host operating system is Linux before collecting anything.
- Collecting the host's network hostname.
- Collecting operating system identity (`platform.system()`, distribution name/version).
- Collecting kernel version and hardware/CPU architecture.
- Collecting the running Python interpreter version and the full platform string.
- Determining the processor (CPU model) name, with a fallback strategy for Linux hosts where `platform.processor()` doesn't return one.
- Degrading a single unavailable field to `"Unknown"` (recording why in `errors`) instead of letting one missing value fail the whole collection.
- Returning everything as one dictionary — no side effects.

It is explicitly **not** responsible for: volatile/runtime metrics (CPU, memory, disk, network, process — see the other files in this directory), scheduling repeated collection, printing/logging output, or sending data anywhere (no network or API calls).

## Linux Dependencies

The collector reads the following Linux-specific resources and standard-library modules:

| Resource / Module | Used for |
|---|---|
| `/proc/cpuinfo` | Fallback source for the CPU model name (`model name` field) when `platform.processor()` doesn't return one. Read via `pathlib.Path`, and only opened if the fallback is actually needed. |
| `/etc/os-release` | Source of the Linux distribution name (`NAME`) and version (`VERSION_ID`, falling back to `VERSION`). Read via `pathlib.Path`. |
| `platform` | Operating system name, kernel/platform strings, `platform.processor()`, CPU architecture (`platform.architecture()`), Python interpreter version. |
| `socket` | Network hostname (`socket.gethostname()`). |
| `os` | `os.uname()`, used for kernel release (`.release`) and machine hardware type (`.machine`) once the host is confirmed to be Linux — `os.uname()` is a Unix-only API. |

> **Note:** `/proc/cpuinfo` and `/etc/os-release` are Linux-specific virtual/config files. Both are read defensively (existence check, then a guarded read) so a missing or unreadable file degrades the corresponding field to `"Unknown"` rather than raising.

## Returned Metrics

All metrics live under the top-level `data` key of the returned dictionary (see [Returned Dictionary Structure](#returned-dictionary-structure)).

| Metric | Description | Example |
|---|---|---|
| `hostname` | Network hostname of the host | `alphaSenate` |
| `operating_system` | Operating system name | `Linux` |
| `distribution_name` | Linux distribution name, from `/etc/os-release` | `Ubuntu` |
| `distribution_version` | Linux distribution version, from `/etc/os-release` | `26.04` |
| `kernel_version` | Kernel release version, from `os.uname().release` | `7.0.0-28-generic` |
| `machine_architecture` | Machine hardware type, from `os.uname().machine` | `x86_64` |
| `cpu_architecture` | Interpreter/CPU bitness, from `platform.architecture()[0]` | `64bit` |
| `python_version` | Version of the running Python interpreter | `3.14.4` |
| `platform_string` | Full platform identification string | `Linux-7.0.0-28-generic-x86_64-with-glibc2.43` |
| `processor_name` | CPU model name (see Error Handling for the fallback order) | `Intel(R) Core(TM) i7-14650HX` |

## Returned Dictionary Structure

`collect_system_info()` always returns a dictionary with exactly these top-level keys:

| Key | Type | Description |
|---|---|---|
| `collector` | `str` | Always `"system_info"` — identifies which collector produced this payload. |
| `status` | `str` | `"success"` on Linux, or `"unsupported_platform"` on any other OS. |
| `timestamp` | `str` | UTC timestamp of the collection, ISO 8601 format (e.g. `2026-07-24T12:00:00+00:00`), from `datetime.now(timezone.utc).isoformat()`. |
| `platform` | `str` | The detected OS name from `platform.system()` (e.g. `"Linux"`, `"Windows"`, `"Darwin"`). |
| `data` | `dict` | The metrics described in [Returned Metrics](#returned-metrics). Empty (`{}`) when `status` is `"unsupported_platform"`. |
| `errors` | `list[str]` | Human-readable messages for any field that could not be determined. Empty when everything was collected successfully. |

## Error Handling

**Unsupported platform.** Before collecting anything, the collector checks `platform.system()`. If it is not `"Linux"`, collection is skipped entirely and it returns:

```python
{
    "collector": "system_info",
    "status": "unsupported_platform",
    "platform": "Windows",
    "data": {},
    "errors": ["Linux Insight Agent supports Linux only."],
}
```

**Per-field degradation.** On a supported (Linux) host, each field is collected independently. If an individual source raises an exception or returns an empty value, that field falls back to `"Unknown"` and a descriptive message is appended to `errors` — one failing field never prevents the rest of the dictionary from being returned. This applies to:

- Any `platform`/`socket`/`os` call that raises `OSError`, `RuntimeError`, or `ValueError`.
- `processor_name`, if neither `platform.processor()` nor `/proc/cpuinfo`'s `model name` field yields a value (tried in that order).
- `distribution_name` / `distribution_version`, if `/etc/os-release` is missing, unreadable, or lacks the relevant fields.

In all of these cases `status` remains `"success"` — `errors` is additive context, not a failure signal on its own.

## Example Output

```python
{
    "collector": "system_info",
    "status": "success",
    "timestamp": "2026-07-24T07:44:10.147935+00:00",
    "platform": "Linux",
    "data": {
        "hostname": "alphaSenate",
        "operating_system": "Linux",
        "distribution_name": "Ubuntu",
        "distribution_version": "26.04",
        "kernel_version": "7.0.0-28-generic",
        "machine_architecture": "x86_64",
        "cpu_architecture": "64bit",
        "python_version": "3.14.4",
        "platform_string": "Linux-7.0.0-28-generic-x86_64-with-glibc2.43",
        "processor_name": "Intel(R) Core(TM) i7-14650HX"
    },
    "errors": []
}
```
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
- Add unit tests covering the `"unsupported_platform"` path and the per-field `"Unknown"` fallback paths (mocked `platform`/`socket`/`os` calls and a missing `/proc/cpuinfo` / `/etc/os-release`).
- Add unit tests with mocked `platform`/`socket` calls to cover the `"unknown"` fallback path.
