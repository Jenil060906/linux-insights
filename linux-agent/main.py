"""Linux Agent startup script.

This is the agent's startup script for Phase 2 — it loads and
validates configuration, builds a fully-wired `core.engine.
MonitoringEngine` (Monitor, SnapshotManager, and Scheduler, with
dependencies injected between them), starts it, and displays a
summary of the latest snapshot once monitoring has run.

It is still **temporary**: Phase 2 hardcodes the run to exactly three
monitoring cycles before stopping automatically, purely so this
script terminates on its own during development, with no infinite
loop and no reliance on a manual interrupt (e.g. Ctrl+C). A later
phase is expected to replace this fixed-cycle-count behavior with
continuous operation.

If configuration is missing required values (e.g. a blank `agent.id`
or `agent.hostname`), loading/validation raises and this script exits
with that exception rather than proceeding with unusable
configuration — validation failures are intentionally not caught or
suppressed here.
"""

import threading

from core.engine import MonitoringEngine

# Number of monitoring cycles to allow before stopping the Scheduler.
# Temporary, for Phase 2 testing only (see module docstring).
_TARGET_CYCLES = 3


def main() -> None:
    """Run the Phase 2 startup sequence: build, run, summarize."""
    engine = _startup()
    _run_for_target_cycles(engine)
    _display_snapshot_summary(engine)


def _startup() -> MonitoringEngine:
    """Load configuration, validate it, and build a wired MonitoringEngine.

    Delegates the actual work to `MonitoringEngine.bootstrap()`, which
    performs, in order: Configuration Manager loads settings, the
    Configuration Manager validates them, then a `Monitor`, a
    `SnapshotManager`, and a `Scheduler` are created and wired
    together via dependency injection (the `Scheduler` receives the
    `Monitor`, the `SnapshotManager`, and the configured refresh
    interval — it never constructs or looks up any of them itself).
    This function adds nothing to that sequence; it only prints a
    short confirmation of what was loaded.

    Returns:
        A `MonitoringEngine` ready to be started.
    """
    engine = MonitoringEngine.bootstrap()
    print("Configuration Loaded")
    _print_configuration_summary(engine)
    return engine


def _print_configuration_summary(engine: MonitoringEngine) -> None:
    """Print the agent identity and scheduling values that were loaded.

    Args:
        engine: A `MonitoringEngine` built via `MonitoringEngine.
            bootstrap`, so `engine.config` is populated.
    """
    agent = engine.config.get("agent")
    scheduler_settings = engine.config.get("scheduler")

    print(f"{'Agent ID':<18}: {agent['id']}")
    print(f"{'Hostname':<18}: {agent['hostname']}")
    print(f"{'Refresh Interval':<18}: {scheduler_settings['refresh_interval']}")


def _run_for_target_cycles(engine: MonitoringEngine) -> None:
    """Start the Scheduler, let it complete exactly `_TARGET_CYCLES`, then stop it.

    Neither `Monitor` nor `Scheduler` (and so neither does
    `MonitoringEngine`, which only delegates to them) expose a "run N
    cycles and stop" mode or any progress callback on their own (by
    design — see their own docstrings), so this function counts
    completed cycles itself by wrapping `monitor.run` on the engine's
    own `Monitor` instance (reached via `MonitoringEngine.monitor`).
    The wrapper still calls the real `run()` for every cycle and
    returns its result unchanged; it only adds counting around it.
    This does not modify `Monitor`, `Scheduler`, or `MonitoringEngine`
    themselves — only this one instance's bound method is replaced.

    Args:
        engine: The `MonitoringEngine` to start and stop.
    """
    cycles_completed = 0
    cycles_lock = threading.Lock()
    # Set once the target cycle count has been reached, so the main
    # thread has something bounded to wait on instead of polling.
    target_reached = threading.Event()

    original_run = engine.monitor.run

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

    engine.monitor.run = counting_run

    engine.start()
    print("Scheduler Started")

    # Block until the target cycle count has been reached. This is a
    # single bounded wait on an event set by the cycle-counting
    # wrapper above — not a loop, and not dependent on manual
    # interruption.
    target_reached.wait()

    # stop() blocks until the background loop has fully exited, so the
    # SnapshotManager is guaranteed to already hold the last cycle's
    # snapshot by the time this call returns.
    engine.stop()
    print("Scheduler Stopped")


def _display_snapshot_summary(engine: MonitoringEngine) -> None:
    """Print a short summary of the latest snapshot — not the whole thing.

    Reads only the specific fields needed for this summary
    (timestamp, overall status, and collector counts) via
    `MonitoringEngine`'s own accessors; the full snapshot dictionary
    (collector-level data, etc.) is never printed.

    Args:
        engine: The `MonitoringEngine` that was running throughout
            this script.
    """
    snapshot = engine.get_latest_snapshot()
    if snapshot is None:
        print("No snapshot is available.")
        return

    monitoring_info = snapshot.get("monitoring", {})

    print(f"{'Snapshot Timestamp':<22}: {engine.get_snapshot_timestamp()}")
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
