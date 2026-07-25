"""Disk collector.

Collects filesystem and storage information for the current
machine — per-partition device/mount/filesystem details, space usage,
and read-only/read-write status, plus the total number of mounted
partitions and root filesystem usage. This collector is Linux-only:
on any other operating system, ``collect_disk_info()`` returns an
``"unsupported_platform"`` response instead of attempting to collect
data.

Uses ``psutil`` for partition enumeration and space usage (which
already surfaces everything this collector needs on Linux, so no
Linux files are read directly). The filesystem type of every mounted
partition is checked before any usage is read: known Linux virtual/
pseudo-filesystem types (``tmpfs``, ``devtmpfs``, ``squashfs``,
``proc``, ``sysfs``, ``securityfs``, ``debugfs``, ``tracefs``,
``overlay``, ``bpf``, ``pstore``, ``cgroup``, ``cgroup2``,
``configfs``) are skipped entirely — silently, with no entry in
"errors" — since they are expected, not a collection failure. Real
storage filesystems (``ext4``, ``xfs``, ``btrfs``, ``zfs``, ``f2fs``,
``ntfs``, ``exfat``, ``vfat``, and any other type not in the
pseudo-filesystem set) are always collected; an "errors" entry is only
recorded if one of those is unexpectedly inaccessible. Fully
self-contained: no printing, logging, scheduling, threading, or
network/API calls.
"""

import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import psutil

_COLLECTOR_NAME = "disk"

# Known Linux virtual/pseudo-filesystem types. These are expected,
# kernel-managed mounts with no meaningful "storage" to report, so
# they are skipped before any usage read is attempted — and a skip is
# never treated as an error. Real storage filesystems (ext4, xfs,
# btrfs, zfs, f2fs, ntfs, exfat, vfat, etc.) are anything not in this
# set, and are always collected.
_IGNORED_FSTYPES = frozenset(
    {
        "tmpfs",
        "devtmpfs",
        "squashfs",
        "proc",
        "sysfs",
        "securityfs",
        "debugfs",
        "tracefs",
        "overlay",
        "bpf",
        "pstore",
        "cgroup",
        "cgroup2",
        "configfs",
    }
)


def collect_disk_info() -> Dict[str, object]:
    """Collect filesystem and storage information for the current host.

    Linux-only: if the host operating system is not Linux, an
    ``"unsupported_platform"`` response is returned instead of
    attempting collection.

    Returns:
        On Linux, a dictionary shaped like::

            {
                "collector": "disk",
                "status": "success",
                "timestamp": "2026-07-24T12:00:00+00:00",
                "platform": "Linux",
                "data": {
                    "partitions": [
                        {
                            "device": "/dev/sda1",
                            "mount_point": "/",
                            "filesystem_type": "ext4",
                            "mount_options": ["rw", "relatime"],
                            "total_bytes": 255000000000,
                            "used_bytes": 120000000000,
                            "free_bytes": 135000000000,
                            "usage_percent": 47.1,
                            "read_only": False,
                        },
                        ...
                    ],
                    "total_partitions": 1,
                    "root_filesystem": {
                        "total_bytes": 255000000000,
                        "used_bytes": 120000000000,
                        "free_bytes": 135000000000,
                        "usage_percent": 47.1,
                    },
                },
                "errors": [],
            }

        On any non-Linux platform::

            {
                "collector": "disk",
                "status": "unsupported_platform",
                "platform": "...",
                "data": {},
                "errors": ["Linux Insight Agent supports Linux only."],
            }

        If an individual partition cannot be read, it is omitted from
        "partitions" and a message describing the failure is appended
        to "errors" — collection continues with the remaining
        partitions rather than failing outright.
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
    partitions = _get_partitions(errors)

    data = {
        "partitions": partitions,
        "total_partitions": len(partitions),
        "root_filesystem": _get_root_filesystem_usage(errors),
    }

    return {
        "collector": _COLLECTOR_NAME,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": current_platform,
        "data": data,
        "errors": errors,
    }


def _get_partitions(errors: List[str]) -> List[Dict[str, object]]:
    """Enumerate mounted filesystems and read their usage details.

    Pseudo/virtual filesystem types in ``_IGNORED_FSTYPES`` are
    skipped, since they don't represent meaningful storage. Every
    other mounted filesystem is read independently, so one unreadable
    partition doesn't prevent the rest from being reported.

    Args:
        errors: Shared list that failure messages are appended to.

    Returns:
        A list of per-partition dictionaries (see
        :func:`collect_disk_info` for the shape).
    """
    try:
        raw_partitions = psutil.disk_partitions(all=True)
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to enumerate mounted filesystems: {error}")
        return []

    partitions: List[Dict[str, object]] = []
    for partition in raw_partitions:
        if partition.fstype in _IGNORED_FSTYPES:
            continue

        partition_data = _read_partition(partition, errors)
        if partition_data is not None:
            partitions.append(partition_data)

    return partitions


def _read_partition(partition, errors: List[str]) -> Optional[Dict[str, object]]:
    """Read device, mount, and usage details for one partition.

    Args:
        partition: A ``psutil`` ``sdiskpart`` named tuple (``device``,
            ``mountpoint``, ``fstype``, ``opts``).
        errors: Shared list that a failure message is appended to if
            this partition cannot be read.

    Returns:
        A dictionary describing the partition, or ``None`` if its
        mount point is inaccessible or its usage can't be read.
    """
    mount_point = partition.mountpoint
    mount_path = Path(mount_point)

    if not mount_path.exists() or not os.access(mount_point, os.R_OK):
        errors.append(
            f"Unable to read partition {partition.device} at {mount_point}: "
            "mount point is not accessible."
        )
        return None

    try:
        usage = psutil.disk_usage(mount_point)
    except OSError as error:
        errors.append(
            f"Unable to read partition {partition.device} at {mount_point}: {error}"
        )
        return None

    options = [option for option in partition.opts.split(",") if option]

    return {
        "device": partition.device,
        "mount_point": mount_point,
        "filesystem_type": partition.fstype,
        "mount_options": options,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "usage_percent": usage.percent,
        "read_only": _get_read_only_status(options),
    }


def _get_read_only_status(mount_options: List[str]) -> object:
    """Determine read-only/read-write status from mount options.

    Args:
        mount_options: The partition's parsed mount options (e.g.
            ``["rw", "relatime"]``).

    Returns:
        ``True`` if mounted read-only, ``False`` if mounted
        read-write, or "Unknown" if neither ``"ro"`` nor ``"rw"``
        appears among the mount options.
    """
    if "ro" in mount_options:
        return True
    if "rw" in mount_options:
        return False
    return "Unknown"


def _get_root_filesystem_usage(errors: List[str]) -> Dict[str, object]:
    """Read space usage for the root filesystem (``/``).

    Collected independently of the partition list so root filesystem
    usage is always reported by mount point, regardless of how ``/``
    is represented (or filtered) in the enumerated partition list.

    Args:
        errors: Shared list that a failure message is appended to if
            root filesystem usage cannot be read.

    Returns:
        A dictionary with "total_bytes", "used_bytes", "free_bytes",
        and "usage_percent" keys, each "Unknown" on failure.
    """
    try:
        usage = psutil.disk_usage("/")
    except OSError as error:
        errors.append(f"Unable to read root filesystem usage: {error}")
        return {
            "total_bytes": "Unknown",
            "used_bytes": "Unknown",
            "free_bytes": "Unknown",
            "usage_percent": "Unknown",
        }

    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "usage_percent": usage.percent,
    }
