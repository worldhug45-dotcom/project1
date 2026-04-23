import json
import os
from pathlib import Path
from unittest import TestCase

from app.ops import load_operator_status_snapshot
from app.ops.observation import (
    CollectObservationRecord,
    NoticeObservationExample,
    save_observation_history,
)
from tests.temp_utils import temporary_directory


class OperatorStatusTests(TestCase):
    def test_load_operator_status_snapshot_reads_paths_and_recent_states(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            history_path = root / "history.json"
            raw_output_dir = root / "raw"
            log_path = root / "report.md"
            state_path = root / "manual_state.json"
            output_dir = root / "output"
            older_xlsx = output_dir / "notices_20260420_run.xlsx"
            latest_xlsx = output_dir / "notices_20260421_run.xlsx"
            older_raw = raw_output_dir / "20260420.jsonl"
            latest_raw = raw_output_dir / "20260421.jsonl"

            output_dir.mkdir(parents=True, exist_ok=True)
            older_xlsx.write_bytes(b"older-xlsx")
            latest_xlsx.write_bytes(b"fake-xlsx")
            raw_output_dir.mkdir(parents=True, exist_ok=True)
            older_raw.write_text('{"day":"older"}\n', encoding="utf-8")
            latest_raw.write_text('{"day":"latest"}\n', encoding="utf-8")
            log_path.write_text("# report\n", encoding="utf-8")
            os.utime(older_xlsx, (1_713_657_600, 1_713_657_600))
            os.utime(latest_xlsx, (1_713_744_000, 1_713_744_000))
            os.utime(log_path, (1_713_787_200, 1_713_787_200))
            os.utime(older_raw, (1_713_830_400, 1_713_830_400))
            os.utime(latest_raw, (1_713_916_800, 1_713_916_800))
            _write_observation_history(history_path)
            state_path.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-04-21T00:30:00+00:00",
                        "actions": {
                            "collect": {
                                "status": "success",
                                "recorded_at": "2026-04-21T00:10:00+00:00",
                                "run_id": "collect-run-1",
                                "fetched_count": 20,
                                "saved_count": 4,
                                "skipped_count": 16,
                                "error_count": 0,
                            },
                            "export": {
                                "status": "success",
                                "recorded_at": "2026-04-21T00:20:00+00:00",
                                "exported_files": [str(latest_xlsx)],
                                "exported_file_count": 1,
                            },
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            snapshot = load_operator_status_snapshot(
                config_path=config_path,
                history_path=history_path,
                raw_output_dir=raw_output_dir,
                log_path=log_path,
                state_path=state_path,
            )

        payload = snapshot.to_dict()
        self.assertEqual(payload["current_paths"]["config_path"], str(config_path))
        self.assertEqual(payload["current_paths"]["sqlite_db_path"], str(root / "notices.sqlite3"))
        self.assertEqual(payload["current_paths"]["latest_exported_file_path"], str(latest_xlsx))
        self.assertEqual(payload["recent_collect"]["run_id"], "collect-run-1")
        self.assertEqual(payload["recent_export"]["exported_file_count"], 1)
        self.assertEqual(payload["recent_observe"]["run_id"], "observe-history-run-1")
        self.assertEqual(payload["recent_observe"]["observed_on"], "2026-04-21")
        self.assertEqual(payload["updated_at"], "2026-04-21T00:30:00+00:00")
        self.assertEqual(len(payload["artifacts"]), 5)
        self.assertEqual(payload["artifacts"][0]["kind"], "export_result")
        self.assertEqual(payload["artifacts"][0]["name"], latest_xlsx.name)
        self.assertEqual(payload["artifacts"][1]["kind"], "export_result")
        self.assertEqual(payload["artifacts"][1]["name"], older_xlsx.name)
        self.assertEqual(payload["artifacts"][2]["kind"], "observation_report")
        self.assertEqual(payload["artifacts"][2]["name"], log_path.name)
        self.assertEqual(payload["artifacts"][3]["kind"], "observation_raw")
        self.assertEqual(payload["artifacts"][3]["name"], latest_raw.name)
        self.assertEqual(payload["artifacts"][4]["kind"], "observation_raw")
        self.assertEqual(payload["artifacts"][4]["name"], older_raw.name)


def _write_fixture_config(directory: Path) -> Path:
    config_path = directory / "settings.toml"
    database_path = directory / "notices.sqlite3"
    output_dir = directory / "output"
    config_path.write_text(
        f"""
[sources.bizinfo]
enabled = true
fixture_path = "tests/fixtures/bizinfo/support_notices.json"

[sources.g2b]
enabled = false

[keywords]
core = ["AI", "DX", "SI"]
supporting = ["데이터", "클라우드", "인프라", "보안", "IT서비스", "유지보수"]
exclude = ["채용", "교육", "행사"]

[storage]
type = "sqlite"
database_path = "{database_path.as_posix()}"

[export]
output_dir = "{output_dir.as_posix()}"
filename_pattern = "notices_{{run_date}}_{{run_id}}.xlsx"
support_sheet_name = "support_notices"
bid_sheet_name = "bid_notices"
date_format = "%Y-%m-%d"

[runtime]
action = "collect"
source_mode = "fixture"
""",
        encoding="utf-8",
    )
    return config_path


def _write_observation_history(path: Path) -> None:
    record = CollectObservationRecord(
        observed_on="2026-04-21",
        run_id="observe-history-run-1",
        status="success",
        fetched_count=20,
        saved_count=4,
        skipped_count=16,
        error_count=0,
        skip_reason_counts=(("excluded_keyword", 4), ("no_keyword_match", 12)),
        saved_examples=(
            NoticeObservationExample(
                title="AI platform support project",
                organization="MSS",
                skip_reason=None,
                primary_domain="ai",
                matched_core_keywords=("AI",),
                matched_supporting_keywords=("platform",),
                matched_excluded_keywords=(),
            ),
        ),
        skipped_examples=(),
    )
    save_observation_history(path, (record,))
