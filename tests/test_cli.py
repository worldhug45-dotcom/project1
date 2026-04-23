import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from xml.etree import ElementTree
from zipfile import ZipFile

from app.main import main
from app.exporters import EXPORT_COLUMN_ORDER
from app.exporters.xlsx import SPREADSHEET_NS
from app.infrastructure.settings import BIZINFO_CERT_KEY_ENV_VAR, G2B_API_KEY_ENV_VAR
from app.ops import StorageWriteError
from tests.temp_utils import temporary_directory


SPREADSHEET_NAMESPACES = {"s": SPREADSHEET_NS}


class CliSkeletonTests(TestCase):
    def test_successful_cli_emits_start_and_finish_events(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_collect_fixture_config(Path(directory))

            with redirect_stdout(stdout):
                exit_code = main(["--config", str(config_path), "--action", "export"])

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        finish_event = json.loads(lines[-1])

        self.assertEqual(exit_code, 0)
        self.assertEqual(start_event["event_type"], "run_started")
        self.assertEqual(start_event["status"], "running")
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "success")
        self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_export_action_creates_xlsx_from_sqlite_notices(self) -> None:
        collect_stdout = io.StringIO()
        export_stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_collect_fixture_config(root)

            with redirect_stdout(collect_stdout):
                collect_exit_code = main(
                    [
                        "--config",
                        str(config_path),
                        "--action",
                        "collect",
                        "--source-mode",
                        "fixture",
                    ]
                )

            with redirect_stdout(export_stdout):
                export_exit_code = main(["--config", str(config_path), "--action", "export"])

            export_lines = export_stdout.getvalue().splitlines()
            start_event = json.loads(export_lines[0])
            export_event = json.loads(export_lines[1])
            summary = json.loads(export_lines[2])
            finish_event = json.loads(export_lines[3])
            exported_file = Path(summary["exported_files"][0])

            self.assertEqual(collect_exit_code, 0)
            self.assertEqual(export_exit_code, 0)
            self.assertTrue(exported_file.exists())
            self.assertEqual(exported_file.parent, root / "output")

            with ZipFile(exported_file) as workbook:
                self.assertEqual(
                    _sheet_names(workbook.read("xl/workbook.xml")),
                    ("support_notices", "bid_notices"),
                )
                support_rows = _sheet_rows(workbook.read("xl/worksheets/sheet1.xml"))
                bid_rows = _sheet_rows(workbook.read("xl/worksheets/sheet2.xml"))
                self.assertEqual(support_rows[0], EXPORT_COLUMN_ORDER)
                self.assertEqual(len(support_rows), 2)
                self.assertEqual(bid_rows, (EXPORT_COLUMN_ORDER,))

            self.assertEqual(start_event["event_type"], "run_started")
            self.assertEqual(export_event["event_type"], "export_finished")
            self.assertEqual(export_event["status"], "success")
            self.assertEqual(export_event["output_file_path"], str(exported_file))
            self.assertEqual(summary["summary_type"], "run_summary")
            self.assertEqual(summary["action"], "export")
            self.assertEqual(summary["status"], "success")
            self.assertEqual(summary["exported_files"], [str(exported_file)])
            self.assertEqual(finish_event["event_type"], "run_finished")
            self.assertEqual(finish_event["status"], "success")
            self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_collect_action_logs_failed_run_when_storage_save_fails(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_collect_fixture_config(Path(directory))

            with patch("app.main.SQLiteNoticeRepository", _FailingSQLiteNoticeRepository):
                with redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "--config",
                            str(config_path),
                            "--action",
                            "collect",
                            "--source-mode",
                            "fixture",
                        ]
                    )

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        source_event = json.loads(lines[1])
        error_event = json.loads(lines[2])
        summary = json.loads(lines[3])
        finish_event = json.loads(lines[4])

        self.assertEqual(exit_code, 1)
        self.assertEqual(start_event["event_type"], "run_started")
        self.assertEqual(source_event["event_type"], "source_finished")
        self.assertEqual(source_event["status"], "failed")
        self.assertEqual(source_event["source"], "bizinfo")
        self.assertEqual(source_event["fetched_count"], 2)
        self.assertEqual(source_event["saved_count"], 0)
        self.assertEqual(source_event["excluded_count"], 0)
        self.assertEqual(error_event["event_type"], "error")
        self.assertEqual(error_event["status"], "failed")
        self.assertEqual(error_event["error_type"], "fatal")
        self.assertEqual(error_event["error_source"], "bizinfo")
        self.assertEqual(summary["summary_type"], "run_summary")
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["collected_count"], 2)
        self.assertEqual(summary["saved_count"], 0)
        self.assertEqual(summary["skipped_count"], 0)
        self.assertEqual(summary["error_count"], 1)
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "failed")
        self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_configuration_error_emits_error_and_failed_finish_events(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr), self.assertRaises(SystemExit):
            main(["--action", "export"])

        lines = stdout.getvalue().splitlines()
        error_event = json.loads(lines[1])
        finish_event = json.loads(lines[2])

        self.assertIn("Configuration error", stderr.getvalue())
        self.assertEqual(error_event["event_type"], "error")
        self.assertEqual(error_event["error_type"], "configuration")
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "failed")

    def test_collect_action_runs_bizinfo_fixture_flow(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_collect_fixture_config(Path(directory))

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--config",
                        str(config_path),
                        "--action",
                        "collect",
                        "--source-mode",
                        "fixture",
                    ]
                )

            self.assertTrue((Path(directory) / "notices.sqlite3").exists())

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        source_event = json.loads(lines[1])
        summary = json.loads(lines[2])
        finish_event = json.loads(lines[3])

        self.assertEqual(exit_code, 0)
        self.assertEqual(start_event["event_type"], "run_started")
        self.assertEqual(source_event["event_type"], "source_finished")
        self.assertEqual(source_event["source"], "bizinfo")
        self.assertEqual(source_event["fetched_count"], 2)
        self.assertEqual(source_event["saved_count"], 1)
        self.assertEqual(source_event["excluded_count"], 1)
        self.assertEqual(summary["summary_type"], "run_summary")
        self.assertEqual(summary["action"], "collect")
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["collected_count"], 2)
        self.assertEqual(summary["saved_count"], 1)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertEqual(summary["error_count"], 0)
        self.assertEqual(summary["source_results"][0]["source"], "bizinfo")
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "success")
        self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_collect_action_runs_g2b_fixture_flow(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_g2b_collect_fixture_config(Path(directory))

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--config",
                        str(config_path),
                        "--action",
                        "collect",
                        "--source-mode",
                        "fixture",
                    ]
                )

            self.assertTrue((Path(directory) / "notices.sqlite3").exists())

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        source_event = json.loads(lines[1])
        summary = json.loads(lines[2])
        finish_event = json.loads(lines[3])

        self.assertEqual(exit_code, 0)
        self.assertEqual(start_event["event_type"], "run_started")
        self.assertEqual(source_event["event_type"], "source_finished")
        self.assertEqual(source_event["source"], "g2b")
        self.assertEqual(source_event["fetched_count"], 2)
        self.assertEqual(source_event["saved_count"], 1)
        self.assertEqual(source_event["excluded_count"], 1)
        self.assertEqual(summary["summary_type"], "run_summary")
        self.assertEqual(summary["action"], "collect")
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["collected_count"], 2)
        self.assertEqual(summary["saved_count"], 1)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertEqual(summary["error_count"], 0)
        self.assertEqual(summary["source_results"][0]["source"], "g2b")
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "success")
        self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_collect_action_runs_g2b_api_flow_with_mocked_http_client(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_g2b_collect_api_config(Path(directory))

            with patch.dict(os.environ, {G2B_API_KEY_ENV_VAR: "local-secret"}, clear=False):
                with patch("app.main.G2BApiHttpClient", _FakeG2BApiHttpClient):
                    with redirect_stdout(stdout):
                        exit_code = main(
                            [
                                "--config",
                                str(config_path),
                                "--action",
                                "collect",
                                "--source-mode",
                                "api",
                            ]
                        )

            self.assertTrue((Path(directory) / "notices.sqlite3").exists())

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        source_event = json.loads(lines[1])
        summary = json.loads(lines[2])
        finish_event = json.loads(lines[3])

        self.assertEqual(exit_code, 0)
        self.assertEqual(source_event["event_type"], "source_finished")
        self.assertEqual(source_event["source"], "g2b")
        self.assertEqual(source_event["fetched_count"], 2)
        self.assertEqual(source_event["saved_count"], 1)
        self.assertEqual(source_event["excluded_count"], 1)
        self.assertEqual(summary["action"], "collect")
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["collected_count"], 2)
        self.assertEqual(summary["saved_count"], 1)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertNotIn("local-secret", stdout.getvalue())
        self.assertEqual(finish_event["status"], "success")
        self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_g2b_api_collect_then_export_creates_bid_sheet_with_rows(self) -> None:
        collect_stdout = io.StringIO()
        export_stdout = io.StringIO()

        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_g2b_collect_api_config(root)

            with patch.dict(os.environ, {G2B_API_KEY_ENV_VAR: "local-secret"}, clear=False):
                with patch("app.main.G2BApiHttpClient", _FakeG2BApiHttpClient):
                    with redirect_stdout(collect_stdout):
                        collect_exit_code = main(
                            [
                                "--config",
                                str(config_path),
                                "--action",
                                "collect",
                                "--source-mode",
                                "api",
                            ]
                        )

            with redirect_stdout(export_stdout):
                export_exit_code = main(["--config", str(config_path), "--action", "export"])

            export_lines = export_stdout.getvalue().splitlines()
            export_event = json.loads(export_lines[1])
            summary = json.loads(export_lines[2])
            exported_file = Path(summary["exported_files"][0])

            self.assertEqual(collect_exit_code, 0)
            self.assertEqual(export_exit_code, 0)
            self.assertTrue(exported_file.exists())

            with ZipFile(exported_file) as workbook:
                self.assertEqual(
                    _sheet_names(workbook.read("xl/workbook.xml")),
                    ("support_notices", "bid_notices"),
                )
                support_rows = _sheet_rows(workbook.read("xl/worksheets/sheet1.xml"))
                bid_rows = _sheet_rows(workbook.read("xl/worksheets/sheet2.xml"))
                self.assertEqual(support_rows, (EXPORT_COLUMN_ORDER,))
                self.assertEqual(bid_rows[0], EXPORT_COLUMN_ORDER)
                self.assertEqual(len(bid_rows), 2)

            self.assertEqual(export_event["event_type"], "export_finished")
            self.assertEqual(export_event["status"], "success")
            self.assertEqual(summary["action"], "export")
            self.assertEqual(summary["status"], "success")
            self.assertEqual(summary["exported_files"], [str(exported_file)])

    def test_collect_action_emits_diagnostics_when_requested(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_collect_fixture_config(Path(directory))

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--config",
                        str(config_path),
                        "--action",
                        "collect",
                        "--source-mode",
                        "fixture",
                        "--collect-diagnostics",
                    ]
                )

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        diagnostic_event_1 = json.loads(lines[1])
        diagnostic_event_2 = json.loads(lines[2])
        source_event = json.loads(lines[3])
        summary = json.loads(lines[4])
        finish_event = json.loads(lines[5])

        self.assertEqual(exit_code, 0)
        self.assertEqual(start_event["event_type"], "run_started")
        self.assertEqual(diagnostic_event_1["event_type"], "collect_diagnostic")
        self.assertEqual(diagnostic_event_1["source"], "bizinfo")
        self.assertEqual(diagnostic_event_1["status"], "running")
        self.assertEqual(diagnostic_event_1["metadata"]["outcome"], "saved")
        self.assertTrue(diagnostic_event_1["metadata"]["eligible"])
        self.assertEqual(diagnostic_event_2["event_type"], "collect_diagnostic")
        self.assertEqual(diagnostic_event_2["metadata"]["outcome"], "skipped")
        self.assertFalse(diagnostic_event_2["metadata"]["eligible"])
        self.assertIsNotNone(diagnostic_event_2["metadata"]["skip_reason"])
        self.assertEqual(source_event["event_type"], "source_finished")
        self.assertEqual(summary["summary_type"], "run_summary")
        self.assertEqual(finish_event["event_type"], "run_finished")

    def test_collect_action_runs_bizinfo_api_flow_with_mocked_http_client(self) -> None:
        stdout = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_collect_api_config(Path(directory))

            with patch.dict(os.environ, {BIZINFO_CERT_KEY_ENV_VAR: "local-secret"}, clear=False):
                with patch("app.main.BizinfoApiHttpClient", _FakeBizinfoApiHttpClient):
                    with redirect_stdout(stdout):
                        exit_code = main(
                            [
                                "--config",
                                str(config_path),
                                "--action",
                                "collect",
                                "--source-mode",
                                "api",
                            ]
                        )

            self.assertTrue((Path(directory) / "notices.sqlite3").exists())

        lines = stdout.getvalue().splitlines()
        start_event = json.loads(lines[0])
        source_event = json.loads(lines[1])
        summary = json.loads(lines[2])
        finish_event = json.loads(lines[3])

        self.assertEqual(exit_code, 0)
        self.assertEqual(source_event["event_type"], "source_finished")
        self.assertEqual(source_event["source"], "bizinfo")
        self.assertEqual(source_event["fetched_count"], 2)
        self.assertEqual(source_event["saved_count"], 1)
        self.assertEqual(source_event["excluded_count"], 1)
        self.assertEqual(summary["action"], "collect")
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["collected_count"], 2)
        self.assertEqual(summary["saved_count"], 1)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertNotIn("local-secret", stdout.getvalue())
        self.assertEqual(finish_event["status"], "success")
        self.assertEqual(start_event["run_id"], finish_event["run_id"])

    def test_collect_api_mode_without_cert_key_emits_configuration_error(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_collect_api_config(Path(directory))

            with patch.dict(os.environ, {}, clear=True):
                with (
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                    self.assertRaises(SystemExit),
                ):
                    main(
                        [
                            "--config",
                            str(config_path),
                            "--action",
                            "collect",
                            "--source-mode",
                            "api",
                        ]
                    )

        lines = stdout.getvalue().splitlines()
        error_event = json.loads(lines[1])
        finish_event = json.loads(lines[2])

        self.assertIn(BIZINFO_CERT_KEY_ENV_VAR, stderr.getvalue())
        self.assertEqual(error_event["event_type"], "error")
        self.assertEqual(error_event["error_type"], "configuration")
        self.assertNotIn("PROJECT1_BIZINFO_CERT_KEY=", stdout.getvalue())
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "failed")

    def test_g2b_collect_api_mode_without_api_key_emits_configuration_error(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with temporary_directory() as directory:
            config_path = _write_g2b_collect_api_config(Path(directory))

            with patch.dict(os.environ, {}, clear=True):
                with (
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                    self.assertRaises(SystemExit),
                ):
                    main(
                        [
                            "--config",
                            str(config_path),
                            "--action",
                            "collect",
                            "--source-mode",
                            "api",
                        ]
                    )

        lines = stdout.getvalue().splitlines()
        error_event = json.loads(lines[1])
        finish_event = json.loads(lines[2])

        self.assertIn(G2B_API_KEY_ENV_VAR, stderr.getvalue())
        self.assertEqual(error_event["event_type"], "error")
        self.assertEqual(error_event["error_type"], "configuration")
        self.assertNotIn("PROJECT1_G2B_API_KEY=", stdout.getvalue())
        self.assertEqual(finish_event["event_type"], "run_finished")
        self.assertEqual(finish_event["status"], "failed")


def _write_collect_fixture_config(directory: Path) -> Path:
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
core = ["AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"]
supporting = ["데이터", "빅데이터", "클라우드", "인프라", "서버", "네트워크", "보안", "IT서비스", "유지보수"]
exclude = ["채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"]

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


def _write_collect_api_config(directory: Path) -> Path:
    config_path = directory / "settings.toml"
    database_path = directory / "notices.sqlite3"
    output_dir = directory / "output"
    config_path.write_text(
        f"""
[sources.bizinfo]
enabled = true
endpoint = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
timeout_seconds = 5
retry_count = 1
retry_backoff_seconds = 0
page_size = 20

[sources.g2b]
enabled = false

[keywords]
core = ["AI", "DX", "SI"]
supporting = ["data", "cloud", "infra"]
exclude = ["hiring", "training"]

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
source_mode = "api"
""",
        encoding="utf-8",
    )
    return config_path


def _write_g2b_collect_api_config(directory: Path) -> Path:
    config_path = directory / "settings.toml"
    database_path = directory / "notices.sqlite3"
    output_dir = directory / "output"
    config_path.write_text(
        f"""
[sources.bizinfo]
enabled = false

[sources.g2b]
enabled = true
endpoint = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc"
timeout_seconds = 5
retry_count = 1
retry_backoff_seconds = 0
page_size = 20
inquiry_division = "1"
inquiry_window_days = 7

[keywords]
core = ["AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"]
supporting = ["데이터", "빅데이터", "클라우드", "인프라", "서버", "네트워크", "보안", "IT서비스", "유지보수"]
exclude = ["채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"]

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
source_mode = "api"
""",
        encoding="utf-8",
    )
    return config_path


def _write_g2b_collect_fixture_config(directory: Path) -> Path:
    config_path = directory / "settings.toml"
    database_path = directory / "notices.sqlite3"
    output_dir = directory / "output"
    config_path.write_text(
        f"""
[sources.bizinfo]
enabled = false

[sources.g2b]
enabled = true
fixture_path = "tests/fixtures/g2b/bid_notices.json"

[keywords]
core = ["AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"]
supporting = ["데이터", "빅데이터", "클라우드", "인프라", "서버", "네트워크", "보안", "IT서비스", "유지보수"]
exclude = ["채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"]

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


class _FailingSQLiteNoticeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def __enter__(self) -> "_FailingSQLiteNoticeRepository":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def exists(self, key: object) -> bool:
        return False

    def save(self, notice: object, key: object) -> None:
        raise StorageWriteError("sqlite write failed")


class _FakeBizinfoApiHttpClient:
    def __init__(
        self,
        *,
        endpoint: str,
        cert_key: str,
        timeout_seconds: int,
        retry_count: int,
        retry_backoff_seconds: int,
        page_size: int,
    ) -> None:
        self.endpoint = endpoint
        self.cert_key = cert_key
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_backoff_seconds = retry_backoff_seconds
        self.page_size = page_size

    def get_json(self) -> dict[str, object]:
        return {
            "jsonArray": {
                "item": [
                    {
                        "pblancId": "API-BIZ-1",
                        "pblancNm": "AI automation support",
                        "jrsdInsttNm": "MSS",
                        "pblancUrl": "https://www.bizinfo.go.kr/web/view.do?pblancId=API-BIZ-1",
                        "bsnsSumryCn": "AI data support",
                        "creatPnttm": "2026-04-01 09:00:00",
                        "reqstBeginEndDe": "20260401 ~ 20260430",
                        "pblancSttusNm": "접수중",
                    },
                    {
                        "pblancId": "API-BIZ-2",
                        "pblancNm": "Hiring fair",
                        "jrsdInsttNm": "MSS",
                        "pblancUrl": "https://www.bizinfo.go.kr/web/view.do?pblancId=API-BIZ-2",
                        "bsnsSumryCn": "training and hiring support",
                        "creatPnttm": "2026-04-02 09:00:00",
                        "reqstBeginEndDe": "20260402 ~ 20260429",
                        "pblancSttusNm": "접수중",
                    },
                ]
            }
        }


class _FakeG2BApiHttpClient:
    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        timeout_seconds: int,
        retry_count: int,
        retry_backoff_seconds: int,
        page_size: int,
        inquiry_division: str,
        inquiry_window_days: int,
        timezone_name: str,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_backoff_seconds = retry_backoff_seconds
        self.page_size = page_size
        self.inquiry_division = inquiry_division
        self.inquiry_window_days = inquiry_window_days
        self.timezone_name = timezone_name

    def get_json(self) -> dict[str, object]:
        return {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                "body": {
                    "pageNo": 1,
                    "numOfRows": 20,
                    "totalCount": 2,
                    "items": {
                        "item": [
                            {
                                "bidNtceNo": "R26BK90000001",
                                "bidNtceOrd": "000",
                                "bidNtceNm": "AI 기반 정보시스템 통합 구축 용역",
                                "dminsttNm": "한국디지털진흥원",
                                "bidNtceDate": "2026-04-21",
                                "bidClseDate": "2026-05-03 10:00",
                                "bidNtceSttusNm": "공고중",
                                "bidNtceDtlUrl": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK90000001&bidPbancOrd=000",
                                "bidNtceDtlInfo": "AI, 데이터, 클라우드 기반 통합 구축 사업",
                                "bsnsDivNm": "일반용역",
                                "cntrctCnclsMthdNm": "협상에의한계약",
                                "bidMethdNm": "전자입찰",
                            },
                            {
                                "bidNtceNo": "R26BK90000002",
                                "bidNtceOrd": "000",
                                "bidNtceNm": "행사 운영 대행 용역",
                                "dminsttNm": "한국문화지원센터",
                                "bidNtceDate": "2026-04-21",
                                "bidClseDate": "2026-05-04 11:00",
                                "bidNtceSttusNm": "공고중",
                                "bidNtceDtlUrl": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK90000002&bidPbancOrd=000",
                                "bidNtceDtlInfo": "행사 운영 및 현장 진행 대행",
                                "bsnsDivNm": "일반용역",
                                "cntrctCnclsMthdNm": "일반경쟁",
                                "bidMethdNm": "전자입찰",
                            },
                        ]
                    },
                },
            }
        }


def _sheet_names(xml_bytes: bytes) -> tuple[str, ...]:
    root = ElementTree.fromstring(xml_bytes)
    return tuple(
        element.attrib["name"]
        for element in root.findall("s:sheets/s:sheet", SPREADSHEET_NAMESPACES)
    )


def _sheet_rows(xml_bytes: bytes) -> tuple[tuple[str, ...], ...]:
    root = ElementTree.fromstring(xml_bytes)
    rows: list[tuple[str, ...]] = []
    for row in root.findall("s:sheetData/s:row", SPREADSHEET_NAMESPACES):
        rows.append(
            tuple(
                cell.findtext("s:is/s:t", default="", namespaces=SPREADSHEET_NAMESPACES)
                for cell in row.findall("s:c", SPREADSHEET_NAMESPACES)
            )
        )
    return tuple(rows)
