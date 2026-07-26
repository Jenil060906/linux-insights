"""Network collector.

Collects a snapshot of network configuration and interface statistics
for the current machine — per-interface addressing/link details and
I/O counters, plus a total interface count and hostname. This
collector is Linux-only: on any other operating system,
``collect_network_info()`` returns an ``"unsupported_platform"``
response instead of attempting to collect data.

"Active" interfaces are the ones the host currently has present
(anything ``psutil`` can enumerate), not only ones that are
administratively up — each interface's real Up/Down state is reported
via ``operational_status`` instead, since pre-filtering to only "up"
interfaces would make that field meaningless. The loopback interface
(``lo``) is excluded unless it is the only interface present at all.

Uses ``psutil`` for interface enumeration, link statistics, and I/O
counters, and ``socket``/``ipaddress`` for address-family matching and
address normalization. No shell commands or subprocesses are invoked
(no ``ip``, ``ifconfig``, ``netstat``, or ``ss``) — every value comes
from Linux networking APIs exposed directly through ``psutil`` and
``socket``. Fully self-contained: no printing, logging, scheduling,
threading, or network/API calls of its own.
"""

import platform
import socket
from datetime import datetime, timezone
from ipaddress import ip_address
from typing import Dict, List, Optional, Tuple

import psutil

_COLLECTOR_NAME = "network"
_LOOPBACK_INTERFACE_NAME = "lo"

_DUPLEX_LABELS = {
    psutil.NIC_DUPLEX_FULL: "full",
    psutil.NIC_DUPLEX_HALF: "half",
    psutil.NIC_DUPLEX_UNKNOWN: "Unknown",
}


