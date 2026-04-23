"""Local environment-file helpers for operator-friendly runtime startup."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILENAMES = (".env", ".env.local")


def build_runtime_environ(
    environ: Mapping[str, str] | None = None,
    *,
    config_path: Path | None = None,
) -> dict[str, str]:
    """Return an environment map that includes local .env overlays.

    Precedence:
    1. Actual process/test environment
    2. config directory .env.local / .env
    3. repo root .env.local / .env
    """

    incoming = dict(os.environ if environ is None else environ)
    file_values: dict[str, str] = {}
    for env_path in _candidate_env_files(config_path):
        file_values.update(_read_env_file(env_path))

    runtime = dict(file_values)
    runtime.update(incoming)
    return runtime


def _candidate_env_files(config_path: Path | None) -> tuple[Path, ...]:
    directories: list[Path] = [REPO_ROOT]
    if config_path is not None:
        config_dir = config_path.resolve().parent
        if config_dir not in directories:
            directories.append(config_dir)

    paths: list[Path] = []
    seen: set[Path] = set()
    for directory in directories:
        for filename in ENV_FILENAMES:
            path = directory / filename
            if path in seen or not path.exists() or not path.is_file():
                continue
            seen.add(path)
            paths.append(path)
    return tuple(paths)


def _read_env_file(path: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = key.strip()
        if not normalized_key:
            continue
        payload[normalized_key] = _strip_quotes(value.strip())
    return payload


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
