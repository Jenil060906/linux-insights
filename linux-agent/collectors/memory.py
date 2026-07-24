"""Memory collector.

Collects dynamic RAM and swap metrics for the current machine —
total/available/used/free RAM, RAM usage percentage, Linux-specific
memory breakdown (buffers, cached, shared, slab), swap totals/usage,
and supplementary virtual-memory subsystem statistics (active/inactive
page counts, swap-in/swap-out activity). This collector is Linux-only:
on any other operating system, ``collect_memory_info()`` returns an
``"unsupported_platform"`` response instead of attempting to collect
data.

Uses ``psutil`` for every metric it already exposes reliably on
Linux — which is nearly all of them, since ``psutil.virtual_memory()``
and ``psutil.swap_memory()`` already parse ``/proc/meminfo``
internally. The one exception is Slab memory: if the running
``psutil`` doesn't expose it as an attribute, ``/proc/meminfo`` is
read directly (via ``pathlib``) as a fallback. All values are reported
in bytes; no unit conversion happens inside this collector. Fully
self-contained: no printing, logging, scheduling, threading, or
network/API calls.
"""

import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import psutil

_COLLECTOR_NAME = "memory"
_MEMINFO_PATH = Path("/proc/meminfo")


def collect_memory_info() -> Dict[str, object]:
    """Collect dynamic RAM and swap metrics for the current host.

    Linux-only: if the host operating system is not Linux, an
    ``"unsupported_platform"`` response is returned instead of
    attempting collection.

    Returns:
        On Linux, a dictionary shaped like::

            {
                "collector": "memory",
                "status": "success",
                "timestamp": "2026-07-24T12:00:00+00:00",
                "platform": "Linux",
                "data": {
                    "total_ram_bytes": 6553714688,
                    "available_ram_bytes": 2469048320,
                    "used_ram_bytes": 4084666368,
                    "free_ram_bytes": 192544768,
                    "ram_usage_percent": 62.3,
                    "buffers_bytes": 33882112,
                    "cached_bytes": 2287443968,
                    "shared_bytes": 125292544,
                    "slab_bytes": 244133888,
                    "total_swap_bytes": 4294963200,
                    "used_swap_bytes": 531578880,
                    "free_swap_bytes": 3763384320,
                    "swap_usage_percent": 12.4,
                    "virtual_memory_stats": {
                        "active_bytes": 2553110528,
                        "inactive_bytes": 3362955264,
                        "swap_in_bytes": 114163712,
                        "swap_out_bytes": 578777088,
                    },
                },
                "errors": [],
            }

        On any non-Linux platform::

            {
                "collector": "memory",
                "status": "unsupported_platform",
                "platform": "...",
                "data": {},
                "errors": ["Linux Insight Agent supports Linux only."],
            }

        A metric that cannot be individually determined is set to
        "Unknown" and a corresponding message is appended to
        "errors", rather than the whole collection failing.
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
    virtual_memory = _get_virtual_memory(errors)
    swap_memory = _get_swap_memory(errors)

    data = {
        "total_ram_bytes": _get_attr(virtual_memory, "total", "total RAM", errors),
        "available_ram_bytes": _get_attr(
            virtual_memory, "available", "available RAM", errors
        ),
        "used_ram_bytes": _get_attr(virtual_memory, "used", "used RAM", errors),
        "free_ram_bytes": _get_attr(virtual_memory, "free", "free RAM", errors),
        "ram_usage_percent": _get_attr(
            virtual_memory, "percent", "RAM usage percentage", errors
        ),
        "buffers_bytes": _get_attr(virtual_memory, "buffers", "buffers", errors),
        "cached_bytes": _get_attr(virtual_memory, "cached", "cached memory", errors),
        "shared_bytes": _get_attr(virtual_memory, "shared", "shared memory", errors),
        "slab_bytes": _get_slab_bytes(virtual_memory, errors),
        "total_swap_bytes": _get_attr(swap_memory, "total", "total swap", errors),
        "used_swap_bytes": _get_attr(swap_memory, "used", "used swap", errors),
        "free_swap_bytes": _get_attr(swap_memory, "free", "free swap", errors),
        "swap_usage_percent": _get_attr(
            swap_memory, "percent", "swap usage percentage", errors
        ),
        "virtual_memory_stats": _get_virtual_memory_stats(
            virtual_memory, swap_memory, errors
        ),
    }

    return {
        "collector": _COLLECTOR_NAME,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": current_platform,
        "data": data,
        "errors": errors,
    }


def _get_virtual_memory(errors: List[str]) -> Optional[object]:
    """Sample virtual memory statistics via ``psutil.virtual_memory()``.

    Args:
        errors: Shared list that a failure message is appended to if
            virtual memory statistics cannot be sampled at all.

    Returns:
        The ``psutil`` ``svmem`` named tuple, or ``None`` on failure.
    """
    try:
        return psutil.virtual_memory()
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to determine virtual memory statistics: {error}")
        return None


def _get_swap_memory(errors: List[str]) -> Optional[object]:
    """Sample swap memory statistics via ``psutil.swap_memory()``.

    Args:
        errors: Shared list that a failure message is appended to if
            swap memory statistics cannot be sampled at all.

    Returns:
        The ``psutil`` ``sswap`` named tuple, or ``None`` on failure.
    """
    try:
        return psutil.swap_memory()
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to determine swap memory statistics: {error}")
        return None


def _get_attr(
    source: Optional[object], attr_name: str, field_name: str, errors: List[str]
) -> object:
    """Read one attribute off a ``psutil`` named tuple, guarding failure.

    Args:
        source: The ``psutil`` named tuple to read from (``None`` if
            sampling it already failed upstream).
        attr_name: Name of the attribute to read.
        field_name: Human-readable name of the field, used in the
            error message if the attribute is missing.
        errors: Shared list that a failure message is appended to.

    Returns:
        The attribute's value, or "Unknown" if ``source`` is ``None``
        or the attribute is missing.
    """
    if source is None:
        return "Unknown"
    value = getattr(source, attr_name, None)
    if value is None:
        errors.append(f"Unable to determine {field_name}.")
        return "Unknown"
    return value


def _get_slab_bytes(source: Optional[object], errors: List[str]) -> object:
    """Determine Slab memory in bytes, with a ``/proc/meminfo`` fallback.

    ``psutil.virtual_memory()`` exposes ``slab`` on Linux, but the
    attribute is not guaranteed to exist on every ``psutil`` version.
    If it's missing, fall back to parsing the "Slab:" field directly
    out of ``/proc/meminfo`` (reported there in kB, converted here to
    bytes) — this is the one case in this collector where a Linux file
    is read directly, since it's the one metric ``psutil`` might not
    provide.

    Args:
        source: The ``psutil`` ``svmem`` named tuple (``None`` if
            sampling it already failed upstream).
        errors: Shared list that a failure message is appended to if
            neither source yields a value.

    Returns:
        Slab memory in bytes, or "Unknown" if unavailable from both
        ``psutil`` and ``/proc/meminfo``.
    """
    if source is not None:
        slab = getattr(source, "slab", None)
        if slab is not None:
            return slab

    slab_from_proc = _read_meminfo_field_bytes("Slab")
    if slab_from_proc is not None:
        return slab_from_proc

    errors.append("Unable to determine slab memory from psutil or /proc/meminfo.")
    return "Unknown"


def _read_meminfo_field_bytes(field_name: str) -> Optional[int]:
    """Read a single field from ``/proc/meminfo``, converting kB to bytes.

    Args:
        field_name: The ``/proc/meminfo`` field label to look for
            (e.g. ``"Slab"``), without the trailing colon.

    Returns:
        The field's value in bytes, or ``None`` if the file is
        missing, unreadable, or has no such field.
    """
    if not _MEMINFO_PATH.is_file():
        return None
    try:
        contents = _MEMINFO_PATH.read_text(encoding="utf-8")
    except OSError:
        return None

    prefix = f"{field_name}:"
    for line in contents.splitlines():
        if line.startswith(prefix):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1]) * 1024
    return None


def _get_virtual_memory_stats(
    virtual_memory: Optional[object],
    swap_memory: Optional[object],
    errors: List[str],
) -> Dict[str, object]:
    """Collect supplementary virtual-memory subsystem statistics.

    Groups the fields that fall outside the primary RAM/swap summary
    — active/inactive page counts and swap-in/swap-out activity —
    under one nested dictionary.

    Args:
        virtual_memory: The ``psutil`` ``svmem`` named tuple (``None``
            if sampling it already failed upstream).
        swap_memory: The ``psutil`` ``sswap`` named tuple (``None`` if
            sampling it already failed upstream).
        errors: Shared list that failure messages are appended to.

    Returns:
        A dictionary with "active_bytes", "inactive_bytes",
        "swap_in_bytes", and "swap_out_bytes" keys.
    """
    return {
        "active_bytes": _get_attr(virtual_memory, "active", "active memory", errors),
        "inactive_bytes": _get_attr(
            virtual_memory, "inactive", "inactive memory", errors
        ),
        "swap_in_bytes": _get_attr(swap_memory, "sin", "swap-in activity", errors),
        "swap_out_bytes": _get_attr(
            swap_memory, "sout", "swap-out activity", errors
        ),
    }
