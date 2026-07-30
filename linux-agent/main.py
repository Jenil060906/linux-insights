"""Temporary manual test script for the Monitor orchestrator.

This is **not** part of the permanent Linux Insight agent — it exists
only so `core.monitor.Monitor` can be exercised end-to-end from the
command line during development: run exactly one monitoring cycle,
print the resulting snapshot as formatted JSON, and print a short
human-readable summary. It has no scheduler, no API, no storage, and
no logging framework, and contains no loops of any kind: it runs once
and exits.
"""

import json

from core.monitor import Monitor

_HEADER = (
    "=====================================\n"
    "Linux Insight - Monitor Test\n"
    "====================================="
)


def main() -> None:
    """Run a single Monitor cycle and print the snapshot plus a summary.

    Any exception raised by `Monitor` itself (as opposed to a single
    collector, which `Monitor.run()` already isolates internally) is
    caught here and reported as a short, informative message instead
    of letting a raw traceback surface.
    """
    print(_HEADER)

    try:
        monitor = Monitor()
        snapshot = monitor.run()
    except Exception as error:  # noqa: BLE001 - top-level test entry point
        print(f"Monitor failed to complete a monitoring cycle: {error}")
        return

    # ensure_ascii=False so any non-ASCII characters in the snapshot
    # (e.g. from a hostname or a process name) print as-is rather than
    # as \uXXXX escape sequences.
    print(json.dumps(snapshot, indent=4, ensure_ascii=False))

    _print_summary(snapshot)


def _print_summary(snapshot: dict) -> None:
    """Print a short, human-readable summary of a Monitor snapshot.

    Args:
        snapshot: The dictionary returned by `Monitor.run()`, expected
            to contain "metadata" and "summary" sections.
    """
    metadata = snapshot.get("metadata", {})
    summary = snapshot.get("summary", {})

    successful_collectors = summary.get("successful_collectors", [])
    failed_collectors = summary.get("failed_collectors", [])

    print()
    print(f"Snapshot Timestamp: {metadata.get('timestamp', 'Unknown')}")
    print(f"Overall Status: {summary.get('overall_status', 'Unknown')}")
    print(
        "Execution Time: "
        f"{metadata.get('execution_time_seconds', 'Unknown')} seconds"
    )
    print(f"Successful Collectors: {', '.join(successful_collectors) or 'None'}")
    print(f"Failed Collectors: {', '.join(failed_collectors) or 'None'}")


if __name__ == "__main__":
    main()
