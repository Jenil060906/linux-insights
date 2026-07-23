"""Linux Agent — entry point for the Linux Insight host-side metrics collector.

This module is currently a placeholder. It will be responsible for starting
the agent process, loading configuration, and running the collector loop
once those pieces are implemented.
"""


"""
Temporary test file for the System Information Collector.
"""

from collectors.system_info import collect_system_info


def main():
    info = collect_system_info()

    print("========== Linux Insight ==========")

    for key, value in info.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()