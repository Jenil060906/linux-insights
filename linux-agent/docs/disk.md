# Disk Collector

`collectors/disk.py` — implemented, Linux-only filesystem and storage collector.

## Overview

The Disk Collector gathers filesystem and storage information for the host machine — per-partition device, mount, and usage details, plus a partition count and root filesystem usage — as opposed to the CPU/memory metrics covered by the [CPU Collector](cpu.md) and [Memory Collector](memory.md). It is exposed through a single public function, `collect_disk_info()`, which returns a plain `dict` and takes no arguments.

Like the other collectors in this package, it is **Linux-only by design**. Rather than approximating or partially collecting on another operating system, it detects the host OS up front and returns a clearly-flagged `"unsupported_platform"` response if it isn't Linux.

## Responsibilities

`collect_disk_info()` is responsible for, and only for:

- Detecting whether the current host operating system is Linux before collecting anything.
- Enumerating every mounted filesystem and identifying its type before reading any usage data.
- Skipping known Linux virtual/pseudo-filesystems entirely (see [Ignored Filesystems](#ignored-filesystems)) — silently, not as an error.
- For every remaining (real storage) partition: device name, mount point, filesystem type, mount options, total/used/free space, usage percentage, and read-only/read-write status.
- Reporting the total number of mounted (non-ignored) partitions.
- Reporting root filesystem (`/`) usage independently of the partition list.
- Continuing to collect the remaining partitions if one real storage partition can't be read, recording why in `errors` instead of failing the whole collection.
- Returning everything as one dictionary — no side effects.

It is explicitly **not** responsible for: static host identity or CPU/memory metrics (see [`system-info.md`](system-info.md), [`cpu.md`](cpu.md), [`memory.md`](memory.md)), disk I/O throughput or latency, SMART/health data, unit conversion (values are always in bytes), scheduling repeated sampling, printing/logging output, or sending data anywhere (no network or API calls).

## Linux Dependencies

| Module / Resource | Used for | Why |
|---|---|---|
| `psutil.disk_partitions(all=True)` | Enumerating every mount in the Linux mount table (device, mount point, filesystem type, mount options), including pseudo-filesystems that `psutil`'s own default filtering would otherwise hide. | `all=True` is used deliberately instead of `psutil`'s default so this collector applies its own explicit ignore list (see below) rather than relying on `psutil`'s internal, less predictable filtering. |
| `psutil.disk_usage(mount_point)` | Total/used/free space and usage percentage for a given mount point. | Wraps the POSIX `statvfs()` call Linux exposes for any mounted filesystem. |
| Filesystem metadata (`fstype`, `opts`) from the mount table | Deciding whether a mount is real storage or a pseudo-filesystem, and deriving `read_only` from the presence of `ro`/`rw` among the mount options. | This is standard Linux mount-table metadata (the same fields shown by `mount` or found in `/proc/mounts`); `psutil` surfaces it without the collector needing to parse those files itself. |
| `pathlib.Path.exists()` / `os.access(path, os.R_OK)` | A pre-check, before calling `psutil.disk_usage()`, that a partition's mount point actually exists and is readable. | Avoids an unnecessary raised exception for mount points that are structurally present in the mount table but not currently accessible (e.g. an unmounted stale entry, or a permission-restricted kernel mount), and produces a clearer error message. |
| `platform.system()` | The Linux-only gate at the top of `collect_disk_info()`. | Determines whether to proceed with collection at all. |

> **Note:** No Linux files are read directly by this collector — `psutil` already surfaces the mount table and per-mount usage data it needs. This mirrors the [CPU Collector](cpu.md), which similarly needs no direct file reads because `psutil` already covers everything.

## Returned Metrics

All metrics live under the top-level `data` key of the returned dictionary (see [Returned Dictionary Structure](#returned-dictionary-structure)). Per-partition fields apply to each entry in `partitions`; `root_filesystem` is a separate nested `dict`.

| Metric | Description | Units | Example |
|---|---|---|---|
| `partitions[].device` | Block device (or pseudo-device name) backing the mount | string | `/dev/sda1` |
| `partitions[].mount_point` | Path the filesystem is mounted at | string | `/` |
| `partitions[].filesystem_type` | Filesystem type reported by the kernel | string | `ext4` |
| `partitions[].mount_options` | Parsed list of mount options | list of strings | `["rw", "relatime"]` |
| `partitions[].total_bytes` | Total space on the partition | bytes | `255000000000` |
| `partitions[].used_bytes` | Space currently in use | bytes | `120000000000` |
| `partitions[].free_bytes` | Space not currently in use | bytes | `135000000000` |
| `partitions[].usage_percent` | Usage as a percentage of total | percent | `47.1` |
| `partitions[].read_only` | Whether the mount is read-only | boolean (or `"Unknown"`) | `false` |
| `total_partitions` | Count of entries in `partitions` (after ignoring pseudo-filesystems) | integer | `12` |
| `root_filesystem.total_bytes` | Total space on the root (`/`) filesystem | bytes | `255000000000` |
| `root_filesystem.used_bytes` | Space in use on `/` | bytes | `120000000000` |
| `root_filesystem.free_bytes` | Free space on `/` | bytes | `135000000000` |
| `root_filesystem.usage_percent` | Usage percentage on `/` | percent | `47.1` |

## Ignored Filesystems

Before reading usage for any mounted filesystem, its `filesystem_type` is checked against a fixed ignore list. If it matches, the mount is skipped **completely** — it is not added to `partitions`, it does not count toward `total_partitions`, and **no entry is added to `errors`**, because skipping an expected pseudo-filesystem is normal behavior, not a collection failure.

The ignored types are Linux virtual/pseudo-filesystems: kernel-managed views into runtime state rather than actual on-disk storage, so "total/used/free space" is either meaningless or always zero for them:

| Filesystem type | What it is |
|---|---|
| `tmpfs`, `devtmpfs` | RAM-backed temporary filesystems (`/run`, `/dev`, etc.) |
| `squashfs` | Read-only compressed images (e.g. snap packages) |
| `proc` | The `/proc` process/kernel information interface |
| `sysfs` | The `/sys` kernel object/device interface |
| `securityfs` | LSM (security module) configuration interface |
| `debugfs`, `tracefs` | Kernel debugging and tracing interfaces |
| `overlay` | OverlayFS union mounts (e.g. container root filesystems) |
| `bpf` | The BPF filesystem (`/sys/fs/bpf`), for pinned eBPF objects |
| `pstore` | Persistent storage for kernel crash/panic records (`/sys/fs/pstore`) |
| `cgroup`, `cgroup2` | Control group hierarchies |
| `configfs` | Kernel object configuration interface |

Every other filesystem type — including real storage filesystems such as `ext4`, `xfs`, `btrfs`, `zfs`, `f2fs`, `ntfs`, `exfat`, and `vfat` — is always collected. This is a fixed set, not a whitelist: any type not in the table above is treated as real storage and reported normally.

> **Note:** Some other Linux pseudo-filesystems (e.g. `autofs`, `hugetlbfs`, `mqueue`, `fusectl`, `binfmt_misc`, `nsfs`, `devpts`, `fuse.*`) are **not** in this list and will currently appear in `partitions` with `total_bytes: 0`. Only the types explicitly named above are filtered.

## Returned Dictionary Structure

`collect_disk_info()` always returns a dictionary with exactly these top-level keys:

| Key | Type | Description |
|---|---|---|
| `collector` | `str` | Always `"disk"` — identifies which collector produced this payload. |
| `status` | `str` | `"success"` on Linux, or `"unsupported_platform"` on any other OS. |
| `timestamp` | `str` | UTC timestamp of the collection, ISO 8601 format (e.g. `2026-07-24T12:00:00+00:00`), from `datetime.now(timezone.utc).isoformat()`. |
| `platform` | `str` | The detected OS name from `platform.system()` (e.g. `"Linux"`, `"Windows"`, `"Darwin"`). |
| `data` | `dict` | The metrics described in [Returned Metrics](#returned-metrics). Empty (`{}`) when `status` is `"unsupported_platform"`. |
| `errors` | `list[str]` | Human-readable messages for any real storage partition that could not be read. Empty when everything was collected successfully. |

## Error Handling

**Unsupported platform.** Before collecting anything, the collector checks `platform.system()`. If it is not `"Linux"`, collection is skipped entirely and it returns:

```python
{
    "collector": "disk",
    "status": "unsupported_platform",
    "platform": "Windows",
    "data": {},
    "errors": ["Linux Insight Agent supports Linux only."],
}
```

**Unreadable partitions.** Each real storage partition (i.e. not in the ignored-filesystem set) is read independently. If its mount point doesn't exist, or `psutil.disk_usage()` raises for it, that partition is simply omitted from `partitions` and a message identifying the device and mount point is appended to `errors` — the remaining partitions are still collected.

**Permission errors.** Before calling `psutil.disk_usage()`, the collector checks `os.access(mount_point, os.R_OK)`. If the mount point isn't readable by the current process, it's treated the same as an unreadable partition: omitted from `partitions`, with a descriptive message in `errors` (rather than letting a `PermissionError` propagate).

**Root filesystem.** `root_filesystem` is read independently via `psutil.disk_usage("/")`. If that call itself raises, its four fields individually fall back to `"Unknown"` and a message is appended to `errors`.

In every case, `status` remains `"success"` on a supported platform — `errors` is additive context about individual partitions, not a failure signal for the whole collection.

## Example Output

```python
{
    "collector": "disk",
    "status": "success",
    "timestamp": "2026-07-25T08:20:10.058031+00:00",
    "platform": "Linux",
    "data": {
        "partitions": [
            {
                "device": "/dev/mapper/ubuntu--vg-ubuntu--lv",
                "mount_point": "/",
                "filesystem_type": "ext4",
                "mount_options": ["rw", "relatime"],
                "total_bytes": 50386849792,
                "used_bytes": 20484853760,
                "free_bytes": 27309289472,
                "usage_percent": 42.9,
                "read_only": false
            },
            {
                "device": "/dev/sda2",
                "mount_point": "/boot",
                "filesystem_type": "ext4",
                "mount_options": ["rw", "relatime"],
                "total_bytes": 2040373248,
                "used_bytes": 149671936,
                "free_bytes": 1766551552,
                "usage_percent": 7.8,
                "read_only": false
            },
            {
                "device": "/dev/sr0",
                "mount_point": "/run/media/jenil/VBox_GAs_7.0.20",
                "filesystem_type": "iso9660",
                "mount_options": ["ro", "nosuid", "nodev", "relatime"],
                "total_bytes": 53504000,
                "used_bytes": 53504000,
                "free_bytes": 0,
                "usage_percent": 100.0,
                "read_only": true
            }
        ],
        "total_partitions": 3,
        "root_filesystem": {
            "total_bytes": 50386849792,
            "used_bytes": 20484853760,
            "free_bytes": 27309289472,
            "usage_percent": 42.9
        }
    },
    "errors": []
}
```

## Future Enhancements

- SMART health status per physical disk (e.g. via `smartctl`), surfacing drive-level health rather than just filesystem-level usage.
- Disk temperature, where the platform/hardware exposes it.
- I/O statistics (read/write bytes and operations per second), from `psutil.disk_io_counters()`.
- Disk queue length / I/O wait time, for identifying storage-bound performance issues.
- RAID detection (e.g. `mdadm` arrays, LVM RAID), to report array-level status alongside individual member devices.
