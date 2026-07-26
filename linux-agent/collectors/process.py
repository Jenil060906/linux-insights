"""Process collector.

Collects a snapshot of currently running processes and their resource
usage for the current machine — per-process identity, resource usage,
and status, plus an overall running-process summary. This collector
is Linux-only: on any other operating system,
``collect_process_info()`` returns an ``"unsupported_platform"``
response instead of attempting to collect data.

Uses ``psutil`` for process enumeration and per-process data, exposed
directly through Linux's ``/proc`` filesystem under the hood — no
shell commands or subprocesses are invoked (no ``ps``, ``top``,
``htop``, ``pidof``, ``pgrep``, or any ``subprocess`` call). A process
that has exited, is a zombie, or is inaccessible
(``psutil.NoSuchProcess`` / ``psutil.AccessDenied`` /
``psutil.ZombieProcess``) is skipped without being treated as a
failure, since that's routine during a live process scan; any other,
genuinely unexpected error while reading a process is recorded in
"errors" instead of stopping collection. Fully self-contained: no
printing, logging, scheduling, threading, or network/API calls.
"""

import platform
from datetime import datetime, timezone
from typing import Dict, List, Optional

import psutil

_COLLECTOR_NAME = "process"
_TOP_PROCESS_LIMIT = 50
_CPU_PERCENT_SAMPLE_SECONDS = 0.1

_COUNTED_STATUSES = (
    psutil.STATUS_RUNNING,
    psutil.STATUS_SLEEPING,
    psutil.STATUS_STOPPED,
    psutil.STATUS_ZOMBIE,
)


def collect_process_info() -> Dict[str, object]:
    """Collect a running-process snapshot for the current host.

    Linux-only: if the host operating system is not Linux, an
    ``"unsupported_platform"`` response is returned instead of
    attempting collection.

    Returns:
        On Linux, a dictionary shaped like::

            {
                "collector": "process",
                "status": "success",
                "timestamp": "2026-07-26T12:00:00+00:00",
                "platform": "Linux",
                "data": {
                    "processes": [
                        {
                            "pid": 1234,
                            "parent_pid": 1,
                            "process_name": "python3",
                            "executable_path": "/usr/bin/python3.14",
                            "username": "jenil",
                            "status": "running",
                            "creation_time": "2026-07-26T07:00:00+00:00",
                            "cpu_usage_percent": 12.5,
                            "memory_usage_percent": 1.3,
                            "resident_set_size_bytes": 41943040,
                            "virtual_memory_size_bytes": 205520896,
                            "num_threads": 4,
                            "nice_value": 0,
                            "open_file_descriptors": 12,
                        },
                        ...
                    ],
                    "total_running_processes": 214,
                    "running": 2,
                    "sleeping": 205,
                    "stopped": 0,
                    "zombie": 0,
                },
                "errors": [],
            }

        Only the top 50 processes by CPU usage percentage (highest
        first) are included in "processes"; "total_running_processes"
        and the status counts still reflect every process seen during
        the scan, not just the top 50.

        On any non-Linux platform::

            {
                "collector": "process",
                "status": "unsupported_platform",
                "platform": "...",
                "data": {},
                "errors": ["Linux Insight Agent supports Linux only."],
            }

        If an individual process cannot be read because it has
        exited, is a zombie, or is inaccessible, it is silently
        omitted (not an error — this is routine during a live scan).
        If reading a process fails for any other, unexpected reason,
        it is likewise omitted but a message describing the failure
        is appended to "errors" — collection continues with the
        remaining processes rather than failing outright.
    """
    current_platform = platform.system()
    if current_platform != "Linux":
        return {
            "collector": _COLLECTOR_NAME,
            "status": "unsupported_platform",
            "platform": current_platform,
            "data": {},
            "errors": ["Linux Insight Agent supports Linux only."],
        }

    errors: List[str] = []
    processes = _list_processes(errors)

    # `Process.cpu_percent(interval=None)` always returns 0.0 on the
    # first call for a given Process object, since it has no prior
    # CPU-times sample to compare against. Prime every process once
    # (discarding the result) to establish that baseline, then take a
    # single short, shared pause — via psutil's own blocking
    # `cpu_percent(interval=...)`, so no extra sleep primitive needs
    # to be imported — before reading real values below.
    _prime_cpu_percent(processes)
    psutil.cpu_percent(interval=_CPU_PERCENT_SAMPLE_SECONDS)

    entries: List[Dict[str, object]] = []
    status_counts: Dict[str, int] = {status: 0 for status in _COUNTED_STATUSES}

    for proc in processes:
        entry = _read_process(proc, errors)
        if entry is None:
            continue
        entries.append(entry)
        if entry["status"] in status_counts:
            status_counts[entry["status"]] += 1

    entries.sort(key=lambda entry: entry["cpu_usage_percent"], reverse=True)

    data = {
        "processes": entries[:_TOP_PROCESS_LIMIT],
        "total_running_processes": len(entries),
        "running": status_counts[psutil.STATUS_RUNNING],
        "sleeping": status_counts[psutil.STATUS_SLEEPING],
        "stopped": status_counts[psutil.STATUS_STOPPED],
        "zombie": status_counts[psutil.STATUS_ZOMBIE],
    }

    return {
        "collector": _COLLECTOR_NAME,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": current_platform,
        "data": data,
        "errors": errors,
    }