def collect_network_info() -> Dict[str, object]:
    """Collect a network configuration/statistics snapshot for the host.

    Linux-only: if the host operating system is not Linux, an
    ``"unsupported_platform"`` response is returned instead of
    attempting collection.

    Returns:
        On Linux, a dictionary shaped like::

            {
                "collector": "network",
                "status": "success",
                "timestamp": "2026-07-25T12:00:00+00:00",
                "platform": "Linux",
                "data": {
                    "interfaces": [
                        {
                            "interface_name": "enp0s3",
                            "operational_status": "Up",
                            "mac_address": "08:00:27:34:97:a6",
                            "ipv4_address": "192.168.1.19",
                            "ipv6_address": "fe80::a00:27ff:fe34:97a6%enp0s3",
                            "netmask": "255.255.255.0",
                            "broadcast_address": "192.168.1.255",
                            "mtu": 1500,
                            "speed_mbps": 1000,
                            "duplex_mode": "full",
                            "io_stats": {
                                "bytes_sent": 9004617,
                                "bytes_received": 18987842,
                                "packets_sent": 17091,
                                "packets_received": 24477,
                                "input_errors": 0,
                                "output_errors": 0,
                                "dropped_incoming_packets": 0,
                                "dropped_outgoing_packets": 0,
                            },
                        },
                        ...
                    ],
                    "total_active_interfaces": 1,
                    "hostname": "alphaSenate",
                },
                "errors": [],
            }

        On any non-Linux platform::

            {
                "collector": "network",
                "status": "unsupported_platform",
                "platform": "...",
                "data": {},
                "errors": ["Linux Insight Agent supports Linux only."],
            }

        If an individual interface cannot be read, it is omitted from
        "interfaces" and a message describing the failure is appended
        to "errors" — collection continues with the remaining
        interfaces rather than failing outright.
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
    addresses_by_interface = _get_all_addresses(errors)
    stats_by_interface = _get_all_stats(errors)
    io_counters_by_interface = _get_all_io_counters(errors)

    all_names = (
        set(addresses_by_interface)
        | set(stats_by_interface)
        | set(io_counters_by_interface)
    )
    interface_names = _select_interface_names(all_names)

    interfaces: List[Dict[str, object]] = []
    for name in interface_names:
        interface_data = _read_interface(
            name,
            addresses_by_interface.get(name, []),
            stats_by_interface.get(name),
            io_counters_by_interface.get(name),
            errors,
        )
        if interface_data is not None:
            interfaces.append(interface_data)

    data = {
        "interfaces": interfaces,
        "total_active_interfaces": len(interfaces),
        "hostname": _get_hostname(errors),
    }

    return {
        "collector": _COLLECTOR_NAME,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": current_platform,
        "data": data,
        "errors": errors,
    }


def _get_all_addresses(errors: List[str]) -> Dict[str, List[object]]:
    """Enumerate per-interface addresses via ``psutil.net_if_addrs()``.

    Args:
        errors: Shared list that a failure message is appended to if
            addresses cannot be enumerated at all.

    Returns:
        A mapping of interface name to its list of ``snicaddr``
        entries, or an empty dict on failure.
    """
    try:
        return psutil.net_if_addrs()
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to enumerate network interface addresses: {error}")
        return {}


def _get_all_stats(errors: List[str]) -> Dict[str, object]:
    """Enumerate per-interface link stats via ``psutil.net_if_stats()``.

    Args:
        errors: Shared list that a failure message is appended to if
            interface statistics cannot be read at all.

    Returns:
        A mapping of interface name to its ``snicstats`` entry, or an
        empty dict on failure.
    """
    try:
        return psutil.net_if_stats()
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to read network interface statistics: {error}")
        return {}


def _get_all_io_counters(errors: List[str]) -> Dict[str, object]:
    """Read per-interface I/O counters via ``psutil.net_io_counters()``.

    Args:
        errors: Shared list that a failure message is appended to if
            I/O counters cannot be read at all.

    Returns:
        A mapping of interface name to its ``snetio`` entry, or an
        empty dict on failure.
    """
    try:
        return psutil.net_io_counters(pernic=True)
    except (OSError, RuntimeError) as error:
        errors.append(f"Unable to read network I/O counters: {error}")
        return {}


def _select_interface_names(all_names: set) -> List[str]:
    """Select which interfaces to report, applying the loopback rule.

    The loopback interface (``lo``) is excluded unless it is the only
    interface present on the host at all.

    Args:
        all_names: The full set of interface names discovered across
            all sources.

    Returns:
        A sorted list of interface names to report.
    """
    if not all_names:
        return []
    if all_names == {_LOOPBACK_INTERFACE_NAME}:
        return [_LOOPBACK_INTERFACE_NAME]
    return sorted(name for name in all_names if name != _LOOPBACK_INTERFACE_NAME)


def _read_interface(
    name: str,
    addresses: List[object],
    stats: Optional[object],
    io_counters: Optional[object],
    errors: List[str],
) -> Optional[Dict[str, object]]:
    """Assemble one interface's full data entry.

    Args:
        name: Interface name (e.g. ``"enp0s3"``).
        addresses: That interface's ``snicaddr`` entries, if any.
        stats: That interface's ``snicstats`` entry, if any.
        io_counters: That interface's ``snetio`` entry, if any.
        errors: Shared list that a failure message is appended to if
            this interface's data can't be assembled.

    Returns:
        A dictionary describing the interface, or ``None`` if an
        unexpected error occurs while reading it.
    """
    try:
        mac_address, ipv4_address, netmask, broadcast_address, ipv6_address = (
            _read_addresses(addresses)
        )
        operational_status, mtu, speed_mbps, duplex_mode = _read_stats(stats)

        return {
            "interface_name": name,
            "operational_status": operational_status,
            "mac_address": mac_address,
            "ipv4_address": ipv4_address,
            "ipv6_address": ipv6_address,
            "netmask": netmask,
            "broadcast_address": broadcast_address,
            "mtu": mtu,
            "speed_mbps": speed_mbps,
            "duplex_mode": duplex_mode,
            "io_stats": _read_io_stats(io_counters),
        }
    except (AttributeError, ValueError) as error:
        errors.append(f"Unable to read network interface {name}: {error}")
        return None


def _read_addresses(addresses: List[object]) -> Tuple[str, str, str, str, str]:
    """Extract MAC/IPv4/IPv6/netmask/broadcast from an interface's addresses.

    Args:
        addresses: The interface's ``snicaddr`` entries.

    Returns:
        A ``(mac_address, ipv4_address, netmask, broadcast_address,
        ipv6_address)`` tuple. Each element is "Unknown" if that
        address family isn't present for the interface.
    """
    mac_address = "Unknown"
    ipv4_address = "Unknown"
    netmask = "Unknown"
    broadcast_address = "Unknown"
    ipv6_address = "Unknown"

    for entry in addresses:
        if entry.family == psutil.AF_LINK and mac_address == "Unknown":
            mac_address = entry.address or "Unknown"
        elif entry.family == socket.AF_INET and ipv4_address == "Unknown":
            ipv4_address = _normalize_ip(entry.address)
            netmask = entry.netmask or "Unknown"
            broadcast_address = entry.broadcast or "Unknown"
        elif entry.family == socket.AF_INET6 and ipv6_address == "Unknown":
            ipv6_address = _normalize_ip(entry.address)

    return mac_address, ipv4_address, netmask, broadcast_address, ipv6_address


def _normalize_ip(address: Optional[str]) -> str:
    """Validate and canonicalize an IPv4/IPv6 address string.

    Args:
        address: The raw address string reported by ``psutil``.

    Returns:
        The canonical string form via ``ipaddress.ip_address()``
        (supports scoped IPv6 link-local addresses, e.g.
        ``"fe80::1%eth0"``), or the original raw string if it isn't a
        parseable address, or "Unknown" if empty.
    """
    if not address:
        return "Unknown"
    try:
        return str(ip_address(address))
    except ValueError:
        return address


def _read_stats(stats: Optional[object]) -> Tuple[str, object, object, str]:
    """Extract operational status, MTU, speed, and duplex from link stats.

    Args:
        stats: The interface's ``snicstats`` entry, or ``None`` if
            unavailable.

    Returns:
        A ``(operational_status, mtu, speed_mbps, duplex_mode)``
        tuple. Each element is "Unknown" if ``stats`` is ``None`` or
        the specific value isn't meaningfully reported (e.g. ``speed``
        is ``0`` when the kernel can't determine it).
    """
    if stats is None:
        return "Unknown", "Unknown", "Unknown", "Unknown"

    operational_status = "Up" if stats.isup else "Down"
    mtu = stats.mtu if stats.mtu else "Unknown"
    speed_mbps = stats.speed if stats.speed else "Unknown"
    duplex_mode = _DUPLEX_LABELS.get(stats.duplex, "Unknown")

    return operational_status, mtu, speed_mbps, duplex_mode


def _read_io_stats(io_counters: Optional[object]) -> Dict[str, object]:
    """Extract I/O counters for one interface.

    Args:
        io_counters: The interface's ``snetio`` entry, or ``None`` if
            unavailable.

    Returns:
        A dictionary with "bytes_sent", "bytes_received",
        "packets_sent", "packets_received", "input_errors",
        "output_errors", "dropped_incoming_packets", and
        "dropped_outgoing_packets" keys, each "Unknown" if
        ``io_counters`` is ``None``.
    """
    if io_counters is None:
        return {
            "bytes_sent": "Unknown",
            "bytes_received": "Unknown",
            "packets_sent": "Unknown",
            "packets_received": "Unknown",
            "input_errors": "Unknown",
            "output_errors": "Unknown",
            "dropped_incoming_packets": "Unknown",
            "dropped_outgoing_packets": "Unknown",
        }

    return {
        "bytes_sent": io_counters.bytes_sent,
        "bytes_received": io_counters.bytes_recv,
        "packets_sent": io_counters.packets_sent,
        "packets_received": io_counters.packets_recv,
        "input_errors": io_counters.errin,
        "output_errors": io_counters.errout,
        "dropped_incoming_packets": io_counters.dropin,
        "dropped_outgoing_packets": io_counters.dropout,
    }


def _get_hostname(errors: List[str]) -> str:
    """Determine the host's network hostname via ``socket.gethostname()``.

    Args:
        errors: Shared list that a failure message is appended to if
            the hostname can't be determined.

    Returns:
        The hostname, or "Unknown" on failure.
    """
    try:
        hostname = socket.gethostname()
    except OSError as error:
        errors.append(f"Unable to determine hostname: {error}")
        return "Unknown"
    return hostname or "Unknown"