"""Temporary manual test script for the Scheduler + Monitor pipeline.

This is **not** part of the permanent Linux Insight agent — it exists
only to exercise `core.scheduler.Scheduler` end-to-end from the
command line during development: start it, let it run exactly three
monitoring cycles, then stop it automatically and exit. There is no
infinite loop and no reliance on a manual interrupt (e.g. Ctrl+C) —
the script always terminates on its own.
"""

import threading

from core.monitor import Monitor
from core.scheduler import Scheduler

# Number of monitoring cycles to allow before stopping the scheduler.
_TARGET_CYCLES = 3

# Seconds between the end of one monitoring cycle and the start of
# the next.
_INTERVAL_SECONDS = 5


def main() -> None:
    """Start the Scheduler, observe exactly three cycles, then stop it.

    Neither `Monitor` nor `Scheduler` expose a "run N cycles and stop"
    mode or any progress callback on their own (by design — see their
    own docstrings), so this script counts completed cycles itself by
    wrapping `monitor.run` on this one `Monitor` instance. The wrapper
    still calls the real `run()` for every cycle and returns its
    result unchanged; it only adds counting and printing around it.
    This does not modify the `Monitor` or `Scheduler` classes
    themselves — only this local instance's bound method is replaced.
    """
    monitor = Monitor()
    scheduler = Scheduler(monitor, interval_seconds=_INTERVAL_SECONDS)

    cycles_completed = 0
    cycles_lock = threading.Lock()
    # Set once the third cycle has completed, so the main thread has
    # something bounded to wait on instead of polling in a loop.
    target_reached = threading.Event()

    original_run = monitor.run

    def counting_run() -> dict:
        """Run one real monitoring cycle, then count and report it."""
        nonlocal cycles_completed
        result = original_run()

        with cycles_lock:
            cycles_completed += 1
            completed_count = cycles_completed

        _print_cycle_result(completed_count, result)
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

    # stop() blocks until the background loop has fully exited, so no
    # further cycle can start after this call returns.
    scheduler.stop()
    print("Scheduler Stopped")


def _print_cycle_result(cycle_number: int, snapshot: dict) -> None:
    """Print a short per-cycle summary — not the full snapshot.

    Reads only `snapshot["monitoring"]["status"]` and
    `snapshot["monitoring"]["execution_time"]` (the compact,
    count/number-based summary `Monitor.run()` already produces for
    exactly this kind of use) and prints three lines: the cycle
    number, its status ("success" or "partial_success", whichever it
    actually is — never hardcoded), and its execution time in
    seconds. The rest of the snapshot (collector data, etc.) is
    intentionally not printed here.

    Args:
        cycle_number: The 1-based number of the cycle that just
            completed.
        snapshot: The dictionary `Monitor.run()` returned for this
            cycle.
    """
    monitoring_info = snapshot.get("monitoring", {})
    status = monitoring_info.get("status", "Unknown")
    execution_time = monitoring_info.get("execution_time", "Unknown")

    if isinstance(execution_time, (int, float)):
        execution_time_display = f"{execution_time:.2f} seconds"
    else:
        execution_time_display = str(execution_time)

    print(f"Monitoring Cycle {cycle_number}")
    print(f"{'Status':<17}: {status}")
    print(f"{'Execution Time':<17}: {execution_time_display}")


if __name__ == "__main__":
    main()
