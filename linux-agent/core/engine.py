"""Monitoring engine module.

Defines :class:`MonitoringEngine`, which wires the Configuration
Manager (`config.config_loader` + `config.validator`), `Monitor`,
`SnapshotManager`, and `Scheduler` into a single, cohesive production
entry point — without changing what any of those four components
themselves are responsible for.

``MonitoringEngine`` contains no configuration parsing, scheduling,
collection, or storage logic of its own. Its only job is composition:
building each collaborator, wiring them together via dependency
injection exactly as they already require (a `Scheduler` still only
ever receives a `Monitor`, a `SnapshotManager`, and an interval
through its constructor; a `Monitor` still only ever runs the
collectors it always has; a `SnapshotManager` still only ever stores
one snapshot at a time), and exposing a small facade
(`start`/`stop`/`is_running`/`get_latest_snapshot`) so a caller never
needs to construct or wire these four pieces by hand.
"""

from pathlib import Path
from typing import Optional, Union

from config.config_loader import Config, load_config
from config.validator import validate_config
from core.monitor import Monitor
from core.scheduler import Scheduler
from core.snapshot import Snapshot, SnapshotManager


class MonitoringEngine:
    """Unified monitoring engine: Configuration Manager + Monitor + Scheduler + SnapshotManager.

    Each collaborator keeps its existing, independent responsibility:

    - The Configuration Manager (`config.config_loader.load_config` /
      `config.validator.validate_config`) loads and validates
      settings — it never runs, schedules, or stores anything.
    - `Monitor` runs one full collection cycle and returns a snapshot
      — it never schedules itself or knows where its result ends up.
    - `Scheduler` repeatedly runs the `Monitor` it's given, on the
      interval it's given, and hands each successful cycle's snapshot
      to the `SnapshotManager` it's given — it never loads
      configuration or decides what that interval should be.
    - `SnapshotManager` stores exactly the latest snapshot it's handed
      — it never produces or schedules anything itself.

    `MonitoringEngine` only composes these four pieces via
    constructor/factory injection and forwards calls to them; it adds
    no monitoring behavior of its own.

    Usage::

        engine = MonitoringEngine.bootstrap()  # loads + validates config.yaml
        engine.start()
        ...
        engine.stop()
        latest = engine.get_latest_snapshot()
    """

    def __init__(
        self,
        monitor: Monitor,
        snapshot_manager: SnapshotManager,
        scheduler: Scheduler,
        config: Optional[Config] = None,
    ) -> None:
        """Compose an engine from already-constructed collaborators.

        Plain constructor injection — the engine never builds a
        `Monitor`, `SnapshotManager`, or `Scheduler` here, so tests
        (or alternative bootstrapping strategies) can supply their
        own. Use :meth:`from_config` or :meth:`bootstrap` to build a
        standard, configuration-driven engine instead of assembling
        these three by hand.

        Args:
            monitor: The `Monitor` the `Scheduler` will run each
                cycle.
            snapshot_manager: The `SnapshotManager` each cycle's
                snapshot is delivered to. Must be the same instance
                `scheduler` was constructed with.
            scheduler: The `Scheduler` driving the monitoring loop.
                Must already be constructed with `monitor` and
                `snapshot_manager` injected.
            config: The `Config` this engine was built from, if any —
                kept only so callers can read configuration values
                (e.g. `agent.id`) back out via :attr:`config` without
                loading the file a second time. Purely informational:
                the engine never reads from it itself after
                construction. `None` when an engine is composed
                directly from collaborators without a `Config`.
        """
        self._monitor = monitor
        self._snapshot_manager = snapshot_manager
        self._scheduler = scheduler
        self._config = config

    @classmethod
    def from_config(cls, config: Config) -> "MonitoringEngine":
        """Build a fully-wired engine from an already-validated `Config`.

        Reads only `scheduler.refresh_interval` from `config` — this
        is where "the Scheduler receives configuration through
        dependency injection" actually happens: the interval is read
        once, here, and passed into `Scheduler`'s constructor, rather
        than the `Scheduler` ever reading configuration itself.

        Args:
            config: A `Config` that has already been passed to
                `config.validator.validate_config` without raising.
                This method does not validate it again.

        Returns:
            A `MonitoringEngine` with a fresh `Monitor`,
            `SnapshotManager`, and `Scheduler` — the `Scheduler`
            already wired to that `Monitor` and `SnapshotManager`,
            using the configured refresh interval.
        """
        monitor = Monitor()
        snapshot_manager = SnapshotManager()
        scheduler = Scheduler(
            monitor=monitor,
            snapshot_manager=snapshot_manager,
            interval_seconds=config.get("scheduler")["refresh_interval"],
        )
        return cls(
            monitor=monitor,
            snapshot_manager=snapshot_manager,
            scheduler=scheduler,
            config=config,
        )

    @classmethod
    def bootstrap(cls, config_path: Optional[Union[str, Path]] = None) -> "MonitoringEngine":
        """Load, validate, and build a fully-wired engine in one step.

        This is the standard way to obtain a `MonitoringEngine` in
        production: it performs the whole pipeline —
        Configuration Manager loads settings, validates them, and the
        engine is composed from the result — without the caller
        needing to touch `config_loader`/`validator` directly.

        Args:
            config_path: Path to the configuration file, forwarded to
                `config.config_loader.load_config`. Defaults to
                `config.yaml` at the agent root when not given.

        Returns:
            A fully-wired `MonitoringEngine`, as in :meth:`from_config`.

        Raises:
            config.config_loader.ConfigParseError: If the
                configuration file exists but isn't valid YAML, or
                isn't a mapping at the top level.
            config.validator.ValidationError: If the loaded
                configuration is missing a mandatory value or contains
                an invalid one (see `config.validator.validate_config`).
        """
        config = load_config(config_path)
        validate_config(config)
        return cls.from_config(config)

    def start(self) -> None:
        """Start the monitoring loop.

        Delegates directly to `Scheduler.start`. See that method for
        the exact starting semantics (background thread, single
        active scheduler process-wide, etc.) — this call adds no
        behavior of its own.
        """
        self._scheduler.start()

    def stop(self) -> None:
        """Stop the monitoring loop and wait for it to fully exit.

        Delegates directly to `Scheduler.stop`.
        """
        self._scheduler.stop()

    def is_running(self) -> bool:
        """Report whether the monitoring loop is currently active.

        Delegates directly to `Scheduler.is_running`.

        Returns:
            `True` if the monitoring loop is currently running.
        """
        return self._scheduler.is_running()

    def get_latest_snapshot(self) -> Optional[Snapshot]:
        """Return the most recently stored snapshot, if any.

        Delegates directly to `SnapshotManager.get_latest_snapshot`.

        Returns:
            A deep copy of the latest snapshot, or `None` if no
            monitoring cycle has completed yet.
        """
        return self._snapshot_manager.get_latest_snapshot()

    def get_snapshot_timestamp(self) -> Optional[str]:
        """Return the latest stored snapshot's timestamp, if any.

        Delegates directly to `SnapshotManager.get_snapshot_timestamp`.

        Returns:
            The timestamp string, or `None` if no snapshot is stored.
        """
        return self._snapshot_manager.get_snapshot_timestamp()

    @property
    def monitor(self) -> Monitor:
        """The `Monitor` this engine's `Scheduler` runs each cycle."""
        return self._monitor

    @property
    def snapshot_manager(self) -> SnapshotManager:
        """The `SnapshotManager` this engine's `Scheduler` updates each cycle."""
        return self._snapshot_manager

    @property
    def scheduler(self) -> Scheduler:
        """The `Scheduler` driving this engine's monitoring loop."""
        return self._scheduler

    @property
    def config(self) -> Optional[Config]:
        """The `Config` this engine was built from, if any.

        `None` if this engine was composed directly from collaborators
        (via the constructor) rather than via :meth:`from_config` or
        :meth:`bootstrap`.
        """
        return self._config