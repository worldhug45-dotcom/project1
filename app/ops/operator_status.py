"""Shared operator status snapshot helpers for CLI and web surfaces."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.infrastructure.local_env import build_runtime_environ
from app.infrastructure.settings import load_settings, resolve_keyword_override_path
from app.ops.observation import CollectObservationRecord, load_observation_history


DEFAULT_LAUNCHERS = {
    "status_launcher": "scripts/run_status.ps1",
    "collect_launcher": "scripts/run_collect.ps1",
    "export_launcher": "scripts/run_export.ps1",
    "observe_launcher": "scripts/run_observe.ps1",
}


@dataclass(frozen=True, slots=True)
class OperatorArtifactSnapshot:
    """Recent operator artifact entry derived from the current filesystem."""

    group: str
    kind: str
    name: str
    path: str
    created_at: str
    status: str
    relative_path: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorStatusSnapshot:
    """Read-only snapshot that powers operator-facing status surfaces."""

    current_paths: dict[str, str]
    recent_collect: dict[str, Any] | None
    recent_export: dict[str, Any] | None
    recent_observe: dict[str, Any] | None
    launchers: dict[str, str]
    updated_at: str | None = None
    artifacts: tuple[OperatorArtifactSnapshot, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_operator_status_snapshot(
    *,
    config_path: Path,
    history_path: Path,
    raw_output_dir: Path,
    log_path: Path,
    state_path: Path,
    environ: dict[str, str] | None = None,
) -> OperatorStatusSnapshot:
    runtime_environ = build_runtime_environ(environ, config_path=config_path)
    settings = load_settings(
        config_path,
        cli_overrides={"action": "export"},
        environ=runtime_environ,
    )
    keyword_override_path = resolve_keyword_override_path(config_path, runtime_environ)
    latest_xlsx = latest_file(settings.export.output_dir, "*.xlsx")
    latest_raw_jsonl = latest_file(raw_output_dir, "*.jsonl")
    latest_observation = latest_observation_record(history_path)
    manual_state = load_manual_state(state_path)

    updated_at = manual_state.get("updated_at")
    if not isinstance(updated_at, str):
        updated_at = None

    return OperatorStatusSnapshot(
        current_paths={
            "config_path": str(config_path),
            "keyword_override_path": display_path(keyword_override_path),
            "sqlite_db_path": str(settings.storage.database_path),
            "export_output_dir": str(settings.export.output_dir),
            "current_source_mode": settings.runtime.source_mode,
            "latest_exported_file_path": display_path(latest_xlsx),
            "observation_history_path": str(history_path),
            "observation_report_path": str(log_path),
            "observation_raw_jsonl_dir": str(raw_output_dir),
            "state_path": str(state_path),
        },
        artifacts=build_recent_artifacts(
            export_output_dir=settings.export.output_dir,
            raw_output_dir=raw_output_dir,
            observation_report_path=log_path,
        ),
        recent_collect=recent_collect_state(manual_state, latest_observation),
        recent_export=recent_export_state(manual_state, latest_xlsx),
        recent_observe=recent_observe_state(
            manual_state,
            latest_observation,
            latest_raw_jsonl,
        ),
        launchers=dict(DEFAULT_LAUNCHERS),
        updated_at=updated_at,
    )


def load_manual_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"actions": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"actions": {}}
    actions = raw.get("actions")
    if not isinstance(actions, dict):
        raw["actions"] = {}
    return raw


def persist_action_state(path: Path, action: str, payload: dict[str, Any]) -> None:
    state = load_manual_state(path)
    actions = state.setdefault("actions", {})
    actions[action] = payload
    state["updated_at"] = now_isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_observation_record(path: Path) -> CollectObservationRecord | None:
    records = load_observation_history(path)
    if not records:
        return None
    return max(records, key=lambda item: (item.observed_on, item.run_id))


def latest_file(directory: Path, pattern: str) -> Path | None:
    recent = recent_files(directory, pattern, limit=1)
    if not recent:
        return None
    return recent[0]


def recent_files(directory: Path, pattern: str, *, limit: int = 5) -> tuple[Path, ...]:
    if not directory.exists():
        return ()
    files = sorted(
        (path for path in directory.glob(pattern) if path.is_file()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return tuple(files[:limit])


def build_recent_artifacts(
    *,
    export_output_dir: Path,
    raw_output_dir: Path,
    observation_report_path: Path,
) -> tuple[OperatorArtifactSnapshot, ...]:
    artifacts: list[OperatorArtifactSnapshot] = []

    for path in recent_files(export_output_dir, "*.xlsx", limit=5):
        artifacts.append(
            OperatorArtifactSnapshot(
                group="export",
                kind="export_result",
                name=path.name,
                path=str(path),
                created_at=mtime_isoformat(path),
                status="available",
                relative_path=_relative_artifact_path(path, export_output_dir),
            )
        )

    if observation_report_path.exists() and observation_report_path.is_file():
        artifacts.append(
            OperatorArtifactSnapshot(
                group="observation",
                kind="observation_report",
                name=observation_report_path.name,
                path=str(observation_report_path),
                created_at=mtime_isoformat(observation_report_path),
                status="available",
            )
        )

    for path in recent_files(raw_output_dir, "*.jsonl", limit=5):
        artifacts.append(
            OperatorArtifactSnapshot(
                group="observation",
                kind="observation_raw",
                name=path.name,
                path=str(path),
                created_at=mtime_isoformat(path),
                status="available",
                relative_path=_relative_artifact_path(path, raw_output_dir),
            )
        )

    return tuple(artifacts)


def recent_collect_state(
    manual_state: dict[str, Any],
    latest_observation: CollectObservationRecord | None,
) -> dict[str, Any] | None:
    actions = manual_state.get("actions", {})
    state = actions.get("collect")
    if isinstance(state, dict):
        return state
    if latest_observation is None:
        return None
    return {
        "status": latest_observation.status,
        "recorded_at": latest_observation.observed_on,
        "run_id": latest_observation.run_id,
        "fetched_count": latest_observation.fetched_count,
        "saved_count": latest_observation.saved_count,
        "skipped_count": latest_observation.skipped_count,
        "error_count": latest_observation.error_count,
        "source": "observation_history_fallback",
    }


def recent_export_state(
    manual_state: dict[str, Any],
    latest_xlsx: Path | None,
) -> dict[str, Any] | None:
    actions = manual_state.get("actions", {})
    state = actions.get("export")
    if isinstance(state, dict):
        return state
    if latest_xlsx is None:
        return None
    return {
        "status": "available",
        "recorded_at": mtime_isoformat(latest_xlsx),
        "exported_file_count": 1,
        "exported_file_path": str(latest_xlsx),
        "source": "filesystem_fallback",
    }


def recent_observe_state(
    manual_state: dict[str, Any],
    latest_observation: CollectObservationRecord | None,
    latest_raw_jsonl: Path | None,
) -> dict[str, Any] | None:
    actions = manual_state.get("actions", {})
    state = actions.get("observe")
    if isinstance(state, dict):
        return state
    if latest_observation is None and latest_raw_jsonl is None:
        return None
    payload: dict[str, Any] = {
        "status": (latest_observation.status if latest_observation is not None else "available"),
        "recorded_at": (
            latest_observation.observed_on
            if latest_observation is not None
            else mtime_isoformat(latest_raw_jsonl)
        ),
        "source": "observation_history_fallback",
        "latest_raw_jsonl_path": display_path(latest_raw_jsonl),
    }
    if latest_observation is not None:
        payload.update(
            {
                "run_id": latest_observation.run_id,
                "observed_on": latest_observation.observed_on,
                "fetched_count": latest_observation.fetched_count,
                "saved_count": latest_observation.saved_count,
                "skipped_count": latest_observation.skipped_count,
                "error_count": latest_observation.error_count,
            }
        )
    return payload


def display_path(path: Path | None) -> str:
    if path is None:
        return "not available"
    return str(path)


def mtime_isoformat(path: Path | None) -> str:
    if path is None:
        return "not available"
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()


def now_isoformat() -> str:
    return datetime.now(UTC).isoformat()


def _relative_artifact_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name
