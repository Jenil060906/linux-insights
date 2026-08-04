"""Configuration loader.

Reads `config.yaml` from disk and parses it into a `Config` object.
This module is responsible only for *reading* configuration — it does
not validate field values, or start, construct, or configure any
other part of the agent (no `Monitor`, `Scheduler`, or
`SnapshotManager` is touched here). Its one exception is
`agent.hostname`: since that field is optional (unlike `agent.id`,
which stays mandatory — see `config.validator`), a blank or missing
hostname is filled in with `socket.gethostname()` at load time, so
every `Config` this module returns always carries a usable hostname.
This is a loading-time convenience, not validation — it never raises,
and it never touches any other field.
"""

import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Location of the project's configuration file: `config.yaml` at the
# agent root (one directory up from this `config/` package).
DEFAULT_CONFIG_PATH: Path = Path(__file__).resolve().parent.parent / "config.yaml"


class ConfigError(Exception):
    """Base class for errors raised while loading configuration."""


class ConfigParseError(ConfigError):
    """Raised when a configuration file exists but cannot be parsed.

    Covers both invalid YAML syntax and YAML that parses successfully
    but is not a mapping at the top level.
    """


@dataclass(frozen=True)
class Config:
    """Read-only wrapper around parsed configuration data.

    Holds exactly what was parsed from `config.yaml`, unmodified and
    unvalidated — callers are responsible for interpreting and
    validating the values they read from it.
    """

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the top-level value for `key`, or `default` if absent.

        Args:
            key: Top-level configuration key (e.g. `"agent"`,
                `"scheduler"`, `"monitoring"`).
            default: Value to return if `key` is not present.

        Returns:
            The raw value stored under `key`, or `default`.
        """
        return self.data.get(key, default)


def load_config(path: Optional[Union[str, Path]] = None) -> Config:
    """Read and parse a YAML configuration file into a `Config`.

    Args:
        path: Path to the configuration file. Defaults to
            `DEFAULT_CONFIG_PATH` (`config.yaml` at the agent root)
            when not given.

    Returns:
        A `Config` wrapping the parsed configuration data, with
        `agent.hostname` filled in via `socket.gethostname()` if it
        was blank or missing (see `_apply_hostname_default`). If the
        file does not exist, an empty `Config` is returned rather than
        raising, so a missing configuration file does not by itself
        prevent the caller from proceeding.

    Raises:
        ConfigParseError: If the file exists but its contents are not
            valid YAML, or parse to something other than a mapping
            (or `null`/empty) at the top level.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH

    if not config_path.is_file():
        return Config({})

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            raw_data = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        raise ConfigParseError(
            f"Configuration file '{config_path}' is not valid YAML: {exc}"
        ) from exc

    if raw_data is None:
        raw_data = {}

    if not isinstance(raw_data, dict):
        raise ConfigParseError(
            f"Configuration file '{config_path}' must contain a mapping "
            f"at the top level, got {type(raw_data).__name__} instead."
        )

    _apply_hostname_default(raw_data)

    return Config(raw_data)


def _apply_hostname_default(raw_data: Dict[str, Any]) -> None:
    """Fill in `agent.hostname` with `socket.gethostname()` if it's blank.

    `agent.hostname` is optional: an operator may set it explicitly to
    override detection, or leave it blank/absent to have it detected
    automatically. This only fills in a *missing or blank* value —
    an explicitly-set hostname is never overwritten. Mutates
    `raw_data` in place; has no effect if `raw_data` has no `"agent"`
    mapping (a missing `agent` section is a `agent.id` problem for
    `config.validator` to report, not something this function should
    paper over).

    Args:
        raw_data: The freshly-parsed configuration mapping, before it
            is wrapped in a `Config`.
    """
    agent_section = raw_data.get("agent")
    if not isinstance(agent_section, dict):
        return

    hostname = agent_section.get("hostname")
    if not isinstance(hostname, str) or not hostname.strip():
        agent_section["hostname"] = socket.gethostname()