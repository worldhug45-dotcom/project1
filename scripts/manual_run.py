"""User-friendly manual runner for collect, export, observe, and status flows."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.infrastructure.settings import (
    BIZINFO_CERT_KEY_ENV_VAR,
    ConfigurationError,
    KEYWORDS_OVERRIDE_PATH_ENV_VAR,
    load_settings,
    resolve_keyword_override_path,
)
from app.ops import CollectObservationRecord
from app.ops import (
    latest_file,
    latest_observation_record,
    load_operator_status_snapshot,
    now_isoformat,
    persist_action_state,
)
from scripts.observe_bizinfo_collect import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_HISTORY_PATH,
    DEFAULT_LOG_PATH,
    DEFAULT_RAW_OUTPUT_DIR,
    DEFAULT_SNAPSHOT_DB_DIR,
)

DEFAULT_STATE_PATH = Path("data/operations/manual_run_state.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manual_run",
        description="Manual operations helper for internal users.",
    )
    parser.add_argument(
        "action",
        choices=["collect", "export", "observe", "status"],
        help="Manual operation to run.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Settings file used for the manual operation.",
    )
    parser.add_argument(
        "--source-mode",
        choices=["api", "fixture"],
        default=None,
        help="Collect source mode override.",
    )
    parser.add_argument(
        "--collect-diagnostics",
        action="store_true",
        help="Pass diagnostics output to collect when needed.",
    )
    parser.add_argument(
        "--history-path",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Observation history JSON path.",
    )
    parser.add_argument(
        "--raw-output-dir",
        type=Path,
        default=DEFAULT_RAW_OUTPUT_DIR,
        help="Observation raw JSONL directory.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Observation Markdown report path.",
    )
    parser.add_argument(
        "--snapshot-db-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DB_DIR,
        help="Observation per-run snapshot SQLite directory.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Manual runner state file that stores the latest action summaries.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings_action = _settings_action_for(args.action)
    cli_overrides = {"action": settings_action}
    if args.source_mode is not None and args.action in {"collect", "observe"}:
        cli_overrides["source_mode"] = args.source_mode

    try:
        settings = load_settings(args.config, cli_overrides=cli_overrides)
    except ConfigurationError as exc:
        _print_action_header(args.action, "config_error")
        _print_section(
            "current_paths",
            (
                ("config_path", args.config),
                ("keyword_override_path", "not loaded"),
                ("state_path", args.state_path),
            ),
        )
        _print_section("details", (("error", str(exc)),))
        persist_action_state(
            args.state_path,
            args.action,
            {
                "status": "config_error",
                "recorded_at": now_isoformat(),
                "config_path": str(args.config),
                "keyword_override_path": "not loaded",
                "error_message": str(exc),
            },
        )
        _print_failure_help(
            args.action,
            source_mode=args.source_mode,
            reason="config_error",
        )
        return 2

    keyword_override_path = resolve_keyword_override_path(args.config, os.environ)
    if args.action == "status":
        return _run_status(args, settings, keyword_override_path)
    if args.action == "observe":
        return _run_observe(args, settings, keyword_override_path)
    return _run_collect_or_export(args, settings, keyword_override_path)


def _run_collect_or_export(
    args,
    settings,
    keyword_override_path: Path | None,
) -> int:
    command = [
        sys.executable,
        "-m",
        "app.main",
        "--config",
        str(args.config),
        "--action",
        args.action,
    ]
    if args.source_mode is not None:
        command.extend(["--source-mode", args.source_mode])
    if args.collect_diagnostics:
        command.append("--collect-diagnostics")

    completed = _run_subprocess(command)
    summary = _extract_run_summary(completed.stdout)
    if completed.returncode != 0:
        _print_process_output(completed)
        print()
        _print_collect_or_export_report(
            action=args.action,
            summary=summary,
            settings=settings,
            config_path=args.config,
            keyword_override_path=keyword_override_path,
            status_label="failed",
        )
        persist_action_state(
            args.state_path,
            args.action,
            _collect_or_export_state_payload(
                action=args.action,
                status="failed",
                summary=summary,
                settings=settings,
                config_path=args.config,
                keyword_override_path=keyword_override_path,
                source_mode=args.source_mode or settings.runtime.source_mode,
                error_message=_extract_process_error_message(completed),
            ),
        )
        _print_failure_help(
            args.action,
            source_mode=args.source_mode or settings.runtime.source_mode,
            reason="runtime_failure",
        )
        return completed.returncode

    if summary is None:
        _print_process_output(completed)
        print()
        _print_action_header(args.action, "summary_missing")
        _print_section(
            "current_paths",
            (
                ("config_path", args.config),
                ("keyword_override_path", _display_path(keyword_override_path)),
                ("state_path", args.state_path),
            ),
        )
        persist_action_state(
            args.state_path,
            args.action,
            {
                "status": "summary_missing",
                "recorded_at": now_isoformat(),
                "config_path": str(args.config),
                "keyword_override_path": _display_path(keyword_override_path),
                "error_message": "run_summary payload was not emitted.",
            },
        )
        _print_failure_help(
            args.action,
            source_mode=args.source_mode or settings.runtime.source_mode,
            reason="summary_missing",
        )
        return completed.returncode

    _print_collect_or_export_report(
        action=args.action,
        summary=summary,
        settings=settings,
        config_path=args.config,
        keyword_override_path=keyword_override_path,
        status_label="success",
    )
    persist_action_state(
        args.state_path,
        args.action,
        _collect_or_export_state_payload(
            action=args.action,
            status="success",
            summary=summary,
            settings=settings,
            config_path=args.config,
            keyword_override_path=keyword_override_path,
            source_mode=args.source_mode or settings.runtime.source_mode,
            error_message=None,
        ),
    )
    return completed.returncode


def _run_observe(
    args,
    settings,
    keyword_override_path: Path | None,
) -> int:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "observe_bizinfo_collect.py"),
        "--config",
        str(args.config),
        "--history-path",
        str(args.history_path),
        "--raw-output-dir",
        str(args.raw_output_dir),
        "--log-path",
        str(args.log_path),
        "--snapshot-db-dir",
        str(args.snapshot_db_dir),
        "--source-mode",
        args.source_mode or settings.runtime.source_mode,
    ]
    completed = _run_subprocess(command)
    latest_observation = latest_observation_record(args.history_path)
    latest_raw_jsonl = latest_file(args.raw_output_dir, "*.jsonl")
    if completed.returncode != 0:
        _print_process_output(completed)
        print()
        _print_observe_report(
            args=args,
            keyword_override_path=keyword_override_path,
            latest_observation=latest_observation,
            latest_raw_jsonl=latest_raw_jsonl,
            status_label="failed",
        )
        persist_action_state(
            args.state_path,
            "observe",
            _observe_state_payload(
                status="failed",
                args=args,
                keyword_override_path=keyword_override_path,
                latest_observation=latest_observation,
                latest_raw_jsonl=latest_raw_jsonl,
                error_message=_extract_process_error_message(completed),
            ),
        )
        _print_failure_help(
            "observe",
            source_mode=args.source_mode or settings.runtime.source_mode,
            reason="runtime_failure",
        )
        return completed.returncode

    _print_observe_report(
        args=args,
        keyword_override_path=keyword_override_path,
        latest_observation=latest_observation,
        latest_raw_jsonl=latest_raw_jsonl,
        status_label="success",
    )
    persist_action_state(
        args.state_path,
        "observe",
        _observe_state_payload(
            status="success",
            args=args,
            keyword_override_path=keyword_override_path,
            latest_observation=latest_observation,
            latest_raw_jsonl=latest_raw_jsonl,
            error_message=None,
        ),
    )
    return completed.returncode


def _run_status(
    args,
    settings,
    keyword_override_path: Path | None,
) -> int:
    snapshot = load_operator_status_snapshot(
        config_path=args.config,
        history_path=args.history_path,
        raw_output_dir=args.raw_output_dir,
        log_path=args.log_path,
        state_path=args.state_path,
    )

    _print_action_header("status", "ready")
    _print_section("current_paths", tuple(snapshot.current_paths.items()))
    _print_state_section("recent_collect", snapshot.recent_collect)
    _print_state_section("recent_export", snapshot.recent_export)
    _print_state_section("recent_observe", snapshot.recent_observe)
    _print_section("launchers", tuple(snapshot.launchers.items()))
    return 0


def _collect_or_export_state_payload(
    *,
    action: str,
    status: str,
    summary: dict[str, object] | None,
    settings,
    config_path: Path,
    keyword_override_path: Path | None,
    source_mode: str,
    error_message: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "recorded_at": now_isoformat(),
        "config_path": str(config_path),
        "keyword_override_path": _display_path(keyword_override_path),
        "db_path": str(settings.storage.database_path),
        "export_output_dir": str(settings.export.output_dir),
        "source_mode": source_mode,
        "error_message": error_message,
    }
    if summary is None:
        return payload

    payload["run_summary_status"] = str(summary.get("status", "unknown"))
    payload["run_id"] = str(summary.get("run_id", "unknown"))
    if action == "collect":
        payload["fetched_count"] = int(summary.get("collected_count", 0))
        payload["saved_count"] = int(summary.get("saved_count", 0))
        payload["skipped_count"] = int(summary.get("skipped_count", 0))
        payload["error_count"] = int(summary.get("error_count", 0))
        return payload

    exported_files = summary.get("exported_files", [])
    if isinstance(exported_files, list):
        payload["exported_files"] = [str(item) for item in exported_files]
        payload["exported_file_count"] = len(exported_files)
        payload["exported_file_path"] = (
            str(exported_files[0]) if exported_files else "not available"
        )
    else:
        payload["exported_files"] = []
        payload["exported_file_count"] = 0
        payload["exported_file_path"] = "not available"
    return payload


def _observe_state_payload(
    *,
    status: str,
    args,
    keyword_override_path: Path | None,
    latest_observation: CollectObservationRecord | None,
    latest_raw_jsonl: Path | None,
    error_message: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "recorded_at": now_isoformat(),
        "config_path": str(args.config),
        "keyword_override_path": _display_path(keyword_override_path),
        "observation_history_path": str(args.history_path),
        "observation_report_path": str(args.log_path),
        "observation_raw_jsonl_dir": str(args.raw_output_dir),
        "observation_snapshot_db_dir": str(args.snapshot_db_dir),
        "latest_raw_jsonl_path": _display_path(latest_raw_jsonl),
        "source_mode": args.source_mode,
        "error_message": error_message,
    }
    if latest_observation is None:
        return payload

    payload["run_id"] = latest_observation.run_id
    payload["observed_on"] = latest_observation.observed_on
    payload["run_summary_status"] = latest_observation.status
    payload["fetched_count"] = latest_observation.fetched_count
    payload["saved_count"] = latest_observation.saved_count
    payload["skipped_count"] = latest_observation.skipped_count
    payload["error_count"] = latest_observation.error_count
    return payload


def _print_collect_or_export_report(
    *,
    action: str,
    summary: dict[str, object] | None,
    settings,
    config_path: Path,
    keyword_override_path: Path | None,
    status_label: str,
) -> None:
    _print_action_header(action, status_label)
    _print_section(
        "current_paths",
        (
            ("config_path", config_path),
            ("keyword_override_path", _display_path(keyword_override_path)),
            ("db_path", settings.storage.database_path),
            ("export_output_dir", settings.export.output_dir),
        ),
    )

    if summary is None:
        _print_section("summary", (("status", "not available"),))
        return

    if action == "collect":
        _print_section(
            "summary",
            (
                ("status", summary.get("status", "unknown")),
                ("fetched_count", summary.get("collected_count", 0)),
                ("saved_count", summary.get("saved_count", 0)),
                ("skipped_count", summary.get("skipped_count", 0)),
                ("error_count", summary.get("error_count", 0)),
            ),
        )
        return

    exported_files = summary.get("exported_files", [])
    exported_lines: list[tuple[str, object]] = [
        ("status", summary.get("status", "unknown")),
        ("exported_file_count", len(exported_files) if isinstance(exported_files, list) else 0),
    ]
    if isinstance(exported_files, list) and exported_files:
        for exported_file in exported_files:
            exported_lines.append(("exported_file_path", exported_file))
    else:
        exported_lines.append(("exported_file_path", "none"))
    _print_section("summary", exported_lines)


def _print_observe_report(
    *,
    args,
    keyword_override_path: Path | None,
    latest_observation: CollectObservationRecord | None,
    latest_raw_jsonl: Path | None,
    status_label: str,
) -> None:
    _print_action_header("observe", status_label)
    _print_section(
        "current_paths",
        (
            ("config_path", args.config),
            ("keyword_override_path", _display_path(keyword_override_path)),
            ("observation_history_path", args.history_path),
            ("observation_report_path", args.log_path),
            ("observation_raw_jsonl_dir", args.raw_output_dir),
            ("observation_snapshot_db_dir", args.snapshot_db_dir),
            ("latest_raw_jsonl_path", _display_path(latest_raw_jsonl)),
        ),
    )
    if latest_observation is None:
        _print_section("summary", (("status", "not available"),))
        return
    _print_section(
        "summary",
        (
            ("status", latest_observation.status),
            ("run_id", latest_observation.run_id),
            ("observed_on", latest_observation.observed_on),
            ("fetched_count", latest_observation.fetched_count),
            ("saved_count", latest_observation.saved_count),
            ("skipped_count", latest_observation.skipped_count),
            ("error_count", latest_observation.error_count),
        ),
    )


def _print_state_section(title: str, payload: dict[str, Any] | None) -> None:
    if not payload:
        _print_section(title, (("status", "not available"),))
        return
    lines: list[tuple[str, object]] = []
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, list):
            if not value:
                lines.append((key, "none"))
                continue
            for item in value:
                lines.append((key, item))
            continue
        lines.append((key, value))
    _print_section(title, lines or (("status", "not available"),))


def _print_failure_help(action: str, *, source_mode: str | None, reason: str) -> None:
    checks: list[str] = []
    if reason == "config_error":
        checks.append("Check that config_path exists and the TOML syntax is valid.")
        checks.append(
            "If you use a custom keyword override file, confirm "
            f"{KEYWORDS_OVERRIDE_PATH_ENV_VAR} points to the correct file."
        )
    elif reason == "summary_missing":
        checks.append("Check whether app.main still emits a run_summary JSON payload.")
        checks.append("Check the previous console output for an error event.")
    else:
        checks.append("Check the previous error log and run_summary status first.")

    if action in {"collect", "observe"} and source_mode == "api":
        checks.append(f"api mode requires the {BIZINFO_CERT_KEY_ENV_VAR} environment variable.")
    if action == "collect":
        checks.append("Check whether source_mode and fixture/api settings match the intended run.")
        checks.append("Check write permission for db_path and export_output_dir.")
    elif action == "export":
        checks.append("Check whether Notice rows already exist in the SQLite database.")
        checks.append("Check write permission for export_output_dir.")
    else:
        checks.append("Check write permission for history, report, and raw jsonl paths.")

    _print_section("next_checks", tuple(("check", item) for item in checks))


def _settings_action_for(action: str) -> str:
    if action == "observe":
        return "collect"
    if action == "status":
        return "export"
    return action


def _run_subprocess(command: list[str]) -> subprocess.CompletedProcess[str]:
    child_environ = os.environ.copy()
    child_environ["PYTHONIOENCODING"] = "utf-8"
    child_environ["PYTHONUTF8"] = "1"
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=child_environ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _extract_run_summary(stdout: str) -> dict[str, object] | None:
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        payload = json.loads(line)
        if payload.get("summary_type") == "run_summary":
            return payload
    return None


def _extract_process_error_message(completed: subprocess.CompletedProcess[str]) -> str | None:
    stderr = completed.stderr.strip()
    if stderr:
        return stderr.splitlines()[-1]

    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- error: "):
            return stripped.removeprefix("- error: ").strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if payload.get("event_type") == "error":
            error_message = payload.get("error_message")
            if isinstance(error_message, str) and error_message.strip():
                return error_message.strip()

    stdout = completed.stdout.strip()
    if stdout:
        return stdout.splitlines()[-1].strip()
    return None


def _print_process_output(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)


def _print_action_header(action: str, status_label: str) -> None:
    print(f"[manual-run] {action} {status_label}")


def _print_section(
    title: str,
    lines: tuple[tuple[str, object], ...] | list[tuple[str, object]],
) -> None:
    print(f"{title}:")
    for label, value in lines:
        print(f"- {label}: {value}")


def _display_path(path: Path | None) -> str:
    if path is None:
        return "not available"
    return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
