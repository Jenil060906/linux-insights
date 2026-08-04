"""Temporary manual test script for the Configuration Manager pipeline.

This is **not** part of the permanent Linux Insight agent — it exists
only to exercise the Configuration Manager (`config.config_loader` +
`config.validator`) together with `core.scheduler.Scheduler` and
`core.snapshot.SnapshotManager`, end-to-end, from the command line
during development: load configuration, validate it, create a
`Monitor`, a `SnapshotManager`, and a `Scheduler` (with the
`SnapshotManager` and the *configured* refresh interval injected into
the `Scheduler`), let it run exactly three monitoring cycles, stop it
automatically, then read the latest snapshot back out of the
`SnapshotManager` and print a short summary of it. There is no
infinite loop and no reliance on a manual interrupt (e.g. Ctrl+C) —
the script always terminates on its own.

If configuration is missing required values (e.g. a blank `agent.id`
or `agent.hostname`), `validate_config` raises and this script exits
with that exception rather than proceeding with unusable
configuration — validation failures are intentionally not caught or
suppressed here.
"""

import threading

from config.config_loader import load_config
from config.validator import validate_config
from core.monitor import Monitor
from core.scheduler import Scheduler
from core.snapshot import SnapshotManager

# Number of monitoring cycles to allow before stopping the scheduler.
_TARGET_CYCLES = 3


def main() -> None:
    """Load and validate configuration, run three cycles, then summarize.

    Neither `Monitor` nor `Scheduler` expose a "run N cycles and stop"
    mode or any progress callback on their own (by design — see their
    own docstrings), so this script counts completed cycles itself by
    wrapping `monitor.run` on this one `Monitor` instance. The wrapper
    still calls the real `run()` for every cycle and returns its
    result unchanged; it only adds counting around it. This does not
    modify the `Monitor` or `Scheduler` classes themselves — only this
    local instance's bound method is replaced.
    """
    config = load_config()
    validate_config(config)
    print("Configuration Loaded")

    # Safe to index directly (rather than using `.get()` with
    # fallbacks) because `validate_config` already guarantees these
    # three values are present and well-formed — re-checking them
    # here would duplicate what the Configuration Manager already
    # did.
    agent = config.get("agent")
    scheduler_settings = config.get("scheduler")
    agent_id = agent["id"]
    hostname = agent["hostname"]
    refresh_interval = scheduler_settings["refresh_interval"]

    print(f"{'Agent ID':<18}: {agent_id}")
    print(f"{'Hostname':<18}: {hostname}")
    print(f"{'Refresh Interval':<18}: {refresh_interval}")

    monitor = Monitor()
    snapshot_manager = SnapshotManager()
    # Dependency injection: the Scheduler only ever receives the
    # SnapshotManager and interval it's given here, sourced from the
    # already-validated configuration — it never reads configuration
    # or hardcodes an interval of its own.
    scheduler = Scheduler(
        monitor=monitor,
        snapshot_manager=snapshot_manager,
        interval_seconds=refresh_interval,
    )

    cycles_completed = 0
    cycles_lock = threading.Lock()
    # Set once the third cycle has completed, so the main thread has
    # something bounded to wait on instead of polling in a loop.
    target_reached = threading.Event()

    original_run = monitor.run

    def counting_run() -> dict:
        """Run one real monitoring cycle, then count it."""
        nonlocal cycles_completed
        result = original_run()

        with cycles_lock:
            cycles_completed += 1
            completed_count = cycles_completed

        if completed_count >= _TARGET_CYCLES:
            target_reached.set()

        return result

    monitor.run = counting_run

    scheduler.start()
    print("Scheduler Started")

    # Block until the third cycle has completed. This is a single
    # bounded wait on an event set by the cycle-counting wrapper
    # above — not a loop, and not dependent on manual interruption.
    target_reached.wait()

    # stop() blocks until the background loop has fully exited, so the
    # SnapshotManager is guaranteed to already hold the third cycle's
    # snapshot by the time this call returns.
    scheduler.stop()
    print("Scheduler Stopped")

    _print_snapshot_summary(snapshot_manager)


def _print_snapshot_summary(snapshot_manager: SnapshotManager) -> None:
    """Print a short summary of the latest snapshot — not the whole thing.

    Reads only the specific fields needed for this summary
    (timestamp, overall status, and collector counts) via
    `SnapshotManager`'s own accessors; the full snapshot dictionary
    (collector-level data, etc.) is never printed.

    Args:
        snapshot_manager: The `SnapshotManager` the Scheduler was
            updating throughout the run.
    """
    snapshot = snapshot_manager.get_latest_snapshot()
    if snapshot is None:
        print("No snapshot is available.")
        return

    monitoring_info = snapshot.get("monitoring", {})

    print(f"{'Snapshot Timestamp':<22}: {snapshot_manager.get_snapshot_timestamp()}")
    print(f"{'Monitoring Status':<22}: {monitoring_info.get('status', 'Unknown')}")
    print(
        f"{'Total Collectors':<22}: "
        f"{monitoring_info.get('total_collectors', 'Unknown')}"
    )
    print(
        f"{'Successful Collectors':<22}: "
        f"{monitoring_info.get('successful_collectors', 'Unknown')}"
    )
    print(
        f"{'Failed Collectors':<22}: "
        f"{monitoring_info.get('failed_collectors', 'Unknown')}"
    )


if __name__ == "__main__":
    main()
