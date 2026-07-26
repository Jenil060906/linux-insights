# Process Collector

`collectors/process.py` — implemented, Linux-only running-process snapshot collector.

## Overview

The Process Collector gathers a snapshot of currently running processes and their resource usage on the host machine — per-process identity, resource usage, and status, plus an overall running-process summary — as opposed to the system-wide CPU/memory/disk/network metrics covered by the other collectors. It is exposed through a single public function, `collect_process_info()`, which returns a plain `dict` and takes no arguments.

Like the other collectors in this package, it is **Linux-only by design**. Rather than approximating or partially collecting on another operating system, it detects the host OS up front and returns a clearly-flagged `"unsupported_platform"` response if it isn't Linux.

## Responsibilities

`collect_process_info()` is responsible for, and only for:

- Detecting whether the current host operating system is Linux before collecting anything.
- Enumerating every currently running process on the host.
- For each process: PID, parent PID, process name, executable path (if accessible), username, status, creation time, CPU usage percentage, memory usage percentage, resident set size (RSS), virtual memory size (VMS), thread count, nice value, and open file descriptor count (if accessible).
- Sorting processes by CPU usage percentage, highest first, and returning only the top 50 (see [Sorting Strategy](#sorting-strategy)).
- Reporting an overall summary — total running process count and per-status counts (running/sleeping/stopped/zombie) — computed across **every** process seen, not just the top 50 returned.
- Continuing to collect the remaining processes if one process can't be read, recording genuinely unexpected failures in `errors` instead of failing the whole collection.
- Returning everything as one dictionary — no side effects.

It is explicitly **not** responsible for: static host identity, CPU, memory, disk, or network metrics (see the other files in this directory), a parent-child process tree, per-process I/O, GPU usage, container/cgroup context, or scheduling policy (see [Future Enhancements](#future-enhancements)), scheduling repeated sampling, printing/logging output, or sending data anywhere (no network or API calls).

## Linux Dependencies

`psutil` is used exclusively — no `ps`, `top`, `htop`, or any other shell command is invoked, and this collector never imports `subprocess`.

| Reason | Explanation |
|---|---|
| No text parsing | `ps`/`top`/`htop` output is meant for humans, varies across distributions, locales, and tool versions, and would need to be parsed with fragile string/regex logic that can silently break on an update. `psutil` reads the same underlying kernel data (Linux's `/proc/<pid>/*` files) and returns typed values directly. |
| No process-spawn overhead | Shelling out means forking and executing a new process on every collection cycle, for every field. `psutil.process_iter()` and `Process` methods read `/proc` directly in-process, with no extra process creation. |
| No tool-availability dependency | `ps`/`top`/`htop` may not be installed (or may be different implementations, e.g. BusyBox vs. procps) on every monitored host. `psutil` only depends on the kernel's `/proc` interface, which is always present on Linux. |
| Consistent, structured data | `psutil.Process` methods (`pid`, `ppid()`, `name()`, `status()`, `memory_info()`, etc.) return typed Python values (ints, floats, named tuples) instead of columns of text that would need re-parsing into the right types. |

**Linux-specific behavior:**

- `open_file_descriptors` (`Process.num_fds()`) is a Unix-only concept with no meaning on other platforms; combined with the top-level platform gate, it's always safe to call here.
- `AccessDenied` is common and expected on Linux for processes owned by other users (a non-root agent can enumerate PIDs but can't always read another user's `/proc/<pid>/exe`, `fd/`, etc.) — handled explicitly rather than as a fatal condition (see [Error Handling](#error-handling)).
- Process status values (`running`, `sleeping`, `stopped`, `zombie`, and others like `idle`/`disk-sleep` not separately counted here) come directly from the Linux kernel's process state, exposed by `psutil.STATUS_*` constants.

## Returned Metrics

All metrics live under the top-level `data` key of the returned dictionary (see [Returned Dictionary Structure](#returned-dictionary-structure)). Per-process fields apply to each entry in `processes`.

| Metric | Description | Units | Example |
|---|---|---|---|
| `processes[].pid` | Process ID | integer | `9737` |
| `processes[].parent_pid` | Parent process ID | integer | `9724` |
| `processes[].process_name` | Process name | string | `python3` |
| `processes[].executable_path` | Path to the executable, if accessible | string | `/usr/bin/python3.14` |
| `processes[].username` | User the process runs as | string | `jenil` |
| `processes[].status` | Process status | string | `running` |
| `processes[].creation_time` | When the process started | ISO 8601 UTC timestamp | `2026-07-26T08:07:17.160000+00:00` |
| `processes[].cpu_usage_percent` | CPU usage over the sampling window | percent | `24.8` |
| `processes[].memory_usage_percent` | Share of total system memory in use | percent | `0.25` |
| `processes[].resident_set_size_bytes` | Physical memory (RSS) in use | bytes | `16605184` |
| `processes[].virtual_memory_size_bytes` | Virtual memory (VMS) in use | bytes | `22032384` |
| `processes[].num_threads` | Number of threads | integer | `1` |
| `processes[].nice_value` | Scheduling niceness | integer | `0` |
| `processes[].open_file_descriptors` | Open file descriptor count, if accessible | integer | `4` |
| `total_running_processes` | Total number of processes seen (not limited to the top 50) | integer | `274` |
| `running` | Count of processes in the `running` state | integer | `1` |
| `sleeping` | Count of processes in the `sleeping` state | integer | `192` |
| `stopped` | Count of processes in the `stopped` state | integer | `0` |
| `zombie` | Count of processes in the `zombie` state | integer | `1` |

## Sorting Strategy

`processes` is sorted by `cpu_usage_percent`, highest first. CPU usage is the single most common signal for "what's actually happening on this host right now" — for an observability agent, the processes consuming the most CPU are almost always the most relevant ones to surface first, whether investigating load or looking for a runaway process.

Only the **top 50** are returned in `processes`. A busy host can have hundreds of processes; returning all of them on every collection cycle would make the payload large and mostly uninteresting, since a long tail of near-idle processes rarely matters for observability. Fifty is enough to see everything relevant at a glance without unbounded payload growth. `total_running_processes` and the status counts (`running`/`sleeping`/`stopped`/`zombie`) are computed across **every** process seen, before the top-50 slice, so the summary still accurately reflects the whole host even though the detailed list is capped.

## Returned Dictionary Structure

`collect_process_info()` always returns a dictionary with exactly these top-level keys:

| Key | Type | Description |
|---|---|---|
| `collector` | `str` | Always `"process"` — identifies which collector produced this payload. |
| `status` | `str` | `"success"` on Linux, or `"unsupported_platform"` on any other OS. |
| `timestamp` | `str` | UTC timestamp of the collection, ISO 8601 format (e.g. `2026-07-26T12:00:00+00:00`), from `datetime.now(timezone.utc).isoformat()`. |
| `platform` | `str` | The detected OS name from `platform.system()` (e.g. `"Linux"`, `"Windows"`, `"Darwin"`). |
| `data` | `dict` | The metrics described in [Returned Metrics](#returned-metrics). Empty (`{}`) when `status` is `"unsupported_platform"`. |
| `errors` | `list[str]` | Human-readable messages for any process that failed to read for an unexpected reason. Empty when everything was collected as expected. |

## Error Handling

**Unsupported platform.** Before collecting anything, the collector checks `platform.system()`. If it is not `"Linux"`, collection is skipped entirely and it returns:

```python
{
    "collector": "process",
    "status": "unsupported_platform",
    "platform": "Windows",
    "data": {},
    "errors": ["Linux Insight Agent supports Linux only."],
}
```

**`AccessDenied`, `ZombieProcess`, `NoSuchProcess`.** These three `psutil` exceptions are treated as routine, expected conditions during a live process scan, not failures:

- `NoSuchProcess` — the process exited between being listed and being read (a normal race on a live system).
- `AccessDenied` — the process is owned by another user and the agent doesn't have permission to read some or all of its data (expected when not running as root).
- `ZombieProcess` — the process has exited but its entry hasn't been reaped by its parent yet, so most of its data is no longer readable.

When any of these three occur while reading a process's **core** fields (PID, name, status, memory, etc.), that process is skipped entirely — silently, with **no entry added to `errors`**. When either `AccessDenied` or `NoSuchProcess`/`ZombieProcess` occurs while reading specifically `executable_path` or `open_file_descriptors` (the two fields marked "if accessible"), only that one field falls back to `"Unknown"` — the rest of the process's entry is still included.

**Partial failures.** If reading a process fails for any other, genuinely unexpected reason, that process is skipped and a message identifying its PID is appended to `errors` — collection continues with the remaining processes rather than aborting.

In every case, `status` remains `"success"` on a supported platform — `errors` is reserved for genuinely unexpected failures, not the routine skips described above.

## Example Output

```python
{
    "collector": "process",
    "status": "success",
    "timestamp": "2026-07-26T08:07:20.331000+00:00",
    "platform": "Linux",
    "data": {
        "processes": [
            {
                "pid": 9737,
                "parent_pid": 9724,
                "process_name": "python3",
                "executable_path": "/usr/bin/python3.14",
                "username": "jenil",
                "status": "running",
                "creation_time": "2026-07-26T08:07:17.160000+00:00",
                "cpu_usage_percent": 24.8,
                "memory_usage_percent": 0.2533705660150947,
                "resident_set_size_bytes": 16605184,
                "virtual_memory_size_bytes": 22032384,
                "num_threads": 1,
                "nice_value": 0,
                "open_file_descriptors": 4
            },
            {
                "pid": 6668,
                "parent_pid": 6189,
                "process_name": "code",
                "executable_path": "/snap/code/252/usr/share/code/code",
                "username": "jenil",
                "status": "sleeping",
                "creation_time": "2026-07-26T07:51:26.290000+00:00",
                "cpu_usage_percent": 12.7,
                "memory_usage_percent": 4.7227298522275865,
                "resident_set_size_bytes": 309514240,
                "virtual_memory_size_bytes": 1554806878208,
                "num_threads": 10,
                "nice_value": 0,
                "open_file_descriptors": 36
            }
        ],
        "total_running_processes": 274,
        "running": 1,
        "sleeping": 192,
        "stopped": 0,
        "zombie": 1
    },
    "errors": []
}
```

## Future Enhancements

- Parent-child process tree, building hierarchy from each process's `parent_pid` rather than a flat list.
- Per-process I/O statistics (bytes/operations read and written), where the kernel and permissions allow it.
- GPU usage per process, for hosts with GPU workloads.
- Container detection — identifying which container (if any) a process belongs to.
- Cgroup information — resource limits/usage from the process's cgroup.
- Scheduling policy (e.g. `SCHED_OTHER`, `SCHED_FIFO`, `SCHED_RR`), beyond the nice value already collected.
