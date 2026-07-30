"""Monitor module.

Defines the :class:`Monitor` class, which orchestrates every collector
in ``collectors/`` into a single, unified snapshot of the host.

``Monitor`` contains no collection logic of its own — it imports and
calls each collector's existing, independent entry-point function
unchanged, in a fixed order, and assembles their individual outputs
into one dictionary alongside snapshot metadata and a monitoring
summary. It deliberately does not implement scheduling, persistence,
caching, an API, logging, or any predictive/analysis logic: it runs
exactly one monitoring cycle per call to :meth:`Monitor.run` and
returns the result, leaving everything else to other layers.
"""

import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Tuple

from collectors.cpu import collect_cpu_info
from collectors.disk import collect_disk_info
from collectors.memory import collect_memory_info
from collectors.network import collect_network_info
from collectors.process import collect_process_info
from collectors.system_info import collect_system_info

# A collector entry point is a zero-argument callable returning the
# collector's own standard envelope dictionary (at minimum a
# "status" key — see each collector module for its exact shape).
CollectorFunction = Callable[[], Dict[str, object]]


class Monitor:
    """Orchestrates all Linux Insight collectors into one host snapshot.

    ``Monitor`` runs each registered collector in a fixed order,
    tolerates any individual collector failing — whether by returning
    a non-"success" status or by raising an unhandled exception —
    without that stopping the remaining collectors from running, and
    combines every result into a single snapshot dictionary.

    Usage::

        snapshot = Monitor().run()

    The class holds no mutable instance state between calls; each
    call to :meth:`run` performs one independent, self-contained
    monitoring cycle.
    """

    # Collectors to run, in the fixed order used throughout this
    # project's documentation: System -> CPU -> Memory -> Disk ->
    # Network -> Process. Each entry pairs the stable name a
    # collector is reported under (in the summary and the
    # "collectors" section) with its public, zero-argument entry
    # point. Collector modules themselves are never modified here —
    # this list only references their existing public functions.
    _COLLECTORS: Tuple[Tuple[str, CollectorFunction], ...] = (
        ("system_info", collect_system_info),
        ("cpu", collect_cpu_info),
        ("memory", collect_memory_info),
        ("disk", collect_disk_info),
        ("network", collect_network_info),
        ("process", collect_process_info),
    )

    def run(self) -> Dict[str, object]:
        """Run one full monitoring cycle across every registered collector.

        Collectors are executed sequentially, in the fixed order
        defined by :attr:`_COLLECTORS`. The total wall-clock duration
        of the whole cycle is measured with a monotonic clock (immune
        to system-clock adjustments mid-run), independently of the
        wall-clock timestamp recorded for the snapshot itself.

        Returns:
            A dictionary shaped like::

                {
                    "metadata": {
                        "timestamp": "2026-07-27T12:00:00+00:00",
                        "execution_time_seconds": 0.42,
                    },
                    "summary": {
                        "overall_status": "success",
                        "total_collectors": 6,
                        "successful_collectors": [
                            "system_info", "cpu", "memory",
                            "disk", "network", "process",
                        ],
                        "failed_collectors": [],
                    },
                    "monitoring": {
                        "status": "success",
                        "execution_time": 0.42,
                        "successful_collectors": 6,
                        "failed_collectors": 0,
                        "total_collectors": 6,
                    },
                    "collectors": {
                        "system_info": {...collector's own envelope...},
                        "cpu": {...},
                        "memory": {...},
                        "disk": {...},
                        "network": {...},
                        "process": {...},
                    },
                }

            "metadata" and "summary" are unchanged from earlier
            versions of this snapshot shape (existing keys are never
            renamed or removed). "monitoring" is an additional,
            self-contained summary of the same cycle aimed at callers
            that want plain counts and a short field name for elapsed
            time, rather than "summary"'s list-of-names form — the two
            sections describe the same run and are always consistent
            with each other.

            "execution_time_seconds"/"execution_time" both cover the
            entire cycle (all six collectors), not any single one.
            "overall_status"/"monitoring.status" are "success" only if
            every collector reported its own "success" status; if one
            or more did not (whether by returning a different status
            or by raising an exception), both read "partial_success",
            and those collectors' names appear in
            "summary.failed_collectors".
        """
        cycle_start = time.monotonic()

        collector_results: Dict[str, Dict[str, object]] = {}
        successful_collectors: List[str] = []
        failed_collectors: List[str] = []

        for name, collector_function in self._COLLECTORS:
            result = self._run_collector(name, collector_function)
            collector_results[name] = result

            if self._collector_succeeded(result):
                successful_collectors.append(name)
            else:
                failed_collectors.append(name)

        execution_time_seconds = time.monotonic() - cycle_start
        overall_status = "success" if not failed_collectors else "partial_success"
        total_collectors = len(self._COLLECTORS)

        return {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_time_seconds": execution_time_seconds,
            },
            "summary": {
                "overall_status": overall_status,
                "total_collectors": total_collectors,
                "successful_collectors": successful_collectors,
                "failed_collectors": failed_collectors,
            },
            # Compact, count-based counterpart to "summary" above,
            # added for callers that just want the headline numbers
            # (e.g. a quick health check) without parsing name lists.
            "monitoring": {
                "status": overall_status,
                "execution_time": execution_time_seconds,
                "successful_collectors": len(successful_collectors),
                "failed_collectors": len(failed_collectors),
                "total_collectors": total_collectors,
            },
            "collectors": collector_results,
        }

    @staticmethod
    def _run_collector(
        name: str, collector_function: CollectorFunction
    ) -> Dict[str, object]:
        """Run a single collector, converting any exception into a result.

        Every collector already handles its own internal failures
        gracefully — falling back to "Unknown"/empty values and
        reporting them in its own "errors" list rather than raising.
        This guard exists only for whatever a collector's own error
        handling didn't anticipate (e.g. a bug, an unforeseen
        exception type), so that one broken collector can never take
        down the rest of the monitoring cycle.

        Args:
            name: The stable name this collector is reported under in
                the summary and the "collectors" section.
            collector_function: The collector's public, zero-argument
                entry-point function.

        Returns:
            Whatever the collector itself returns, completely
            unchanged, if it returns normally. If it raises instead, a
            minimal envelope is synthesized in the same general shape
            collectors use for themselves ("collector", "status",
            "data", "errors"), so callers never need to special-case a
            raised exception versus a returned failure.
        """
        try:
            return collector_function()
        except Exception as error:  # noqa: BLE001 - must not abort the cycle
            return {
                "collector": name,
                "status": "error",
                "data": {},
                "errors": [
                    f"Collector '{name}' raised an unexpected exception: {error}"
                ],
            }

    @staticmethod
    def _collector_succeeded(result: Dict[str, object]) -> bool:
        """Determine whether a collector's result counts as successful.

        A collector counts as successful only if it reported its own
        ``"status": "success"``. Both an unsupported-platform response
        (``"status": "unsupported_platform"``) and a synthesized
        failure envelope from :meth:`_run_collector`
        (``"status": "error"``) count as not successful for the
        monitoring summary, even though neither one raised past this
        class.

        Args:
            result: The dictionary a collector (or
                :meth:`_run_collector`) returned.

        Returns:
            ``True`` if the collector's own reported status is
            ``"success"``.
        """
        return result.get("status") == "success"