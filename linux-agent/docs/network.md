# Network Collector

`collectors/network.py` — implemented, Linux-only network configuration and statistics collector.

## Overview

The Network Collector gathers a snapshot of network configuration and interface statistics for the host machine — per-interface addressing/link details and I/O counters, plus a total interface count and hostname — as opposed to the CPU/memory/disk metrics covered by the other collectors. It is exposed through a single public function, `collect_network_info()`, which returns a plain `dict` and takes no arguments.

Like the other collectors in this package, it is **Linux-only by design**. Rather than approximating or partially collecting on another operating system, it detects the host OS up front and returns a clearly-flagged `"unsupported_platform"` response if it isn't Linux.

## Responsibilities

`collect_network_info()` is responsible for, and only for:

- Detecting whether the current host operating system is Linux before collecting anything.
- Enumerating every network interface currently present on the host (not only ones that are administratively up).
- Excluding the loopback interface (`lo`) unless it's the only interface present at all (see [Ignored Interfaces](#ignored-interfaces)).
- For every remaining interface: name, operational (Up/Down) status, MAC address, IPv4 address, IPv6 address (if available), netmask, broadcast address (if available), MTU (if available), link speed (if available), and duplex mode (if available).
- For every remaining interface: I/O statistics — bytes and packets sent/received, input/output errors, and dropped incoming/outgoing packets.
- Reporting the total number of interfaces reported and the host's network hostname.
- Continuing to collect the remaining interfaces if one interface's data can't be assembled, recording why in `errors` instead of failing the whole collection.
- Returning everything as one dictionary — no side effects.

