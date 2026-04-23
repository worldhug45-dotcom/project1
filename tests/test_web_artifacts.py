import json
import os
import threading
from pathlib import Path
from urllib.request import urlopen
from unittest import TestCase

from app.presentation.web.server import DashboardServerSettings, create_server
from tests.temp_utils import temporary_directory


class WebArtifactsTests(TestCase):
    def test_status_payload_exposes_recent_artifacts_with_open_and_download_urls(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            history_path = root / "history.json"
            raw_output_dir = root / "raw"
            log_path = root / "report.md"
            state_path = root / "manual_state.json"
            output_dir = root / "output"
            exported_file = output_dir / "notices_20260423_run.xlsx"
            raw_file = raw_output_dir / "20260423.jsonl"

            output_dir.mkdir(parents=True, exist_ok=True)
            raw_output_dir.mkdir(parents=True, exist_ok=True)
            exported_file.write_bytes(b"fake-xlsx")
            raw_file.write_text('{"event":"latest"}\n', encoding="utf-8")
            log_path.write_text("# report\n", encoding="utf-8")
            history_path.write_text("[]\n", encoding="utf-8")
            state_path.write_text(
                json.dumps({"updated_at": "2026-04-23T00:30:00+00:00", "actions": {}}),
                encoding="utf-8",
            )
            os.utime(exported_file, (1_713_916_800, 1_713_916_800))
            os.utime(log_path, (1_713_873_600, 1_713_873_600))
            os.utime(raw_file, (1_713_960_000, 1_713_960_000))

            server = create_server(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                    history_path=history_path,
                    raw_output_dir=raw_output_dir,
                    log_path=log_path,
                    state_path=state_path,
                )
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                payload = json.loads(urlopen(f"{base_url}/api/status").read().decode("utf-8"))
                export_item = next(
                    item for item in payload["artifacts"] if item["kind"] == "export_result"
                )
                report_item = next(
                    item for item in payload["artifacts"] if item["kind"] == "observation_report"
                )
                raw_item = next(
                    item for item in payload["artifacts"] if item["kind"] == "observation_raw"
                )

                with urlopen(f"{base_url}{export_item['download_url']}") as response:
                    export_bytes = response.read()
                    export_disposition = response.headers.get("Content-Disposition", "")

                with urlopen(f"{base_url}{report_item['open_url']}") as response:
                    report_text = response.read().decode("utf-8")

                with urlopen(f"{base_url}{raw_item['open_url']}") as response:
                    raw_text = response.read().decode("utf-8")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertEqual(export_item["group"], "export")
        self.assertEqual(export_item["name"], exported_file.name)
        self.assertEqual(export_item["status"], "available")
        self.assertTrue(export_item["open_url"].startswith("/artifacts/export/"))
        self.assertTrue(export_item["download_url"].startswith("/artifacts/export/"))
        self.assertEqual(report_item["group"], "observation")
        self.assertEqual(report_item["name"], log_path.name)
        self.assertEqual(report_item["open_url"], "/artifacts/report")
        self.assertEqual(report_item["download_url"], "/artifacts/report?download=1")
        self.assertEqual(raw_item["group"], "observation")
        self.assertTrue(raw_item["open_url"].startswith("/artifacts/raw/"))
        self.assertEqual(export_bytes, b"fake-xlsx")
        self.assertIn(exported_file.name, export_disposition)
        self.assertIn("# report", report_text)
        self.assertIn('"event":"latest"', raw_text)


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
core = ["AI", "DX"]
supporting = ["data", "cloud"]
exclude = ["job"]

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
