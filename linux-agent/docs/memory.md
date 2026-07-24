# Memory Collector

`collectors/memory.py` — implemented, Linux-only dynamic RAM and swap metrics collector.

## Overview

The Memory Collector gathers dynamic, point-in-time RAM and swap metrics for the host machine — usage totals, Linux-specific memory breakdown, and virtual-memory subsystem activity — as opposed to the static identity facts covered by the [System Information Collector](system-info.md) or the utilization metrics covered by the [CPU Collector](cpu.md). It is exposed through a single public function, `collect_memory_info()`, which returns a plain `dict` and takes no arguments.

Like the other collectors in this package, it is **Linux-only by design**. Rather than approximating or partially collecting on another operating system, it detects the host OS up front and returns a clearly-flagged `"unsupported_platform"` response if it isn't Linux.

## Responsibilities

`collect_memory_info()` is responsible for, and only for:

- Detecting whether the current host operating system is Linux before collecting anything.
- Collecting RAM totals: total, available, used, free, and usage percentage.
- Collecting the Linux-specific memory breakdown: buffers, cached, shared, and slab memory.
- Collecting swap totals: total, used, free, and usage percentage.
- Collecting supplementary virtual-memory subsystem statistics: active/inactive page counts and swap-in/swap-out activity.
- Reporting every value in bytes — no unit conversion happens inside the collector.
- Degrading a single unavailable metric to `"Unknown"` (recording why in `errors`) instead of letting one missing value fail the whole collection.
- Returning everything as one dictionary — no side effects.

