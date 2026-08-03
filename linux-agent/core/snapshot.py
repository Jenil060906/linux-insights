"""Snapshot module.

Defines the :class:`SnapshotManager` class: a thread-safe, in-memory
holder for exactly one snapshot at a time — typically whatever
:meth:`core.monitor.Monitor.run` most recently produced.

``SnapshotManager`` has no knowledge of, or dependency on, ``Monitor``
or ``Scheduler`` — it stores and returns plain dictionaries handed to
it, and nothing more. It performs no persistence (no database, no
disk writes), exposes no API, uses no logging framework, and performs
no analysis or prediction over what it stores. The single `print()`
call in :meth:`SnapshotManager.update_snapshot` exists purely as
developer-facing console feedback during testing — it does not change
what the method stores, returns, or how it's synchronized.
"""

import copy
import threading
from typing import Dict, Optional

# A snapshot is treated as an opaque dictionary — SnapshotManager
# never inspects or relies on any particular shape beyond what
# `get_snapshot_timestamp` documents below.
Snapshot = Dict[str, object]


class SnapshotManager:
    """Thread-safe, in-memory holder for a single, latest snapshot.

    ``SnapshotManager`` stores at most one snapshot at a time: each
    call to :meth:`update_snapshot` replaces whatever was stored
    before, if anything. All access is synchronized with a single
    `threading.Lock`, so concurrent calls from multiple threads (e.g.
    a `Scheduler`'s background thread calling `update_snapshot` while
    another thread calls `get_latest_snapshot`) are always safe.

    The stored snapshot is never exposed or mutated directly: both
    storing and reading a snapshot copy it with `copy.deepcopy`, so
    neither the caller's original object nor this manager's internal
    state can ever be mutated through the other.

    Usage::

        manager = SnapshotManager()
        manager.update_snapshot(monitor.run())
        ...
        latest = manager.get_latest_snapshot()
    """

    def __init__(self) -> None:
        """Create an empty SnapshotManager (no snapshot stored yet)."""
        self._snapshot: Optional[Snapshot] = None
        self._lock = threading.Lock()

    def update_snapshot(self, snapshot: Snapshot) -> None:
        """Store a new snapshot, replacing whatever was stored before.

        Args:
            snapshot: The snapshot dictionary to store (e.g. the
                dictionary returned by `Monitor.run()`). A deep copy
                of `snapshot` is stored, not the object itself, so any
                later change the caller makes to `snapshot` cannot
                affect what's stored here.
        """
        with self._lock:
            self._snapshot = copy.deepcopy(snapshot)

        # Developer-facing console feedback only, printed after the
        # lock is released (so the critical section stays limited to
        # the actual store). Does not print the snapshot itself.
        print("Snapshot Updated")

    def get_latest_snapshot(self) -> Optional[Snapshot]:
        """Return the most recently stored snapshot, if any.

        Returns:
            A deep copy of the latest stored snapshot, or `None` if no
            snapshot has ever been stored, or the last one was
            discarded via `clear_snapshot()`. Because the returned
            value is a deep copy, mutating it can never affect what's
            stored internally.
        """
        with self._lock:
            return self._copy_snapshot_locked()

    def has_snapshot(self) -> bool:
        """Report whether a snapshot is currently stored.

        Returns:
            `True` if a snapshot has been stored and not since
            cleared, `False` otherwise.
        """
        with self._lock:
            return self._snapshot is not None

    def clear_snapshot(self) -> None:
        """Discard the currently stored snapshot, if any.

        After this call, `has_snapshot()` returns `False` and
        `get_latest_snapshot()`/`get_snapshot_timestamp()` return
        `None`, until `update_snapshot()` is called again. Safe to
        call even if no snapshot is currently stored.
        """
        with self._lock:
            self._snapshot = None

    def get_snapshot_timestamp(self) -> Optional[str]:
        """Return the stored snapshot's timestamp, if any.

        This reads `snapshot["metadata"]["timestamp"]` from the
        stored snapshot — the shape `Monitor.run()` produces —
        rather than this class generating or tracking a timestamp of
        its own; `SnapshotManager` only reports what the snapshot
        itself already says.

        Returns:
            The timestamp string, or `None` if no snapshot is
            currently stored, or the stored snapshot has no
            `"metadata"`/`"timestamp"` field in the expected shape.
        """
        with self._lock:
            if self._snapshot is None:
                return None

            metadata = self._snapshot.get("metadata")
            if not isinstance(metadata, dict):
                return None

            timestamp = metadata.get("timestamp")
            return timestamp if isinstance(timestamp, str) else None

    def _copy_snapshot_locked(self) -> Optional[Snapshot]:
        """Return a deep copy of the stored snapshot.

        Must only be called while holding `self._lock`.

        Returns:
            A deep copy of `self._snapshot`, or `None` if nothing is
            stored.
        """
        if self._snapshot is None:
            return None
        return copy.deepcopy(self._snapshot)