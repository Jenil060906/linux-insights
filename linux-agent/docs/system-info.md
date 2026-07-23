# System Information Collector

`collectors/system_info.py` — static host identity information.

> **Status:** Design documented here ahead of/alongside implementation. Check `collectors/system_info.py` in the branch you're working from for the current code state.

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
| `processor` | Processor model name, if available (see fallback strategy below) |
| `platform` | Full platform identification string |
| `python_version` | Version of the running Python interpreter |

Any value that can't be determined falls back to `"unknown"` rather than raising, so one missing field never blocks the rest of the collection.

## Python Modules Used

- `platform` — OS, kernel, architecture, processor, platform string, Python version.
- `socket` — hostname.
- `/proc/cpuinfo` (read directly, no extra import) — Linux-specific fallback for `processor`.

Standard library only — no third-party dependencies (e.g. no `psutil`).

## Processor Fallback Strategy

On most Linux distributions, `platform.processor()` doesn't return a real CPU model — it reflects `uname -p`, which the kernel/libc typically leaves empty (surfaced as `""` or `"unknown"`/`"Unknown"`). To still report a meaningful value:

1. Try `platform.processor()` first.
2. If it's empty or `"unknown"`/`"Unknown"`, parse the `model name` field out of `/proc/cpuinfo`, which the kernel always populates on x86/x86_64.
3. Return that model name if found.
4. If both methods fail, return `"unknown"`.

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

## Future Enhancements

- Add uptime / boot time.
- Detect virtualization/container context (bare metal vs. VM vs. container).
- Cache the result for the agent's lifetime, since this data is static per run.
- Add unit tests with mocked `platform`/`socket` calls to cover the `"unknown"` fallback path.
