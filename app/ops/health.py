"""Read-only health snapshot helpers for operator-facing web endpoints."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.infrastructure.settings import AppSettings, ConfigurationError, load_settings
from app.ops.operator_status import now_isoformat


@dataclass(frozen=True, slots=True)
class OperatorHealthSnapshot:
    """Minimal read-only health payload for web and container checks."""

    status: str
    app_name: str
    server_time: str
    config_path: str
    sqlite_db_path: str
    export_output_dir: str
    settings_loaded: bool
    state_file_accessible: bool
    observation_history_exists: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_operator_health_snapshot(
    *,
    config_path: Path,
    history_path: Path,
    state_path: Path,
) -> OperatorHealthSnapshot:
    app_name = AppSettings().name
    sqlite_db_path = "not available"
    export_output_dir = "not available"
    settings_loaded = False
    loaded_settings = None

    try:
        loaded_settings = load_settings(config_path, cli_overrides={"action": "export"})
    except ConfigurationError:
        pass
    else:
        settings_loaded = True
        if loaded_settings is not None:
            app_name = loaded_settings.app.name
            sqlite_db_path = str(loaded_settings.storage.database_path)
            export_output_dir = str(loaded_settings.export.output_dir)

    state_file_accessible = _is_state_file_accessible(state_path)
    observation_history_exists = history_path.exists() and history_path.is_file()

    if not settings_loaded:
        status = "error"
    elif state_file_accessible and observation_history_exists:
        status = "ok"
    else:
        status = "degraded"

    return OperatorHealthSnapshot(
        status=status,
        app_name=app_name,
        server_time=now_isoformat(),
        config_path=str(config_path),
        sqlite_db_path=sqlite_db_path,
        export_output_dir=export_output_dir,
        settings_loaded=settings_loaded,
        state_file_accessible=state_file_accessible,
        observation_history_exists=observation_history_exists,
    )


def build_unavailable_health_snapshot(config_path: Path) -> OperatorHealthSnapshot:
    """Fallback health payload when endpoint-level failures occur."""

    return OperatorHealthSnapshot(
        status="error",
        app_name=AppSettings().name,
        server_time=now_isoformat(),
        config_path=str(config_path),
        sqlite_db_path="not available",
        export_output_dir="not available",
        settings_loaded=False,
        state_file_accessible=False,
        observation_history_exists=False,
    )


def _is_state_file_accessible(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(raw, dict)
