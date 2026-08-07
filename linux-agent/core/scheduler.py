"""Scheduler module.

Defines the :class:`Scheduler` class, which repeatedly runs a
:class:`~core.monitor.Monitor` instance on a fixed interval, in a
background thread, until explicitly stopped.

``Scheduler`` contains no collection or aggregation logic of its own —
it only calls the ``Monitor`` it is given, on schedule, and forwards
each successful cycle's snapshot to an injected
:class:`~core.snapshot.SnapshotManager`. It never modifies the
``Monitor`` it wraps, never constructs its own
``SnapshotManager`` (one is always supplied by the caller), and never
logs, persists to a database, or serves anything: pacing repeated
collection and keeping the latest snapshot available is the extent of
what this module is responsible for. Scheduling policy (fixed
interval, single active run loop) and pacing primitives
(``threading.Thread``, ``threading.Event``, ``time.sleep()``) round
out its responsibilities.

Each successful cycle also prints a short, three-line developer-facing
summary (cycle number, then whatever `SnapshotManager.update_snapshot`
itself prints, then overall status) — plain `print()` calls only, no
logging framework, and never the full snapshot. This is console
feedback for testing, not a change to what the Scheduler decides or
does.
"""

import threading
import time
from typing import Optional

from core.monitor import Monitor
from core.snapshot import SnapshotManager


