import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import TestCase

from app.presentation.web.server import DashboardServerSettings, create_server
from tests.temp_utils import temporary_directory


class WebKeywordEditTests(TestCase):
    def test_core_keyword_save_updates_override_and_snapshot(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"
            override_path.write_text(
                """
[keywords_override]
add_core = ["iot"]
add_supporting = ["legacy"]
add_exclude = ["sales"]
remove_core = []
remove_supporting = ["cloud"]
remove_exclude = []
""",
                encoding="utf-8",
            )

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            status_code, payload = _post_core_keywords(
                settings,
                {
                    "core_keywords": [
                        "AI",
                        "platform",
                        "DX",
                        "Platform",
                        "   ",
                        "platform",
                    ]
                },
            )

            override_text = override_path.read_text(encoding="utf-8")

        self.assertEqual(status_code, 200)
        self.assertTrue(payload["saved"])
        snapshot = payload["keywords_snapshot"]
        self.assertEqual(snapshot["keywords"]["core"], ["AI", "DX", "platform"])
        self.assertEqual(snapshot["keywords"]["supporting"], ["data", "legacy"])
        self.assertEqual(snapshot["keywords"]["exclude"], ["job", "sales"])
        self.assertEqual(snapshot["override_path"], str(override_path))
        self.assertTrue(snapshot["override_exists"])
        self.assertEqual(snapshot["save_meta"]["status"], "success")
        self.assertEqual(snapshot["save_meta"]["changed_group"], "core")
        self.assertEqual(snapshot["save_meta"]["target_path"], str(override_path))
        self.assertNotEqual(snapshot["save_meta"]["saved_at"], "not available")
        self.assertIn('add_core = ["platform"]', override_text)
        self.assertIn("remove_core = []", override_text)
        self.assertIn('add_supporting = ["legacy"]', override_text)
        self.assertIn('add_exclude = ["sales"]', override_text)
        self.assertIn('remove_supporting = ["cloud"]', override_text)

    def test_core_keyword_save_rejects_empty_keyword_list(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            status_code, payload = _post_core_keywords(
                settings,
                {"core_keywords": ["   ", ""]},
            )

        self.assertEqual(status_code, 400)
        self.assertFalse(payload["saved"])
        self.assertIn("Core keywords must not be empty.", payload["error_message"])

    def test_core_keyword_save_creates_override_file_and_get_reflects_it(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            save_status_code, save_payload = _post_core_keywords(
                settings,
                {"core_keywords": ["AI", "platform"]},
            )
            get_status_code, get_payload = _fetch_keywords(settings)
            override_exists = override_path.exists()

        self.assertEqual(save_status_code, 200)
        self.assertTrue(save_payload["saved"])
        self.assertTrue(override_exists)
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["status"], "ready")
        self.assertEqual(get_payload["override_path"], str(override_path))
        self.assertTrue(get_payload["override_exists"])
        self.assertEqual(get_payload["last_loaded_path"], str(override_path))
        self.assertEqual(get_payload["keywords"]["core"], ["AI", "platform"])
        self.assertEqual(get_payload["save_meta"]["status"], "success")
        self.assertEqual(get_payload["save_meta"]["changed_group"], "core")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(override_path))

    def test_failed_core_keyword_save_persists_failure_meta_for_refresh(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            save_status_code, save_payload = _post_core_keywords(
                settings,
                {"core_keywords": ["   ", ""]},
            )
            get_status_code, get_payload = _fetch_keywords(settings)

        self.assertEqual(save_status_code, 400)
        self.assertFalse(save_payload["saved"])
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["save_meta"]["status"], "failed")
        self.assertEqual(get_payload["save_meta"]["changed_group"], "core")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(override_path))
        self.assertEqual(
            get_payload["save_meta"]["error_message"],
            "Core keywords must not be empty.",
        )

    def test_supporting_keyword_save_updates_override_and_snapshot(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"
            override_path.write_text(
                """
[keywords_override]
add_core = ["iot"]
add_supporting = ["legacy"]
add_exclude = ["sales"]
remove_core = []
remove_supporting = ["cloud"]
remove_exclude = []
""",
                encoding="utf-8",
            )

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            status_code, payload = _post_supporting_keywords(
                settings,
                {
                    "supporting_keywords": [
                        "cloud",
                        "platform",
                        "data",
                        "Cloud",
                        "   ",
                        "platform",
                    ]
                },
            )

            override_text = override_path.read_text(encoding="utf-8")

        self.assertEqual(status_code, 200)
        self.assertTrue(payload["saved"])
        snapshot = payload["keywords_snapshot"]
        self.assertEqual(snapshot["keywords"]["core"], ["AI", "DX", "iot"])
        self.assertEqual(snapshot["keywords"]["supporting"], ["data", "cloud", "platform"])
        self.assertEqual(snapshot["keywords"]["exclude"], ["job", "sales"])
        self.assertEqual(snapshot["override_path"], str(override_path))
        self.assertTrue(snapshot["override_exists"])
        self.assertEqual(snapshot["save_meta"]["status"], "success")
        self.assertEqual(snapshot["save_meta"]["changed_group"], "supporting")
        self.assertEqual(snapshot["save_meta"]["target_path"], str(override_path))
        self.assertIn('add_core = ["iot"]', override_text)
        self.assertIn('add_exclude = ["sales"]', override_text)
        self.assertIn('add_supporting = ["platform"]', override_text)
        self.assertIn("remove_supporting = []", override_text)

    def test_supporting_keyword_save_rejects_empty_keyword_list(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            status_code, payload = _post_supporting_keywords(
                settings,
                {"supporting_keywords": ["   ", ""]},
            )

        self.assertEqual(status_code, 400)
        self.assertFalse(payload["saved"])
        self.assertIn("Supporting keywords must not be empty.", payload["error_message"])

    def test_supporting_keyword_save_creates_override_file_and_get_reflects_it(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            save_status_code, save_payload = _post_supporting_keywords(
                settings,
                {"supporting_keywords": ["data", "platform"]},
            )
            get_status_code, get_payload = _fetch_keywords(settings)
            override_exists = override_path.exists()

        self.assertEqual(save_status_code, 200)
        self.assertTrue(save_payload["saved"])
        self.assertTrue(override_exists)
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["status"], "ready")
        self.assertEqual(get_payload["override_path"], str(override_path))
        self.assertTrue(get_payload["override_exists"])
        self.assertEqual(get_payload["last_loaded_path"], str(override_path))
        self.assertEqual(get_payload["keywords"]["supporting"], ["data", "platform"])
        self.assertEqual(get_payload["save_meta"]["status"], "success")
        self.assertEqual(get_payload["save_meta"]["changed_group"], "supporting")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(override_path))

    def test_exclude_keyword_save_updates_override_and_snapshot(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"
            override_path.write_text(
                """
[keywords_override]
add_core = ["iot"]
add_supporting = ["legacy"]
add_exclude = ["sales"]
remove_core = []
remove_supporting = ["cloud"]
remove_exclude = []
""",
                encoding="utf-8",
            )

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            status_code, payload = _post_exclude_keywords(
                settings,
                {
                    "exclude_keywords": [
                        "job",
                        "audit",
                        "Audit",
                        "   ",
                        "audit",
                    ]
                },
            )

            override_text = override_path.read_text(encoding="utf-8")

        self.assertEqual(status_code, 200)
        self.assertTrue(payload["saved"])
        snapshot = payload["keywords_snapshot"]
        self.assertEqual(snapshot["keywords"]["core"], ["AI", "DX", "iot"])
        self.assertEqual(snapshot["keywords"]["supporting"], ["data", "legacy"])
        self.assertEqual(snapshot["keywords"]["exclude"], ["job", "audit"])
        self.assertEqual(snapshot["override_path"], str(override_path))
        self.assertTrue(snapshot["override_exists"])
        self.assertEqual(snapshot["save_meta"]["status"], "success")
        self.assertEqual(snapshot["save_meta"]["changed_group"], "exclude")
        self.assertEqual(snapshot["save_meta"]["target_path"], str(override_path))
        self.assertIn('add_core = ["iot"]', override_text)
        self.assertIn('add_supporting = ["legacy"]', override_text)
        self.assertIn('remove_supporting = ["cloud"]', override_text)
        self.assertIn('add_exclude = ["audit"]', override_text)
        self.assertIn("remove_exclude = []", override_text)

    def test_exclude_keyword_save_rejects_empty_keyword_list(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            status_code, payload = _post_exclude_keywords(
                settings,
                {"exclude_keywords": ["   ", ""]},
            )

        self.assertEqual(status_code, 400)
        self.assertFalse(payload["saved"])
        self.assertIn("Exclude keywords must not be empty.", payload["error_message"])

    def test_exclude_keyword_save_creates_override_file_and_get_reflects_it(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "keywords.override.toml"

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )
            save_status_code, save_payload = _post_exclude_keywords(
                settings,
                {"exclude_keywords": ["job", "audit"]},
            )
            get_status_code, get_payload = _fetch_keywords(settings)
            override_exists = override_path.exists()

        self.assertEqual(save_status_code, 200)
        self.assertTrue(save_payload["saved"])
        self.assertTrue(override_exists)
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["status"], "ready")
        self.assertEqual(get_payload["override_path"], str(override_path))
        self.assertTrue(get_payload["override_exists"])
        self.assertEqual(get_payload["last_loaded_path"], str(override_path))
        self.assertEqual(get_payload["keywords"]["exclude"], ["job", "audit"])
        self.assertEqual(get_payload["save_meta"]["status"], "success")
        self.assertEqual(get_payload["save_meta"]["changed_group"], "exclude")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(override_path))


def _post_core_keywords(
    settings: DashboardServerSettings,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    request = Request(
        f"{base_url}/api/keywords/core",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        try:
            with urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _post_supporting_keywords(
    settings: DashboardServerSettings,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    request = Request(
        f"{base_url}/api/keywords/supporting",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        try:
            with urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _post_exclude_keywords(
    settings: DashboardServerSettings,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    request = Request(
        f"{base_url}/api/keywords/exclude",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        try:
            with urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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
