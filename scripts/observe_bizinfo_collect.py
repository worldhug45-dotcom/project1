"""Run bizinfo API collect with diagnostics and persist an observation snapshot."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.ops import (
    load_observation_history,
    parse_collect_observation_lines,
    render_observation_log,
    save_observation_history,
    upsert_observation_record,
)


DEFAULT_CONFIG_PATH = Path("config/settings.local.toml")
DEFAULT_HISTORY_PATH = Path("data/observations/bizinfo/collect_observations.json")
DEFAULT_RAW_OUTPUT_DIR = Path("data/observations/bizinfo/raw")
DEFAULT_LOG_PATH = Path("doc/bizinfo_collect_observation_log.md")
DEFAULT_SNAPSHOT_DB_DIR = Path("data/observations/bizinfo/snapshots")
NEXT_ROUND_CANDIDATES = (
    "국방기술/국방벤처: day 2 no_keyword_match 사례가 나와 방산·국방 SI/infra 인접 키워드 후보로 관찰 지속",
    "전자전/KES: 전자·하드웨어 계열 전시회 공고가 target scope인지 잡음인지 day 3까지 추가 확인 필요",
    "플랫폼: 인접성은 있으나 일반 사업/마케팅 문맥 잡음이 여전히 커서 보류 유지",
    "IP: 브랜드/IP 보호 전략 문맥이 기술 도메인과 직접 연결되는지 근거가 더 필요해 보류 유지",
    "교육: excluded_keyword 재검토 후보이지만 2일 누적 기준 비적격 사례가 우세해 아직 유지",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="observe_bizinfo_collect",
        description="Record one bizinfo API collect observation snapshot.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Settings file used for repeated bizinfo observation runs.",
    )
    parser.add_argument(
        "--history-path",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Local JSON history file that accumulates observation snapshots.",
    )
    parser.add_argument(
        "--raw-output-dir",
        type=Path,
        default=DEFAULT_RAW_OUTPUT_DIR,
        help="Directory where raw CLI JSONL output is stored.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Markdown report regenerated from the accumulated observation history.",
    )
    parser.add_argument(
        "--snapshot-db-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DB_DIR,
        help="Per-observation SQLite snapshot directory to avoid duplicate_notice skew.",
    )
    parser.add_argument(
        "--source-mode",
        choices=["api", "fixture"],
        default="api",
        help="Collect source mode. Observation runs default to api.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = [
        sys.executable,
        "-m",
        "app.main",
        "--config",
        str(args.config),
        "--action",
        "collect",
        "--source-mode",
        args.source_mode,
        "--collect-diagnostics",
    ]
    snapshot_db_path = _build_snapshot_db_path(args.snapshot_db_dir)
    child_environ = os.environ.copy()
    child_environ["PROJECT1_STORAGE_DATABASE_PATH"] = str(snapshot_db_path)
    child_environ["PYTHONIOENCODING"] = "utf-8"
    child_environ["PYTHONUTF8"] = "1"

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=child_environ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not stdout_lines:
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode or 1)

    record = parse_collect_observation_lines(stdout_lines)
    raw_path = _write_raw_output(args.raw_output_dir, record, stdout_lines)

    history = load_observation_history(args.history_path)
    history = upsert_observation_record(history, record)
    save_observation_history(args.history_path, history)

    args.log_path.parent.mkdir(parents=True, exist_ok=True)
    args.log_path.write_text(
        render_observation_log(
            history,
            config_path=str(args.config).replace("\\", "/"),
            source_mode=args.source_mode,
            next_round_candidates=NEXT_ROUND_CANDIDATES,
        ),
        encoding="utf-8",
    )

    print(
        "Observation recorded: "
        f"date={record.observed_on} "
        f"run_id={record.run_id} "
        f"status={record.status} "
        f"fetched={record.fetched_count} "
        f"saved={record.saved_count} "
        f"skipped={record.skipped_count} "
        f"error={record.error_count}"
    )
    print(f"History: {args.history_path}")
    print(f"Report: {args.log_path}")
    print(f"Raw JSONL: {raw_path}")
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return completed.returncode


def _write_raw_output(
    raw_output_dir: Path,
    record,
    stdout_lines: list[str],
) -> Path:
    raw_output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_output_dir / f"{record.observed_on}_{record.run_id}.jsonl"
    raw_path.write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")
    return raw_path


def _build_snapshot_db_path(snapshot_db_dir: Path) -> Path:
    snapshot_db_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return snapshot_db_dir / f"{timestamp}_notices.sqlite3"


if __name__ == "__main__":
    raise SystemExit(main())