def _list_processes(errors: List[str]) -> List[psutil.Process]:
    """Enumerate currently running processes via ``psutil.process_iter()``.

    Args:
        errors: Shared list that a failure message is appended to if
            processes cannot be enumerated at all.

    Returns:
        A list of ``psutil.Process`` objects, or an empty list on
        failure.
    """
    try:
        return list(psutil.process_iter())
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to enumerate running processes: {error}")
        return []


def _prime_cpu_percent(processes: List[psutil.Process]) -> None:
    """Prime each process's CPU-percent baseline for accurate sampling.

    Args:
        processes: The processes to prime. Any process that has
            already exited or is inaccessible at this point is
            silently skipped — it will simply be skipped again (and
            handled the same way) in the real read pass.
    """
    for proc in processes:
        try:
            proc.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def _read_process(
    proc: psutil.Process, errors: List[str]
) -> Optional[Dict[str, object]]:
    """Read one process's full data entry.

    Core fields are read together under a single ``oneshot()`` cache.
    If the process has exited or is inaccessible while reading any of
    them, it is skipped without recording an error, since that's a
    routine, expected condition during a live scan — not a failure.
    Any other, unexpected exception is recorded in ``errors`` and the
    process is likewise skipped, so one bad process never stops
    collection.

    ``executable_path`` and ``open_file_descriptors`` are read
    individually and degrade to "Unknown" on their own if
    inaccessible, without affecting the rest of the entry.

    Args:
        proc: The process to read.
        errors: Shared list that a failure message is appended to if
            reading this process fails unexpectedly.

    Returns:
        A dictionary describing the process, or ``None`` if it can't
        be read at all.
    """
    try:
        with proc.oneshot():
            memory_info = proc.memory_info()
            return {
                "pid": proc.pid,
                "parent_pid": proc.ppid(),
                "process_name": proc.name(),
                "executable_path": _get_executable_path(proc),
                "username": proc.username(),
                "status": proc.status(),
                "creation_time": datetime.fromtimestamp(
                    proc.create_time(), tz=timezone.utc
                ).isoformat(),
                "cpu_usage_percent": proc.cpu_percent(None),
                "memory_usage_percent": proc.memory_percent(),
                "resident_set_size_bytes": memory_info.rss,
                "virtual_memory_size_bytes": memory_info.vms,
                "num_threads": proc.num_threads(),
                "nice_value": proc.nice(),
                "open_file_descriptors": _get_open_file_descriptors(proc),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None
    except Exception as error:  # noqa: BLE001 - must not abort the scan
        errors.append(f"Unable to read process {proc.pid}: {error}")
        return None


def _get_executable_path(proc: psutil.Process) -> str:
    """Read a process's executable path, if accessible.

    Args:
        proc: The process to read.

    Returns:
        The executable path, or "Unknown" if it can't be read
        (commonly ``AccessDenied`` for another user's process).
    """
    try:
        return proc.exe() or "Unknown"
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"


def _get_open_file_descriptors(proc: psutil.Process) -> object:
    """Read a process's open file descriptor count, if accessible.

    Args:
        proc: The process to read.

    Returns:
        The open file descriptor count, or "Unknown" if it can't be
        read (commonly ``AccessDenied`` for another user's process).
    """
    try:
        return proc.num_fds()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "Unknown"
