import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest import TestCase

from app.ops.observation import (
    CollectObservationRecord,
    NoticeObservationExample,
    save_observation_history,
)
from app.presentation.web.server import DashboardServerSettings, create_server
from tests.temp_utils import temporary_directory


class WebHealthEndpointTests(TestCase):
    def test_health_endpoint_reports_ok_when_settings_and_runtime_files_are_available(
        self,
    ) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            history_path = root / "history.json"
            state_path = root / "manual_state.json"
            _write_observation_history(history_path)
            state_path.write_text(
                json.dumps({"updated_at": "2026-04-21T13:00:00+00:00", "actions": {}}),
                encoding="utf-8",
            )

            status_code, payload = _fetch_health(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                    history_path=history_path,
                    state_path=state_path,
                )
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["app_name"], "project1")
        self.assertEqual(payload["config_path"], str(config_path))
        self.assertEqual(payload["sqlite_db_path"], str(root / "notices.sqlite3"))
        self.assertEqual(payload["export_output_dir"], str(root / "output"))
        self.assertTrue(payload["settings_loaded"])
        self.assertTrue(payload["state_file_accessible"])
        self.assertTrue(payload["observation_history_exists"])
        self.assertIsInstance(payload["server_time"], str)

    def test_health_endpoint_reports_degraded_when_optional_runtime_files_are_missing(
        self,
    ) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            history_path = root / "missing_history.json"
            state_path = root / "missing_state.json"

            status_code, payload = _fetch_health(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                    history_path=history_path,
                    state_path=state_path,
                )
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["status"], "degraded")
        self.assertTrue(payload["settings_loaded"])
        self.assertFalse(payload["state_file_accessible"])
        self.assertFalse(payload["observation_history_exists"])
        self.assertEqual(payload["sqlite_db_path"], str(root / "notices.sqlite3"))
        self.assertEqual(payload["export_output_dir"], str(root / "output"))

    def test_health_endpoint_reports_error_when_settings_cannot_be_loaded(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = root / "missing_settings.toml"
            history_path = root / "history.json"
            state_path = root / "manual_state.json"

            status_code, payload = _fetch_health(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                    history_path=history_path,
                    state_path=state_path,
                )
            )

        self.assertEqual(status_code, 503)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["app_name"], "project1")
        self.assertEqual(payload["config_path"], str(config_path))
        self.assertEqual(payload["sqlite_db_path"], "not available")
        self.assertEqual(payload["export_output_dir"], "not available")
        self.assertFalse(payload["settings_loaded"])
        self.assertFalse(payload["state_file_accessible"])
        self.assertFalse(payload["observation_history_exists"])


def _fetch_health(settings: DashboardServerSettings) -> tuple[int, dict[str, object]]:
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        try:
            with urlopen(f"{base_url}/health") as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _write_fixture_config(directory: Path) -> Path:
    config_path = directory / "settings.toml"
    database_path = directory / "notices.sqlite3"
    output_dir = directory / "output"
    config_path.write_text(
        f"""
[app]
name = "project1"

[sources.bizinfo]
enabled = true
fixture_path = "tests/fixtures/bizinfo/support_notices.json"

[sources.g2b]
enabled = false

[keywords]
core = ["AI", "DX", "SI"]
supporting = ["data", "cloud", "infra", "security", "it_service", "maintenance"]
exclude = ["hiring", "training", "event"]

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