It is explicitly **not** responsible for: static host identity, CPU, memory, or disk metrics (see the other files in this directory), DNS/gateway/routing information, open connections, wireless signal quality, or latency (see [Future Enhancements](#future-enhancements)), scheduling repeated sampling, printing/logging output, or sending data anywhere (no network or API calls of its own).

## Linux Dependencies

| Module | Used for | Why |
|---|---|---|
| `psutil.net_if_addrs()` | Per-interface addresses: MAC, IPv4, IPv6, netmask, broadcast. | Surfaces the Linux kernel's per-interface address list (the same data behind `ip addr`) directly as structured named tuples, keyed by address family, with no parsing required. |
| `psutil.net_if_stats()` | Per-interface operational status, MTU, speed, and duplex mode. | Surfaces the Linux kernel's per-interface link state (the same data behind `ip link` / `ethtool`) directly, without needing to read `/sys/class/net/*` or invoke a tool. |
| `psutil.net_io_counters(pernic=True)` | Per-interface I/O statistics: bytes/packets sent and received, errors, drops. | Surfaces the kernel's per-interface traffic counters (the same data behind `/proc/net/dev`) directly as structured named tuples. |
| `socket.AF_INET` / `socket.AF_INET6` | Distinguishing IPv4 vs. IPv6 entries within an interface's address list. | Standard library address-family constants; `psutil` reports each address's family using these same values, so no separate mapping is needed. |
| `psutil.AF_LINK` | Identifying the link-layer (MAC) address entry within an interface's address list. | The cross-platform constant `psutil` provides for the OS's link-layer address family (`socket.AF_PACKET` on Linux), so the collector doesn't need to hardcode a platform-specific value. |
| `ipaddress.ip_address()` | Validating and canonicalizing IPv4/IPv6 address strings, including scoped IPv6 link-local addresses (e.g. `fe80::1%eth0`). | Guarantees a consistent, canonical address representation (e.g. compressed IPv6 notation) rather than trusting the raw string `psutil` returns as-is, while still degrading gracefully to the raw string if it's ever unparseable. |
| `platform.system()` | The Linux-only gate at the top of `collect_network_info()`. | Determines whether to proceed with collection at all. |

> **Why not `ip`, `ifconfig`, `netstat`, or `ss`?** All of the data this collector needs is already exposed through `psutil` and the standard library, without spawning a process. Shelling out to a CLI tool would mean parsing its text output (which varies across distributions and tool versions and can silently break), incurring process-launch overhead per collection cycle, and depending on that tool being installed and on `PATH` on every monitored host. Reading the same underlying kernel data directly through `psutil`'s bindings avoids all of that, and this collector never imports `subprocess` or invokes a shell command.

## Returned Metrics

All metrics live under the top-level `data` key of the returned dictionary (see [Returned Dictionary Structure](#returned-dictionary-structure)). Per-interface fields apply to each entry in `interfaces`; `io_stats` is a nested `dict` within each interface entry.

| Metric | Description | Units | Example |
|---|---|---|---|
| `interfaces[].interface_name` | Interface name | string | `enp0s3` |
| `interfaces[].operational_status` | Whether the interface is currently up or down | string (`"Up"`/`"Down"`) | `Up` |
| `interfaces[].mac_address` | Link-layer (MAC) address | string | `08:00:27:34:97:a6` |
| `interfaces[].ipv4_address` | IPv4 address, if assigned | string | `192.168.1.19` |
| `interfaces[].ipv6_address` | IPv6 address, if assigned (may be link-local) | string | `fe80::a00:27ff:fe34:97a6%enp0s3` |
| `interfaces[].netmask` | IPv4 subnet mask | string | `255.255.255.0` |
| `interfaces[].broadcast_address` | IPv4 broadcast address, if available | string | `192.168.1.255` |
| `interfaces[].mtu` | Maximum transmission unit | bytes | `1500` |
| `interfaces[].speed_mbps` | Negotiated link speed, if the kernel can determine it | megabits/second | `1000` |
| `interfaces[].duplex_mode` | Duplex mode | string (`"full"`/`"half"`/`"Unknown"`) | `full` |
| `interfaces[].io_stats.bytes_sent` | Total bytes transmitted | bytes | `9004617` |
| `interfaces[].io_stats.bytes_received` | Total bytes received | bytes | `18987842` |
| `interfaces[].io_stats.packets_sent` | Total packets transmitted | count | `17091` |
| `interfaces[].io_stats.packets_received` | Total packets received | count | `24477` |
| `interfaces[].io_stats.input_errors` | Receive errors | count | `0` |
| `interfaces[].io_stats.output_errors` | Transmit errors | count | `0` |
| `interfaces[].io_stats.dropped_incoming_packets` | Incoming packets dropped | count | `0` |
| `interfaces[].io_stats.dropped_outgoing_packets` | Outgoing packets dropped | count | `0` |
| `total_active_interfaces` | Count of entries in `interfaces` | integer | `1` |
| `hostname` | The host's network hostname | string | `alphaSenate` |

## Ignored Interfaces

The loopback interface (`lo`) is excluded from `interfaces` **unless it is the only interface present on the host at all** (e.g. a minimal container with no external network attached).

Loopback traffic is local-only (the kernel looping packets back to the same host) and isn't representative of the host's actual network connectivity or throughput, so including it alongside real interfaces would dilute — not add to — an observability snapshot meant to reflect the host's network state. The one exception (keep it when it's the *only* interface) exists so the collector never silently returns zero interfaces on a host that genuinely has nothing else configured; reporting `lo` in that case is more useful than reporting nothing.

## Returned Dictionary Structure

`collect_network_info()` always returns a dictionary with exactly these top-level keys:

| Key | Type | Description |
|---|---|---|
| `collector` | `str` | Always `"network"` — identifies which collector produced this payload. |
| `status` | `str` | `"success"` on Linux, or `"unsupported_platform"` on any other OS. |
| `timestamp` | `str` | UTC timestamp of the collection, ISO 8601 format (e.g. `2026-07-25T12:00:00+00:00`), from `datetime.now(timezone.utc).isoformat()`. |
| `platform` | `str` | The detected OS name from `platform.system()` (e.g. `"Linux"`, `"Windows"`, `"Darwin"`). |
| `data` | `dict` | The metrics described in [Returned Metrics](#returned-metrics). Empty (`{}`) when `status` is `"unsupported_platform"`. |
| `errors` | `list[str]` | Human-readable messages for any interface (or interface-level data source) that could not be read. Empty when everything was collected successfully. |

## Error Handling

**Unsupported platform.** Before collecting anything, the collector checks `platform.system()`. If it is not `"Linux"`, collection is skipped entirely and it returns:

```python
{
    "collector": "network",
    "status": "unsupported_platform",
    "platform": "Darwin",
    "data": {},
    "errors": ["Linux Insight Agent supports Linux only."],
}
```

**Unreadable interfaces.** Each interface's addresses, link stats, and I/O counters are assembled independently. If assembling a given interface's entry raises an unexpected error, that interface is omitted from `interfaces` entirely and a message identifying it is appended to `errors` — the remaining interfaces are still collected.

**Partial failures.** `psutil.net_if_addrs()`, `psutil.net_if_stats()`, and `psutil.net_io_counters()` are each called exactly once per collection (not once per interface), and each is guarded independently: if one of them raises, a single error is appended and that entire category of data (addresses, link stats, or I/O counters) falls back to empty for every interface — the other two categories, and the interfaces themselves, are still collected. Within a single interface's entry, a missing address family (e.g. no IPv6 configured) or a missing stat (e.g. undeterminable link speed) individually falls back to `"Unknown"` without being treated as an error at all, since that's an expected, common condition rather than a failure.

In every case, `status` remains `"success"` on a supported platform — `errors` is additive context about individual interfaces or data sources, not a failure signal for the whole collection.

## Example Output

```python
{
    "collector": "network",
    "status": "success",
    "timestamp": "2026-07-26T07:57:48.153514+00:00",
    "platform": "Linux",
    "data": {
        "interfaces": [
            {
                "interface_name": "enp0s3",
                "operational_status": "Up",
                "mac_address": "08:00:27:34:97:a6",
                "ipv4_address": "192.168.1.19",
                "ipv6_address": "2401:4900:8f72:d7a1:a00:27ff:fe34:97a6",
                "netmask": "255.255.255.0",
                "broadcast_address": "192.168.1.255",
                "mtu": 1500,
                "speed_mbps": 1000,
                "duplex_mode": "full",
                "io_stats": {
                    "bytes_sent": 13535086,
                    "bytes_received": 19616835,
                    "packets_sent": 21496,
                    "packets_received": 26971,
                    "input_errors": 0,
                    "output_errors": 0,
                    "dropped_incoming_packets": 0,
                    "dropped_outgoing_packets": 0
                }
            }
        ],
        "total_active_interfaces": 1,
        "hostname": "alphaSenate"
    },
    "errors": []
}
```

## Future Enhancements

- DNS information (configured resolvers, search domains), from `/etc/resolv.conf`.
- Default gateway information, from the kernel routing table.
- Full routing table entries, beyond just the default gateway.
- Open TCP/UDP connections (e.g. via `psutil.net_connections()`), including per-connection state and owning process.
- Wireless signal quality/strength, for hosts with a Wi-Fi interface.
- Network latency (e.g. round-trip time to a configured target), which would require actively probing rather than reading passive kernel counters.
