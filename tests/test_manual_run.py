import io
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from app.ops import CollectObservationRecord, NoticeObservationExample, save_observation_history
from scripts.manual_run import main
from tests.temp_utils import temporary_directory


class ManualRunTests(TestCase):
    def test_collect_prints_counts_and_result_paths_in_consistent_format(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"
            state_path = root / "manual-state.json"
            override_path.write_text(
                """
[keywords_override]
add_supporting = ["국방기술"]
""",
                encoding="utf-8",
            )

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "collect",
                        "--config",
                        str(config_path),
                        "--source-mode",
                        "fixture",
                        "--state-path",
                        str(state_path),
                    ]
                )

            self.assertTrue(state_path.exists())

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("[manual-run] collect success", output)
        self.assertIn("summary:", output)
        self.assertIn("- fetched_count: 2", output)
        self.assertIn("- saved_count: 1", output)
        self.assertIn("- skipped_count: 1", output)
        self.assertIn("- error_count: 0", output)
        self.assertIn("current_paths:", output)
        self.assertIn(f"- config_path: {config_path}", output)
        self.assertIn(f"- keyword_override_path: {override_path}", output)
        self.assertIn("- db_path: ", output)
        self.assertIn("- export_output_dir: ", output)

    def test_export_prints_exported_file_path_and_output_dir(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            state_path = root / "manual-state.json"

            with redirect_stdout(io.StringIO()):
                collect_exit_code = main(
                    [
                        "collect",
                        "--config",
                        str(config_path),
                        "--source-mode",
                        "fixture",
                        "--state-path",
                        str(state_path),
                    ]
                )
            self.assertEqual(collect_exit_code, 0)

            with redirect_stdout(stdout):
                export_exit_code = main(
                    [
                        "export",
                        "--config",
                        str(config_path),
                        "--state-path",
                        str(state_path),
                    ]
                )

            exported_files = list((root / "output").glob("*.xlsx"))

        output = stdout.getvalue()
        self.assertEqual(export_exit_code, 0)
        self.assertTrue(exported_files)
        self.assertIn("[manual-run] export success", output)
        self.assertIn("- export_output_dir: ", output)
        self.assertIn("- exported_file_count: 1", output)
        self.assertIn(f"- exported_file_path: {exported_files[0]}", output)

    def test_observe_prints_history_report_and_raw_paths(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            history_path = root / "observation-history.json"
            raw_output_dir = root / "raw"
            log_path = root / "observation-report.md"
            snapshot_db_dir = root / "snapshots"
            state_path = root / "manual-state.json"

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "observe",
                        "--config",
                        str(config_path),
                        "--source-mode",
                        "fixture",
                        "--history-path",
                        str(history_path),
                        "--raw-output-dir",
                        str(raw_output_dir),
                        "--log-path",
                        str(log_path),
                        "--snapshot-db-dir",
                        str(snapshot_db_dir),
                        "--state-path",
                        str(state_path),
                    ]
                )

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("[manual-run] observe success", output)
        self.assertIn(f"- observation_history_path: {history_path}", output)
        self.assertIn(f"- observation_report_path: {log_path}", output)
        self.assertIn(f"- observation_raw_jsonl_dir: {raw_output_dir}", output)
        self.assertIn(f"- observation_snapshot_db_dir: {snapshot_db_dir}", output)
        self.assertIn("- latest_raw_jsonl_path: ", output)

    def test_status_prints_current_paths_and_recent_summaries(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            output_dir = root / "output"
            history_path = root / "observation-history.json"
            raw_output_dir = root / "raw"
            log_path = root / "observation-report.md"
            state_path = root / "manual-state.json"
            latest_xlsx = output_dir / "notices_20260421_run.xlsx"
            latest_xlsx.parent.mkdir(parents=True, exist_ok=True)
            latest_xlsx.write_bytes(b"fake-xlsx")
            raw_output_dir.mkdir(parents=True, exist_ok=True)
            latest_raw_jsonl = raw_output_dir / "2026-04-21_run.jsonl"
            latest_raw_jsonl.write_text("{}\n", encoding="utf-8")
            log_path.write_text("# observation report\n", encoding="utf-8")
            _write_observation_history(history_path)
            state_path.write_text(
                """
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
      "error_count": 0
    },
    "export": {
      "status": "success",
      "recorded_at": "2026-04-21T00:20:00+00:00",
      "exported_file_count": 1,
      "exported_files": ["TEMP_XLSX"]
    },
    "observe": {
      "status": "success",
      "recorded_at": "2026-04-21T00:30:00+00:00",
      "run_id": "observe-run-1",
      "fetched_count": 20,
      "saved_count": 4,
      "skipped_count": 16,
      "error_count": 0
    }
  }
}
""".replace("TEMP_XLSX", str(latest_xlsx).replace("\\", "\\\\")),
                encoding="utf-8",
            )

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "status",
                        "--config",
                        str(config_path),
                        "--history-path",
                        str(history_path),
                        "--raw-output-dir",
                        str(raw_output_dir),
                        "--log-path",
                        str(log_path),
                        "--state-path",
                        str(state_path),
                    ]
                )

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("[manual-run] status ready", output)
        self.assertIn(f"- config_path: {config_path}", output)
        self.assertIn(f"- sqlite_db_path: {root / 'notices.sqlite3'}", output)
        self.assertIn(f"- export_output_dir: {output_dir}", output)
        self.assertIn(f"- latest_exported_file_path: {latest_xlsx}", output)
        self.assertIn(f"- observation_history_path: {history_path}", output)
        self.assertIn(f"- observation_report_path: {log_path}", output)
        self.assertIn(f"- observation_raw_jsonl_dir: {raw_output_dir}", output)
        self.assertIn("recent_collect:", output)
        self.assertIn("- run_id: collect-run-1", output)
        self.assertIn("recent_export:", output)
        self.assertIn(f"- exported_files: {latest_xlsx}", output)
        self.assertIn("recent_observe:", output)
        self.assertIn("- run_id: observe-run-1", output)
        self.assertIn("launchers:", output)
        self.assertIn("- status_launcher: scripts/run_status.ps1", output)

    def test_configuration_error_prints_next_checks(self) -> None:
        stdout = io.StringIO()
        with temporary_directory() as directory:
            state_path = Path(directory) / "manual-state.json"

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "collect",
                        "--config",
                        "missing-settings.toml",
                        "--state-path",
                        str(state_path),
                    ]
                )

            state_payload = state_path.read_text(encoding="utf-8")

        output = stdout.getvalue()
        self.assertEqual(exit_code, 2)
        self.assertIn("[manual-run] collect config_error", output)
        self.assertIn("next_checks:", output)
        self.assertIn("Check that config_path exists", output)
        self.assertIn("PROJECT1_KEYWORDS_OVERRIDE_PATH", output)
        self.assertIn('"status": "config_error"', state_payload)
        self.assertIn(
            '"error_message": "Config file does not exist: missing-settings.toml"', state_payload
        )

    def test_runtime_failure_prints_next_checks(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            completed = subprocess.CompletedProcess(
                args=["python"],
                returncode=1,
                stdout='{"status":"failed","summary_type":"run_summary","collected_count":0,"saved_count":0,"skipped_count":0,"error_count":1,"exported_files":[]}\n',
                stderr="",
            )

            with patch("scripts.manual_run._run_subprocess", return_value=completed):
                with redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "collect",
                            "--config",
                            str(config_path),
                            "--source-mode",
                            "fixture",
                        ]
                    )

        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("[manual-run] collect failed", output)
        self.assertIn("next_checks:", output)
        self.assertIn("source_mode and fixture/api settings", output)
        self.assertIn("write permission for db_path", output)

    def test_launcher_scripts_exist_and_target_manual_run_actions(self) -> None:
        launcher_expectations = {
            "scripts/run_collect.ps1": "collect",
            "scripts/run_export.ps1": "export",
            "scripts/run_observe.ps1": "observe",
            "scripts/run_status.ps1": "status",
        }

        for launcher_path, action in launcher_expectations.items():
            script = Path(launcher_path)
            self.assertTrue(script.exists(), launcher_path)
            content = script.read_text(encoding="utf-8")
            self.assertIn("scripts/manual_run.py", content)
            self.assertIn(f'"{action}"', content)


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
        skip_reason_counts=(("excluded_keyword", 7), ("no_keyword_match", 9)),
        saved_examples=(
            NoticeObservationExample(
                title="AI 지원사업",
                organization="MSS",
                primary_domain="ai",
                skip_reason=None,
            ),
        ),
        skipped_examples=(
            NoticeObservationExample(
                title="일반 행사 공고",
                organization="Agency",
                primary_domain=None,
                skip_reason="excluded_keyword",
                matched_excluded_keywords=("행사",),
            ),
        ),
    )
    save_observation_history(path, (record,))
