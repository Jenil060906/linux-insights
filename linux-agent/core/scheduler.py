"""Scheduler module.

Defines the :class:`Scheduler` class, which repeatedly runs a
:class:`~core.monitor.Monitor` instance on a fixed interval, in a
background thread, until explicitly stopped.

``Scheduler`` contains no collection or aggregation logic of its own —
it only calls the ``Monitor`` it is given, on schedule. It never
modifies the ``Monitor`` it wraps, never stores or inspects the
snapshots ``Monitor.run()`` returns, and never logs, persists, or
serves anything: pacing repeated collection is its one job. Scheduling
policy (fixed interval, single active run loop) and pacing primitives
(``threading.Thread``, ``threading.Event``, ``time.sleep()``) are the
extent of what this module is responsible for.
"""

import threading
import time
from typing import Optional

from core.monitor import Monitor


class Scheduler:
    """Runs a `Monitor` repeatedly, on a fixed interval, until stopped.

    Each cycle is: call ``monitor.run()``, then ``time.sleep()`` for
    the configured interval, then repeat — until :meth:`stop` is
    called. The cycle runs in a background `threading.Thread` so
    :meth:`start` returns immediately to the caller.

    At most one `Scheduler` instance may be running at a time across
    the whole process: calling :meth:`start` while another instance is
    already running raises `RuntimeError` rather than silently
    starting a second, competing collection loop. This is a process-
    wide invariant (tracked on the class, not per instance), because
    two concurrent monitoring loops would mean duplicate,
    interleaved collection work for no benefit.

    Usage::

        scheduler = Scheduler(monitor=Monitor(), interval_seconds=30)
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

    def __init__(self, monitor: Monitor, interval_seconds: float) -> None:
        """Create a Scheduler for a given Monitor and refresh interval.

        Args:
            monitor: The `Monitor` instance to run repeatedly. The
                Scheduler only ever calls `monitor.run()` — it never
                modifies, reconfigures, or replaces this object.
            interval_seconds: How long to sleep between the end of one
                monitoring cycle and the start of the next, in
                seconds. Must be a positive number.

        Raises:
            ValueError: If `interval_seconds` is not a positive number.
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive number.")

        self._monitor = monitor
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
        isolates every individual collector's failures internally —
        but this loop guards against it anyway (without logging or
        storing anything about the failure, per this module's
        constraints) so one unexpected exception can never silently
        kill the scheduling loop.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # The Scheduler's only interaction with Monitor:
                    # trigger one cycle. The returned snapshot is
                    # intentionally discarded — this module never
                    # stores, inspects, or forwards it.
                    self._monitor.run()
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