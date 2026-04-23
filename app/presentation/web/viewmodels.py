"""View-model builders for the operator dashboard."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.application import (
    CollectControlState,
    ExportControlState,
    ObserveControlState,
)
from app.ops import OperatorStatusSnapshot


PATH_LABELS = (
    ("config_path", "Config path"),
    ("keyword_override_path", "Keywords override"),
    ("sqlite_db_path", "SQLite DB"),
    ("export_output_dir", "Export output"),
    ("current_source_mode", "Current source mode"),
    ("latest_exported_file_path", "Latest exported file"),
    ("observation_history_path", "Observation history"),
    ("observation_report_path", "Observation report"),
    ("observation_raw_jsonl_dir", "Observation raw JSONL"),
)

SUMMARY_LABELS = {
    "status": "Status",
    "recorded_at": "Recorded at",
    "run_id": "Run ID",
    "observed_on": "Observed on",
    "run_summary_status": "Run summary",
    "source_mode": "Source mode",
    "fetched_count": "Fetched",
    "saved_count": "Saved",
    "skipped_count": "Skipped",
    "error_count": "Errors",
    "error_message": "Error",
    "exported_file_count": "Exported files",
    "latest_raw_jsonl_path": "Latest raw JSONL",
}

ACTION_TITLES = {
    "collect": "Recent Collect",
    "export": "Recent Export",
    "observe": "Recent Observe",
}


def build_dashboard_view_model(
    snapshot: OperatorStatusSnapshot,
    *,
    collect_control: CollectControlState,
    export_control: ExportControlState,
    observe_control: ObserveControlState,
) -> dict[str, Any]:
    return {
        "status": "ready",
        "dashboard_title": "Crawling Dashboard",
        "dashboard_subtitle": (
            "The web operator dashboard reuses the CLI engine, exposes status/health/keywords, "
            "and keeps collect, export, and observe available from one operator surface."
        ),
        "read_only": False,
        "updated_at": snapshot.updated_at or "not available",
        "paths": [
            {
                "key": key,
                "label": label,
                "value": snapshot.current_paths.get(key, "not available"),
            }
            for key, label in PATH_LABELS
        ],
        "artifacts": _build_artifact_items(snapshot.artifacts),
        "recent_actions": (
            _build_action_panel("collect", snapshot.recent_collect),
            _build_action_panel("export", snapshot.recent_export),
            _build_action_panel("observe", snapshot.recent_observe),
        ),
        "launchers": [
            {"label": _humanize_launcher(key), "value": value}
            for key, value in snapshot.launchers.items()
        ],
        "collect_control": _build_collect_control(collect_control),
        "export_control": _build_export_control(export_control),
        "observe_control": _build_observe_control(observe_control),
    }


def build_dashboard_error_view_model(error_message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "dashboard_title": "Crawling Dashboard",
        "dashboard_subtitle": (
            "The web shell is running, but the current operator snapshot could not be loaded."
        ),
        "read_only": False,
        "updated_at": "not available",
        "error_message": error_message,
        "paths": [],
        "artifacts": [],
        "recent_actions": (
            _empty_action_panel("collect"),
            _empty_action_panel("export"),
            _empty_action_panel("observe"),
        ),
        "launchers": [],
        "collect_control": _build_collect_control(
            CollectControlState(
                status="failed",
                fetched_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=0,
                db_path="not available",
                recorded_at="not available",
                error_message=error_message,
            )
        ),
        "export_control": _build_export_control(
            ExportControlState(
                status="failed",
                exported_file_count=0,
                exported_file_path="not available",
                export_output_dir="not available",
                recorded_at="not available",
                error_message=error_message,
            )
        ),
        "observe_control": _build_observe_control(
            ObserveControlState(
                status="failed",
                run_id="not available",
                observed_on="not available",
                fetched_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=0,
                observation_history_path="not available",
                observation_report_path="not available",
                latest_raw_jsonl_path="not available",
                recorded_at="not available",
                error_message=error_message,
            )
        ),
    }


def _build_action_panel(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return _empty_action_panel(action)

    items: list[dict[str, str]] = []
    for key in (
        "status",
        "recorded_at",
        "run_id",
        "observed_on",
        "run_summary_status",
        "source_mode",
        "fetched_count",
        "saved_count",
        "skipped_count",
        "error_count",
        "error_message",
        "exported_file_count",
        "latest_raw_jsonl_path",
    ):
        value = payload.get(key)
        if value in (None, ""):
            continue
        items.append({"label": SUMMARY_LABELS[key], "value": str(value)})

    exported_files = payload.get("exported_files")
    if isinstance(exported_files, list):
        for exported_file in exported_files:
            items.append({"label": "Exported file", "value": str(exported_file)})

    exported_file_path = payload.get("exported_file_path")
    if exported_file_path:
        items.append({"label": "Exported file", "value": str(exported_file_path)})

    return {
        "key": action,
        "title": ACTION_TITLES[action],
        "status": str(payload.get("status", "unknown")),
        "items": items or [{"label": "Status", "value": "not available"}],
    }


def _empty_action_panel(action: str) -> dict[str, Any]:
    return {
        "key": action,
        "title": ACTION_TITLES[action],
        "status": "not_available",
        "items": [{"label": "Status", "value": "not available"}],
    }


def _build_collect_control(state: CollectControlState) -> dict[str, Any]:
    return {
        "status": state.status,
        "recorded_at": state.recorded_at,
        "source_mode": state.source_mode,
        "error_message": state.error_message,
        "items": [
            {"label": "Status", "value": state.status},
            {"label": "Fetched", "value": str(state.fetched_count)},
            {"label": "Saved", "value": str(state.saved_count)},
            {"label": "Skipped", "value": str(state.skipped_count)},
            {"label": "Errors", "value": str(state.error_count)},
            {"label": "DB Path", "value": state.db_path},
        ],
    }


def _build_export_control(state: ExportControlState) -> dict[str, Any]:
    return {
        "status": state.status,
        "recorded_at": state.recorded_at,
        "error_message": state.error_message,
        "items": [
            {"label": "Status", "value": state.status},
            {"label": "Exported files", "value": str(state.exported_file_count)},
            {"label": "Exported file path", "value": state.exported_file_path},
            {"label": "Export output dir", "value": state.export_output_dir},
        ],
    }


def _build_observe_control(state: ObserveControlState) -> dict[str, Any]:
    return {
        "status": state.status,
        "recorded_at": state.recorded_at,
        "error_message": state.error_message,
        "items": [
            {"label": "Status", "value": state.status},
            {"label": "Run ID", "value": state.run_id},
            {"label": "Observed on", "value": state.observed_on},
            {"label": "Fetched", "value": str(state.fetched_count)},
            {"label": "Saved", "value": str(state.saved_count)},
            {"label": "Skipped", "value": str(state.skipped_count)},
            {"label": "Errors", "value": str(state.error_count)},
            {"label": "Observation history", "value": state.observation_history_path},
            {"label": "Observation report", "value": state.observation_report_path},
            {"label": "Latest raw JSONL", "value": state.latest_raw_jsonl_path},
        ],
    }


def _humanize_launcher(value: str) -> str:
    return value.replace("_", " ").title()


def _build_artifact_items(items: tuple[Any, ...]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for item in items:
        artifact = {
            "group": item.group,
            "kind": item.kind,
            "name": item.name,
            "path": item.path,
            "created_at": item.created_at,
            "status": item.status,
            "open_url": _artifact_open_url(item),
            "download_url": _artifact_download_url(item),
        }
        payload.append(artifact)
    return payload


def _artifact_open_url(item: Any) -> str | None:
    if item.kind == "export_result" and item.relative_path:
        return f"/artifacts/export/{quote(item.relative_path)}"
    if item.kind == "observation_raw" and item.relative_path:
        return f"/artifacts/raw/{quote(item.relative_path)}"
    if item.kind == "observation_report":
        return "/artifacts/report"
    return None


def _artifact_download_url(item: Any) -> str | None:
    open_url = _artifact_open_url(item)
    if open_url is None:
        return None
    return f"{open_url}?download=1"
