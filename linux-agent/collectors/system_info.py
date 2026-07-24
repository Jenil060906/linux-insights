"""System info collector.

Collects static host identity information for the current machine —
hostname, OS/distribution identity, kernel version, architecture,
processor name, and Python runtime details. This collector is
Linux-only: on any other operating system, ``collect_system_info()``
returns an ``"unsupported_platform"`` response instead of attempting
to collect data.

Relies only on the standard library (``platform``, ``socket``, ``os``,
``pathlib``, ``datetime``) so this collector has no third-party
dependencies and is fully self-contained: no printing, logging,
scheduling, threading, or network/API calls.
"""

import os
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

_COLLECTOR_NAME = "system_info"
_OS_RELEASE_PATH = Path("/etc/os-release")
_CPUINFO_PATH = Path("/proc/cpuinfo")


def collect_system_info() -> Dict[str, object]:
    """Collect static system identity information for the current host.

    Linux-only: if the host operating system is not Linux, an
    ``"unsupported_platform"`` response is returned instead of
    attempting collection.

    Returns:
        On Linux, a dictionary shaped like::

            {
                "collector": "system_info",
                "status": "success",
                "timestamp": "2026-07-24T12:00:00+00:00",
                "platform": "Linux",
                "data": {
                    "hostname": "...",
                    "operating_system": "...",
                    "distribution_name": "...",
                    "distribution_version": "...",
                    "kernel_version": "...",
                    "machine_architecture": "...",
                    "cpu_architecture": "...",
                    "python_version": "...",
                    "platform_string": "...",
                    "processor_name": "...",
                },
                "errors": [],
            }

        On any non-Linux platform::

            {
                "collector": "system_info",
                "status": "unsupported_platform",
                "platform": "...",
                "data": {},
                "errors": ["Linux Insight Agent supports Linux only."],
            }

        A field that cannot be individually determined is set to
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
    data = {
        "hostname": _safe_get(socket.gethostname, "hostname", errors),
        "operating_system": _safe_get(platform.system, "operating system", errors),
        "distribution_name": None,
        "distribution_version": None,
        "kernel_version": _safe_get(
            lambda: os.uname().release, "kernel version", errors
        ),
        "machine_architecture": _safe_get(
            lambda: os.uname().machine, "machine architecture", errors
        ),
        "cpu_architecture": _safe_get(
            lambda: platform.architecture()[0], "CPU architecture", errors
        ),
        "python_version": _safe_get(
            platform.python_version, "Python version", errors
        ),
        "platform_string": _safe_get(platform.platform, "platform string", errors),
        "processor_name": _get_processor_name(errors),
    }
    data["distribution_name"], data["distribution_version"] = _get_distribution_info(
        errors
    )

    return {
        "collector": _COLLECTOR_NAME,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": current_platform,
        "data": data,
        "errors": errors,
    }


def _safe_get(func: Callable[[], str], field_name: str, errors: List[str]) -> str:
    """Call a zero-argument info function, recording an error on failure.

    Args:
        func: A zero-argument callable returning a string (e.g.
            ``platform.system``).
        field_name: Human-readable name of the field being collected,
            used in the error message if the call fails.
        errors: Shared list that failure messages are appended to.

    Returns:
        The callable's return value as a string, or "Unknown" if the
        call raises an exception or returns an empty value.
    """
    try:
        value = func()
    except (OSError, RuntimeError, ValueError) as error:
        errors.append(f"Unable to determine {field_name}: {error}")
        return "Unknown"
    if not value:
        errors.append(f"Unable to determine {field_name}.")
        return "Unknown"
    return str(value)


def _get_processor_name(errors: List[str]) -> str:
    """Determine the CPU model name, with a Linux-specific fallback.

    ``platform.processor()`` is documented as returning the raw result
    of ``uname -p``, but on most Linux distributions that value is not
    populated by the kernel/libc and comes back empty (or "unknown").
    To still report a meaningful value, fall back to parsing the
    "model name" field out of ``/proc/cpuinfo``, which the kernel
    always populates on x86/x86_64.

    Args:
        errors: Shared list that a failure message is appended to if
            neither source yields a value.

    Returns:
        The processor model name, or "Unknown" if neither
        ``platform.processor()`` nor ``/proc/cpuinfo`` yields one.
    """
    try:
        processor = platform.processor()
    except (OSError, RuntimeError):
        processor = ""

    if processor and processor.lower() != "unknown":
        return processor

    model_name = _read_cpuinfo_model_name()
    if model_name:
        return model_name

    errors.append(
        "Unable to determine processor name from platform.processor() "
        "or /proc/cpuinfo."
    )
    return "Unknown"


def _read_cpuinfo_model_name() -> Optional[str]:
    """Read the CPU model name from ``/proc/cpuinfo``, if present.

    Returns:
        The value of the first "model name" field found, or ``None``
        if the file is missing, unreadable, or has no such field.
    """
    if not _CPUINFO_PATH.is_file():
        return None
    try:
        contents = _CPUINFO_PATH.read_text(encoding="utf-8")
    except OSError:
        return None

    for line in contents.splitlines():
        if line.lower().startswith("model name"):
            _, _, value = line.partition(":")
            value = value.strip()
            if value:
                return value
    return None


def _get_distribution_info(errors: List[str]) -> Tuple[str, str]:
    """Read the Linux distribution name and version from ``/etc/os-release``.

    Args:
        errors: Shared list that a failure message is appended to if
            the file is missing/unreadable or a field can't be found.

    Returns:
        A ``(distribution_name, distribution_version)`` tuple. Missing
        fields fall back to "Unknown".
    """
    fields: Dict[str, str] = {}
    if _OS_RELEASE_PATH.is_file():
        try:
            contents = _OS_RELEASE_PATH.read_text(encoding="utf-8")
        except OSError as error:
            errors.append(f"Unable to read /etc/os-release: {error}")
            contents = ""
        for line in contents.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                fields[key.strip()] = value.strip().strip('"')
    else:
        errors.append("/etc/os-release not found.")

    name = fields.get("NAME") or "Unknown"
    version = fields.get("VERSION_ID") or fields.get("VERSION") or "Unknown"

    if name == "Unknown" or version == "Unknown":
        errors.append(
            "Distribution name/version could not be fully determined "
            "from /etc/os-release."
        )

    return name, version
