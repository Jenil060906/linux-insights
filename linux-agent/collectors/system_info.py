"""System info collector.

Collects static host identity information — the kind of data that does
not change between successive collection cycles (hostname, OS/kernel
version, architecture, processor, and Python runtime details). For
volatile metrics (CPU load, memory usage, etc.), see the other
collectors in this package.

Relies only on the Python standard library (``platform``, ``socket``,
plus reading ``/proc/cpuinfo`` directly for the Linux processor-name
fallback) so this collector has no third-party dependencies.
"""

import platform
import socket
from typing import Dict


def collect_system_info() -> Dict[str, str]:
    """Collect static system identity information for the current host.

    Returns:
        A dictionary with the following string keys:
            - "hostname": Network name of the host.
            - "os": Operating system name (e.g. "Linux").
            - "os_version": Detailed OS release/version string.
            - "kernel_version": Kernel release version.
            - "architecture": Machine hardware architecture (e.g. "x86_64").
            - "processor": Processor name/identifier, if available.
            - "platform": Full platform identification string.
            - "python_version": Version of the running Python interpreter.

        Any field that cannot be determined is set to "unknown" instead
        of raising, so a single unavailable value never prevents the
        rest of the system information from being collected.

    Raises:
        OSError: If none of the system information sources are
            reachable at all, indicating a broader environment failure.
    """
    try:
        return {
            "hostname": _safe_call(socket.gethostname),
            "os": _safe_call(platform.system),
            "os_version": _safe_call(platform.version),
            "kernel_version": _safe_call(platform.release),
            "architecture": _safe_call(platform.machine),
            "processor": _get_processor_name(),
            "platform": _safe_call(platform.platform),
            "python_version": _safe_call(platform.python_version),
        }
    except OSError as error:
        raise OSError(f"Failed to collect system information: {error}") from error


def _get_processor_name() -> str:
    """Determine the CPU model name, with a Linux-specific fallback.

    ``platform.processor()`` is documented as returning the raw result
    of ``uname -p``, but on most Linux distributions that value is not
    populated by the kernel/libc and the call falls back to an empty
    string (normalized to "Unknown" by some ``platform`` versions)
    instead of an actual CPU model. To still report a meaningful value
    on Linux, fall back to parsing the "model name" field out of
    ``/proc/cpuinfo``, which the kernel always populates on x86/x86_64.

    Returns:
        The processor model name, or "unknown" if neither
        ``platform.processor()`` nor ``/proc/cpuinfo`` yields one.
    """
    processor = _safe_call(platform.processor)
    if processor.lower() != "unknown":
        return processor

    # platform.processor() came back empty/"Unknown" — read the CPU
    # model directly from the kernel's /proc/cpuinfo instead.
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
            for line in cpuinfo:
                if line.lower().startswith("model name"):
                    _, _, value = line.partition(":")
                    value = value.strip()
                    if value:
                        return value
    except (OSError, UnicodeDecodeError):
        pass

    return "unknown"


def _safe_call(func) -> str:
    """Call a zero-argument info function, falling back to "unknown".

    Args:
        func: A zero-argument callable returning a string (e.g.
            ``platform.system``).

    Returns:
        The callable's return value as a string, or "unknown" if the
        call raises an exception or returns an empty value.
    """
    try:
        value = func()
        return str(value) if value else "unknown"
    except (OSError, RuntimeError, ValueError):
        return "unknown"
