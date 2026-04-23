import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import TestCase
from unittest.mock import patch

from app.presentation.web.server import DashboardServerSettings, create_server
from tests.temp_utils import temporary_directory


class WebSettingsTests(TestCase):
    def test_settings_snapshot_exposes_source_state_and_masked_api_keys(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "settings.override.toml"
            env_local_path = root / ".env.local"
            override_path.write_text(
                """
[sources.g2b]
enabled = true

[[extra_sources]]
name = "New Source"
endpoint = "https://example.com/api"
api_key_env_var = "PROJECT1_NEW_SOURCE_API_KEY"
enabled = false
description = "draft source"
""".strip()
                + "\n",
                encoding="utf-8",
            )
            env_local_path.write_text(
                """
PROJECT1_G2B_API_KEY=abcdefghij
""".strip()
                + "\n",
                encoding="utf-8",
            )

            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                status_code, payload = _fetch_json(settings, "/api/settings")

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["config_path"], str(config_path))
        self.assertEqual(payload["override_path"], str(override_path))
        self.assertTrue(payload["override_exists"])
        self.assertEqual(payload["env_local_path"], str(env_local_path))
        self.assertTrue(payload["env_local_exists"])
        self.assertEqual(payload["current_source_mode"], "fixture")
        self.assertTrue(payload["sources"]["bizinfo"]["enabled"])
        self.assertTrue(payload["sources"]["g2b"]["enabled"])
        self.assertEqual(payload["sources"]["g2b"]["api_key_env_var"], "PROJECT1_G2B_API_KEY")
        self.assertTrue(payload["sources"]["g2b"]["api_key_configured"])
        self.assertNotEqual(payload["sources"]["g2b"]["api_key_masked"], "abcdefghij")
        self.assertEqual(len(payload["extra_sources"]), 1)
        self.assertEqual(payload["extra_sources"][0]["name"], "New Source")
        self.assertEqual(payload["save_meta"]["status"], "not_available")

    def test_source_settings_save_updates_override_and_snapshot(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "settings.override.toml"
            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                save_status_code, save_payload = _post_json(
                    settings,
                    "/api/settings/sources",
                    {
                        "source_mode": "api",
                        "sources": {
                            "bizinfo": {"enabled": False},
                            "g2b": {"enabled": True},
                        },
                        "extra_sources": [
                            {
                                "name": "Vendor API",
                                "endpoint": "https://example.com/vendor",
                                "api_key_env_var": "PROJECT1_VENDOR_API_KEY",
                                "enabled": False,
                                "description": "future onboarding",
                            }
                        ],
                    },
                )
                get_status_code, get_payload = _fetch_json(settings, "/api/settings")

            override_text = override_path.read_text(encoding="utf-8")

        self.assertEqual(save_status_code, 200)
        self.assertTrue(save_payload["saved"])
        save_payload_text = json.dumps(save_payload, ensure_ascii=False)
        self.assertNotIn("12345678", save_payload_text)
        self.assertNotIn("abcdefghij", save_payload_text)
        snapshot = save_payload["settings_snapshot"]
        self.assertEqual(snapshot["save_meta"]["status"], "success")
        self.assertEqual(snapshot["save_meta"]["changed_section"], "sources")
        self.assertEqual(snapshot["save_meta"]["target_path"], str(override_path))
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["current_source_mode"], "api")
        self.assertFalse(get_payload["sources"]["bizinfo"]["enabled"])
        self.assertTrue(get_payload["sources"]["g2b"]["enabled"])
        self.assertEqual(len(get_payload["extra_sources"]), 1)
        self.assertEqual(get_payload["extra_sources"][0]["name"], "Vendor API")
        self.assertIn("[runtime]", override_text)
        self.assertIn('source_mode = "api"', override_text)
        self.assertIn("[sources.bizinfo]", override_text)
        self.assertIn("[sources.g2b]", override_text)
        self.assertIn("enabled = false", override_text)
        self.assertIn("[[extra_sources]]", override_text)
        self.assertIn('api_key_env_var = "PROJECT1_VENDOR_API_KEY"', override_text)

    def test_source_settings_save_rejects_enabling_both_built_in_sources(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "settings.override.toml"
            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                save_status_code, save_payload = _post_json(
                    settings,
                    "/api/settings/sources",
                    {
                        "source_mode": "fixture",
                        "sources": {
                            "bizinfo": {"enabled": True},
                            "g2b": {"enabled": True},
                        },
                        "extra_sources": [],
                    },
                )
                get_status_code, get_payload = _fetch_json(settings, "/api/settings")

        self.assertEqual(save_status_code, 400)
        self.assertFalse(save_payload["saved"])
        self.assertIn(
            "Collect currently supports one enabled source at a time.",
            save_payload["error_message"],
        )
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["save_meta"]["status"], "failed")
        self.assertEqual(get_payload["save_meta"]["changed_section"], "sources")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(override_path))
        self.assertIn(
            "Collect currently supports one enabled source at a time.",
            get_payload["save_meta"]["error_message"],
        )

    def test_source_settings_save_rejects_disabling_all_built_in_sources(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            override_path = root / "settings.override.toml"
            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                save_status_code, save_payload = _post_json(
                    settings,
                    "/api/settings/sources",
                    {
                        "sources": {
                            "bizinfo": {"enabled": False},
                            "g2b": {"enabled": False},
                        },
                        "extra_sources": [],
                    },
                )
                get_status_code, get_payload = _fetch_json(settings, "/api/settings")

        self.assertEqual(save_status_code, 400)
        self.assertFalse(save_payload["saved"])
        self.assertIn(
            "At least one built-in source must remain enabled.",
            save_payload["error_message"],
        )
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["save_meta"]["status"], "failed")
        self.assertEqual(get_payload["save_meta"]["changed_section"], "sources")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(override_path))
        self.assertEqual(
            get_payload["save_meta"]["error_message"],
            "At least one built-in source must remain enabled.",
        )

    def test_api_key_settings_save_updates_env_local_and_masks_values(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            env_local_path = root / ".env.local"
            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                save_status_code, save_payload = _post_json(
                    settings,
                    "/api/settings/api-keys",
                    {
                        "bizinfo_api_key": "12345678",
                        "g2b_api_key": "abcdefghij",
                    },
                )
                get_status_code, get_payload = _fetch_json(settings, "/api/settings")

            env_text = env_local_path.read_text(encoding="utf-8")

        self.assertEqual(save_status_code, 200)
        self.assertTrue(save_payload["saved"])
        snapshot = save_payload["settings_snapshot"]
        self.assertEqual(snapshot["save_meta"]["status"], "success")
        self.assertEqual(snapshot["save_meta"]["changed_section"], "api_keys")
        self.assertEqual(snapshot["save_meta"]["target_path"], str(env_local_path))
        self.assertEqual(get_status_code, 200)
        self.assertTrue(get_payload["env_local_exists"])
        self.assertTrue(get_payload["sources"]["bizinfo"]["api_key_configured"])
        self.assertTrue(get_payload["sources"]["g2b"]["api_key_configured"])
        self.assertNotEqual(get_payload["sources"]["bizinfo"]["api_key_masked"], "12345678")
        self.assertNotEqual(get_payload["sources"]["g2b"]["api_key_masked"], "abcdefghij")
        self.assertIn("PROJECT1_BIZINFO_CERT_KEY=12345678", env_text)
        self.assertIn("PROJECT1_G2B_API_KEY=abcdefghij", env_text)

    def test_api_key_settings_save_rejects_empty_payload(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            env_local_path = root / ".env.local"
            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                save_status_code, save_payload = _post_json(
                    settings,
                    "/api/settings/api-keys",
                    {
                        "bizinfo_api_key": "   ",
                        "g2b_api_key": "",
                    },
                )
                get_status_code, get_payload = _fetch_json(settings, "/api/settings")

        self.assertEqual(save_status_code, 400)
        self.assertFalse(save_payload["saved"])
        self.assertIn(
            "At least one API key value must be provided.",
            save_payload["error_message"],
        )
        self.assertEqual(get_status_code, 200)
        self.assertEqual(get_payload["save_meta"]["status"], "failed")
        self.assertEqual(get_payload["save_meta"]["changed_section"], "api_keys")
        self.assertEqual(get_payload["save_meta"]["target_path"], str(env_local_path))
        self.assertEqual(
            get_payload["save_meta"]["error_message"],
            "At least one API key value must be provided.",
        )

    def test_api_key_settings_save_rejects_multiline_secret_without_leaking_value(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            settings = DashboardServerSettings(
                host="127.0.0.1",
                port=0,
                config_path=config_path,
            )

            with patch.dict(os.environ, {}, clear=True):
                save_status_code, save_payload = _post_json(
                    settings,
                    "/api/settings/api-keys",
                    {
                        "bizinfo_api_key": "secret-line-1\nsecret-line-2",
                    },
                )

        response_text = json.dumps(save_payload, ensure_ascii=False)
        self.assertEqual(save_status_code, 400)
        self.assertFalse(save_payload["saved"])
        self.assertNotIn("secret-line-1", response_text)
        self.assertNotIn("secret-line-2", response_text)
        self.assertIn("PROJECT1_BIZINFO_CERT_KEY", save_payload["error_message"])


@contextmanager
def _serve(settings: DashboardServerSettings):
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield base_url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _fetch_json(settings: DashboardServerSettings, path: str) -> tuple[int, dict[str, object]]:
    with _serve(settings) as base_url:
        try:
            with urlopen(f"{base_url}{path}") as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))


def _post_json(
    settings: DashboardServerSettings,
    path: str,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    with _serve(settings) as base_url:
        request = Request(
            f"{base_url}{path}",
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))


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
