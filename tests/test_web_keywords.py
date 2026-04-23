import json
import os
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest import TestCase

from app.presentation.web.server import DashboardServerSettings, create_server
from tests.temp_utils import temporary_directory


class WebKeywordsEndpointTests(TestCase):
    def test_keywords_endpoint_reports_effective_keywords_and_override_metadata(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"
            override_path.write_text(
                """
[keywords_override]
add_core = ["security-ai"]
add_supporting = ["integration"]
remove_supporting = ["cloud"]
add_exclude = ["event"]
remove_core = []
remove_exclude = []
""",
                encoding="utf-8",
            )

            status_code, payload = _fetch_keywords(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                )
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["config_path"], str(config_path))
        self.assertEqual(payload["override_path"], str(override_path))
        self.assertTrue(payload["override_exists"])
        self.assertEqual(payload["last_loaded_path"], str(override_path))
        self.assertEqual(payload["keyword_counts"]["core"], 3)
        self.assertEqual(payload["keyword_counts"]["supporting"], 2)
        self.assertEqual(payload["keyword_counts"]["exclude"], 3)
        self.assertEqual(payload["keyword_counts"]["total"], 8)
        self.assertEqual(payload["keywords"]["core"], ["AI", "DX", "security-ai"])
        self.assertEqual(payload["keywords"]["supporting"], ["data", "integration"])
        self.assertEqual(payload["keywords"]["exclude"], ["job", "sales", "event"])
        self.assertEqual(payload["save_meta"]["status"], "not_available")
        self.assertEqual(payload["save_meta"]["changed_group"], "not available")
        self.assertEqual(payload["save_meta"]["target_path"], str(override_path))

    def test_keywords_endpoint_falls_back_to_config_when_override_is_missing(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root).resolve()
            original_cwd = Path.cwd()
            try:
                os.chdir(root)
                status_code, payload = _fetch_keywords(
                    DashboardServerSettings(
                        host="127.0.0.1",
                        port=0,
                        config_path=config_path,
                    )
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["override_path"], "not available")
        self.assertFalse(payload["override_exists"])
        self.assertEqual(payload["last_loaded_path"], str(config_path))
        self.assertEqual(payload["keyword_counts"]["total"], 6)
        self.assertEqual(payload["keywords"]["core"], ["AI", "DX"])
        self.assertEqual(payload["keywords"]["supporting"], ["data", "cloud"])
        self.assertEqual(payload["keywords"]["exclude"], ["job", "sales"])
        self.assertEqual(payload["save_meta"]["status"], "not_available")
        self.assertEqual(
            payload["save_meta"]["target_path"],
            str(config_path.with_name("keywords.override.toml")),
        )

    def test_keywords_endpoint_reports_persisted_save_meta(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"
            override_path.write_text(
                """
[keywords_override]
add_core = ["platform"]
add_supporting = []
add_exclude = []
remove_core = []
remove_supporting = []
remove_exclude = []
""",
                encoding="utf-8",
            )
            override_path.with_suffix(".meta.json").write_text(
                json.dumps(
                    {
                        "status": "success",
                        "saved_at": "2026-04-22T10:11:12+00:00",
                        "target_path": str(override_path),
                        "changed_group": "core",
                        "error_message": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            status_code, payload = _fetch_keywords(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                )
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["save_meta"]["status"], "success")
        self.assertEqual(payload["save_meta"]["saved_at"], "2026-04-22T10:11:12+00:00")
        self.assertEqual(payload["save_meta"]["target_path"], str(override_path))
        self.assertEqual(payload["save_meta"]["changed_group"], "core")

    def test_keywords_endpoint_reports_error_when_settings_cannot_be_loaded(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = root / "missing-settings.toml"

            status_code, payload = _fetch_keywords(
                DashboardServerSettings(
                    host="127.0.0.1",
                    port=0,
                    config_path=config_path,
                )
            )

        self.assertEqual(status_code, 500)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["config_path"], str(config_path))
        self.assertEqual(payload["override_path"], "not available")
        self.assertFalse(payload["override_exists"])
        self.assertEqual(payload["keyword_counts"]["total"], 0)
        self.assertEqual(payload["save_meta"]["status"], "not_available")


def _fetch_keywords(settings: DashboardServerSettings) -> tuple[int, dict[str, object]]:
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        try:
            with urlopen(f"{base_url}/api/keywords") as response:
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
core = ["AI", "DX"]
supporting = ["data", "cloud"]
exclude = ["job", "sales"]

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