class Scheduler:
    """Runs a `Monitor` repeatedly, on a fixed interval, until stopped.

    Each cycle is: call ``monitor.run()``, hand its result to the
    injected `SnapshotManager` via ``update_snapshot()``, then
    ``time.sleep()`` for the configured interval, then repeat — until
    :meth:`stop` is called. The cycle runs in a background
    `threading.Thread` so :meth:`start` returns immediately to the
    caller.

    At most one `Scheduler` instance may be running at a time across
    the whole process: calling :meth:`start` while another instance is
    already running raises `RuntimeError` rather than silently
    starting a second, competing collection loop. This is a process-
    wide invariant (tracked on the class, not per instance), because
    two concurrent monitoring loops would mean duplicate,
    interleaved collection work for no benefit.

    Usage::

        scheduler = Scheduler(
            monitor=Monitor(),
            snapshot_manager=SnapshotManager(),
            interval_seconds=30,
        )
        scheduler.start()
        ...
        scheduler.stop()  # blocks until the background loop exits
    """

    # Process-wide guard: the Scheduler instance currently running, if
    # any. `None` when no Scheduler is active. Guarded by `_class_lock`
    # so concurrent `start()` calls (from different instances, from
    # different threads) can't both pass the check at once.
    _active_scheduler: Optional["Scheduler"] = None
    _class_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        monitor: Monitor,
        snapshot_manager: SnapshotManager,
        interval_seconds: float,
    ) -> None:
        """Create a Scheduler for a given Monitor and refresh interval.

        Both collaborators are supplied by the caller (dependency
        injection) — the Scheduler never constructs its own `Monitor`
        or `SnapshotManager`, so callers can share, pre-configure, or
        substitute either independently of this class.

        Args:
            monitor: The `Monitor` instance to run repeatedly. The
                Scheduler only ever calls `monitor.run()` — it never
                modifies, reconfigures, or replaces this object.
            snapshot_manager: The `SnapshotManager` that each cycle's
                snapshot is handed to via `update_snapshot()`, after
                that cycle completes successfully. The Scheduler never
                reads from it, only writes to it.
            interval_seconds: How long to sleep between the end of one
                monitoring cycle and the start of the next, in
                seconds. Must be a positive number.

        Raises:
            ValueError: If `interval_seconds` is not a positive number.
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive number.")

        self._monitor = monitor
        self._snapshot_manager = snapshot_manager
        self._interval_seconds = interval_seconds

        # Set by stop() to signal the background loop to exit at its
        # next check. Never used to store or communicate snapshot
        # data — purely a stop signal.
        self._stop_event = threading.Event()

        # The background thread driving the loop, once started.
        # `None` before the first start() and after a full stop().
        self._thread: Optional[threading.Thread] = None

        # Explicit internal running state, set by the background
        # thread itself at the start/end of its loop (see
        # `_run_loop`), rather than only inferred from thread
        # liveness. Reads/writes are guarded by `_state_lock`.
        self._running = False
        self._state_lock = threading.Lock()

        # 1-based count of successful cycles in the current run, used
        # only for the "Monitoring Cycle N" console line. Reset on
        # each start() so a fresh run always begins counting at 1.
        # Purely cosmetic — no scheduling decision depends on it.
        #
        # Intentionally not guarded by a lock. This is safe under the
        # current architecture because each Scheduler instance's
        # monitoring loop runs on exactly one dedicated background
        # thread (see _run_loop, started by start()), and
        # _cycle_count is only ever read or written from within that
        # same thread — there is no concurrent access to synchronize
        # against. This single-worker-thread-per-instance assumption
        # is part of the current design, not an oversight. If a
        # future version ever allowed multiple worker threads to
        # drive a single Scheduler instance concurrently, that
        # assumption would no longer hold, and _cycle_count would
        # need explicit synchronization (e.g. reusing _state_lock) or
        # an atomic counter to stay correct.
        self._cycle_count = 0

    def start(self) -> None:
        """Start running the Monitor repeatedly, in a background thread.

        Returns immediately; the monitoring loop runs on a background
        `threading.Thread` until :meth:`stop` is called.

        Raises:
            RuntimeError: If this Scheduler instance is already
                running, or if a different Scheduler instance is
                currently running anywhere in this process.
        """
        with self._state_lock:
            if self._running:
                raise RuntimeError("This Scheduler instance is already running.")

            # Claim the process-wide "active scheduler" slot before
            # launching the thread, so two Schedulers racing to start
            # can't both succeed.
            with Scheduler._class_lock:
                if (
                    Scheduler._active_scheduler is not None
                    and Scheduler._active_scheduler is not self
                ):
                    raise RuntimeError(
                        "Another Scheduler instance is already running; "
                        "only one Scheduler may run at a time."
                    )
                Scheduler._active_scheduler = self

            self._stop_event.clear()
            self._running = True
            self._cycle_count = 0
            self._thread = threading.Thread(
                target=self._run_loop,
                name="linux-insight-scheduler",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Signal the background loop to stop and wait for it to exit.

        Blocks until the background thread has fully exited (i.e. the
        in-progress cycle, if any, finishes and the loop observes the
        stop signal), so the Monitor is guaranteed not to be mid-run
        by the time this method returns. Safe to call even if this
        Scheduler was never started, or has already stopped.
        """
        self._stop_event.set()

        thread = self._thread
        if thread is not None:
            thread.join()

        # Release the process-wide "active scheduler" slot, if this
        # instance was the one holding it.
        with Scheduler._class_lock:
            if Scheduler._active_scheduler is self:
                Scheduler._active_scheduler = None

    def is_running(self) -> bool:
        """Report whether the background monitoring loop is active.

        Returns:
            `True` if the background loop is currently running
            (between a successful `start()` and the loop actually
            exiting after `stop()`), `False` otherwise.
        """
        with self._state_lock:
            return self._running

    def _run_loop(self) -> None:
        """Background loop body: run the Monitor, sleep, repeat.

        Runs on the background thread started by `start()`. Checks
        the stop signal both before and after each `time.sleep()`
        call, so `stop()` takes effect at the next natural boundary
        between cycles rather than mid-collection.

        A `Monitor.run()` call is not expected to raise — it already
        isolates every individual collector's failures internally, so
        even a cycle with one or more failed collectors still returns
        a snapshot rather than raising — but this loop guards against
        an exception anyway (without logging or storing anything
        about the failure, per this module's constraints) so one
        unexpected exception can never silently kill the scheduling
        loop. A cycle only counts as "successful" here if
        `monitor.run()` returns normally; only then is its snapshot
        handed to the `SnapshotManager`, its console summary printed,
        and the cycle counter advanced — a cycle that raised produces
        no output at all and never overwrites the last good snapshot.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # The Scheduler's interaction with its two
                    # collaborators, once per cycle: trigger a
                    # Monitor run, then hand the resulting snapshot to
                    # the SnapshotManager. The snapshot itself is
                    # never printed or stored anywhere else by this
                    # class — only its overall status is read, for
                    # the console line below.
                    snapshot = self._monitor.run()

                    # Safe without a lock: this loop is this
                    # instance's single dedicated worker thread. See
                    # _cycle_count's declaration in __init__ for the
                    # full rationale.
                    self._cycle_count += 1
                    print(f"Monitoring Cycle {self._cycle_count}")

                    # SnapshotManager.update_snapshot() prints its own
                    # "Snapshot Updated" line as part of this call.
                    self._snapshot_manager.update_snapshot(snapshot)

                    status = snapshot.get("monitoring", {}).get("status", "Unknown")
                    print(f"Status: {status}")
                except Exception:  # noqa: BLE001 - must not kill the loop
                    pass

                if self._stop_event.is_set():
                    break

                # Pace the next cycle. A plain, fixed sleep is used
                # (rather than e.g. subtracting the cycle's own
                # duration) to keep this module's responsibility
                # limited to straightforward, predictable pacing.
                time.sleep(self._interval_seconds)
        finally:
            # Always clear the running flag on the way out, even if
            # something above behaved unexpectedly, so `is_running()`
            # never reports a stale "running" state.
            with self._state_lock:
                self._running = False