It is explicitly **not** responsible for: static host identity or CPU utilization (see [`system-info.md`](system-info.md) and [`cpu.md`](cpu.md)), unit conversion (e.g. to MB/GB — that's a display-layer concern), scheduling repeated sampling, printing/logging output, or sending data anywhere (no network or API calls).

## Linux Dependencies

| Module / Resource | Used for | Why |
|---|---|---|
| `psutil.virtual_memory()` | Total/available/used/free RAM, RAM usage percentage, buffers, cached, shared memory, and (usually) slab memory. | On Linux, `psutil` already parses `/proc/meminfo` internally and exposes the Linux-specific fields (`buffers`, `cached`, `shared`, `slab`) directly as attributes — so the collector gets them "for free" without needing to parse the file itself. |
| `psutil.swap_memory()` | Total/used/free swap, swap usage percentage, and swap-in/swap-out activity. | Same reasoning as above — the swap equivalent of `virtual_memory()`, already Linux-aware. |
| `/proc/meminfo` | Fallback source for Slab memory (`Slab:` field) if the running `psutil` version doesn't expose `slab` as an attribute. Read via `pathlib.Path`, and only opened if the fallback is actually needed. | `slab` isn't guaranteed to exist as a `psutil` attribute on every version, so a direct read of the same underlying Linux file `psutil` itself parses is used as a last resort, converting the reported kB value to bytes. |
| `platform.system()` | The Linux-only gate at the top of `collect_memory_info()`. | Determines whether to proceed with collection at all. |

> **Note:** `/proc/meminfo` is the only Linux file read directly by this collector, and only for the Slab-memory fallback — every other metric comes from `psutil`, which is itself already reading `/proc/meminfo` under the hood on Linux.

## Returned Metrics

All metrics live under the top-level `data` key of the returned dictionary (see [Returned Dictionary Structure](#returned-dictionary-structure)). `virtual_memory_stats` is a nested `dict`; its four fields are listed individually below.

| Metric | Description | Units | Example |
|---|---|---|---|
| `total_ram_bytes` | Total physical RAM installed | bytes | `6553714688` |
| `available_ram_bytes` | RAM available for new allocations without swapping | bytes | `2469048320` |
| `used_ram_bytes` | RAM currently in use | bytes | `4084666368` |
| `free_ram_bytes` | RAM not currently in use | bytes | `192544768` |
| `ram_usage_percent` | RAM usage as a percentage of total | percent | `62.3` |
| `buffers_bytes` | Memory used for kernel I/O buffers | bytes | `33882112` |
| `cached_bytes` | Memory used for the page cache | bytes | `2287443968` |
| `shared_bytes` | Memory shared between processes (e.g. `tmpfs`) | bytes | `125292544` |
| `slab_bytes` | Kernel slab allocator memory (see Error Handling for the fallback order) | bytes | `244133888` |
| `total_swap_bytes` | Total configured swap space | bytes | `4294963200` |
| `used_swap_bytes` | Swap space currently in use | bytes | `531578880` |
| `free_swap_bytes` | Swap space not currently in use | bytes | `3763384320` |
| `swap_usage_percent` | Swap usage as a percentage of total | percent | `12.4` |
| `virtual_memory_stats.active_bytes` | Memory on the active LRU list (recently used) | bytes | `2553110528` |
| `virtual_memory_stats.inactive_bytes` | Memory on the inactive LRU list (reclaim candidates) | bytes | `3362955264` |
| `virtual_memory_stats.swap_in_bytes` | Cumulative memory swapped in since boot | bytes | `114163712` |
| `virtual_memory_stats.swap_out_bytes` | Cumulative memory swapped out since boot | bytes | `578777088` |

## Returned Dictionary Structure

`collect_memory_info()` always returns a dictionary with exactly these top-level keys:

| Key | Type | Description |
|---|---|---|
| `collector` | `str` | Always `"memory"` — identifies which collector produced this payload. |
| `status` | `str` | `"success"` on Linux, or `"unsupported_platform"` on any other OS. |
| `timestamp` | `str` | UTC timestamp of the collection, ISO 8601 format (e.g. `2026-07-24T08:55:02.282857+00:00`), from `datetime.now(timezone.utc).isoformat()`. |
| `platform` | `str` | The detected OS name from `platform.system()` (e.g. `"Linux"`, `"Windows"`, `"Darwin"`). |
| `data` | `dict` | The metrics described in [Returned Metrics](#returned-metrics). Empty (`{}`) when `status` is `"unsupported_platform"`. |
| `errors` | `list[str]` | Human-readable messages for any metric that could not be determined. Empty when everything was collected successfully. |

## Error Handling

**Unsupported platform.** Before collecting anything, the collector checks `platform.system()`. If it is not `"Linux"`, collection is skipped entirely and it returns:

```python
{
    "collector": "memory",
    "status": "unsupported_platform",
    "platform": "Darwin",
    "data": {},
    "errors": ["Linux Insight Agent supports Linux only."],
}
```

**Unavailable metric handling.** On a supported (Linux) host, `psutil.virtual_memory()` and `psutil.swap_memory()` are each sampled once and reused across the metrics derived from them. If a metric's underlying attribute is missing, it individually falls back to `"Unknown"` and a descriptive message is appended to `errors`, without affecting any other metric. `slab_bytes` specifically has a two-step fallback: `psutil`'s `slab` attribute first, then `/proc/meminfo`'s `Slab:` field, then `"Unknown"` only if both fail.

**Graceful exception handling.** If `psutil.virtual_memory()` or `psutil.swap_memory()` itself raises (`OSError`/`RuntimeError`), a single root-cause message is appended to `errors` and every metric that would have been derived from that call falls back to `"Unknown"` — the collector does not attempt to re-derive each dependent metric individually or crash. In every case `status` remains `"success"`: `errors` is additive context, not a failure signal on its own.

## Example Output

```python
{
    "collector": "memory",
    "status": "success",
    "timestamp": "2026-07-24T08:55:02.282857+00:00",
    "platform": "Linux",
    "data": {
        "total_ram_bytes": 6553714688,
        "available_ram_bytes": 2520035328,
        "used_ram_bytes": 4033679360,
        "free_ram_bytes": 280698880,
        "ram_usage_percent": 61.5,
        "buffers_bytes": 31158272,
        "cached_bytes": 2254200832,
        "shared_bytes": 126894080,
        "slab_bytes": 243228672,
        "total_swap_bytes": 4294963200,
        "used_swap_bytes": 624590848,
        "free_swap_bytes": 3670372352,
        "swap_usage_percent": 14.5,
        "virtual_memory_stats": {
            "active_bytes": 2693476352,
            "inactive_bytes": 3178565632,
            "swap_in_bytes": 114348032,
            "swap_out_bytes": 667394048
        }
    },
    "errors": []
}
```

## Future Enhancements

- HugePages statistics (total/free/reserved huge pages), from `/proc/meminfo`'s `HugePages_*` fields.
- Transparent Huge Pages (THP) status, from `/sys/kernel/mm/transparent_hugepage/enabled`.
- NUMA-aware memory breakdown (per-node totals), from `/sys/devices/system/node/node*/meminfo` on multi-node hosts.
- Memory pressure metrics (PSI — Pressure Stall Information), from `/proc/pressure/memory` on kernels that expose it.
- OOM (out-of-memory) statistics — recent OOM-kill events and counts, from the kernel log or `/proc/vmstat`'s `oom_kill` counter.
