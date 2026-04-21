from pathlib import Path
from unittest import TestCase

from app.infrastructure.settings import (
    BIZINFO_CERT_KEY_ENV_VAR,
    ConfigurationError,
    KEYWORDS_OVERRIDE_PATH_ENV_VAR,
    load_settings,
    resolve_keyword_override_path,
)
from tests.temp_utils import temporary_directory


class SettingsTests(TestCase):
    def test_loads_example_settings_file(self) -> None:
        settings = load_settings(
            Path("config/settings.example.toml"),
            environ={BIZINFO_CERT_KEY_ENV_VAR: "dummy-key"},
        )

        self.assertEqual(settings.app.name, "project1")
        self.assertEqual(settings.runtime.action, "all")
        self.assertEqual(settings.runtime.source_mode, "api")
        self.assertEqual(settings.export.support_sheet_name, "support_notices")
        self.assertEqual(settings.sources.bizinfo.cert_key, "dummy-key")

    def test_cli_override_wins_over_file(self) -> None:
        settings = load_settings(
            Path("config/settings.example.toml"),
            cli_overrides={"action": "export", "env": "dev"},
            environ={BIZINFO_CERT_KEY_ENV_VAR: "dummy-key"},
        )

        self.assertEqual(settings.runtime.action, "export")
        self.assertEqual(settings.app.env, "dev")

    def test_fixture_source_mode_requires_existing_bizinfo_fixture(self) -> None:
        with temporary_directory() as directory:
            fixture_path = Path(directory) / "bizinfo.json"
            fixture_path.write_text('{"items": []}', encoding="utf-8")
            config_path = Path(directory) / "settings.toml"
            config_path.write_text(
                f"""
[sources.bizinfo]
enabled = true
fixture_path = "{fixture_path.as_posix()}"

[sources.g2b]
enabled = true

[runtime]
action = "collect"
source_mode = "fixture"

[keywords]
core = ["AI"]
supporting = ["데이터"]
exclude = ["채용"]
""",
                encoding="utf-8",
            )

            settings = load_settings(config_path)

        self.assertEqual(settings.runtime.source_mode, "fixture")
        self.assertEqual(settings.sources.bizinfo.fixture_path, fixture_path)

    def test_enabled_collect_source_requires_endpoint(self) -> None:
        with temporary_directory() as directory:
            config_path = Path(directory) / "settings.toml"
            config_path.write_text(
                """
[sources.bizinfo]
enabled = true
endpoint = ""

[sources.g2b]
enabled = false

[runtime]
action = "collect"

[keywords]
core = ["AI"]
supporting = ["데이터"]
exclude = ["채용"]
""",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigurationError):
                load_settings(config_path, environ={BIZINFO_CERT_KEY_ENV_VAR: "dummy-key"})

    def test_collect_api_mode_requires_bizinfo_cert_key_from_env(self) -> None:
        with temporary_directory() as directory:
            config_path = Path(directory) / "settings.toml"
            config_path.write_text(
                """
[sources.bizinfo]
enabled = true
endpoint = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

[sources.g2b]
enabled = false

[runtime]
action = "collect"
source_mode = "api"

[keywords]
core = ["AI"]
supporting = ["데이터"]
exclude = ["채용"]
""",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigurationError) as context:
                load_settings(config_path, environ={})

        self.assertIn(BIZINFO_CERT_KEY_ENV_VAR, str(context.exception))

    def test_export_action_does_not_require_source_endpoint(self) -> None:
        with temporary_directory() as directory:
            config_path = Path(directory) / "settings.toml"
            config_path.write_text(
                """
[sources.bizinfo]
enabled = true
endpoint = ""

[sources.g2b]
enabled = false

[runtime]
action = "export"

[keywords]
core = ["AI"]
supporting = ["데이터"]
exclude = ["채용"]
""",
                encoding="utf-8",
            )

            settings = load_settings(config_path)

        self.assertEqual(settings.runtime.action, "export")

    def test_keyword_override_file_adds_and_removes_keywords(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = root / "settings.toml"
            override_path = root / "keywords.override.toml"
            config_path.write_text(
                """
[sources.bizinfo]
enabled = true
fixture_path = "tests/fixtures/bizinfo/support_notices.json"

[sources.g2b]
enabled = false

[runtime]
action = "collect"
source_mode = "fixture"

[keywords]
core = ["AI"]
supporting = ["데이터", "클라우드"]
exclude = ["채용", "문화"]
""",
                encoding="utf-8",
            )
            override_path.write_text(
                """
[keywords_override]
add_core = ["보안 AI"]
add_supporting = ["국방기술", "클라우드"]
remove_supporting = ["데이터"]
remove_exclude = ["문화"]
add_exclude = ["행사"]
""",
                encoding="utf-8",
            )

            settings = load_settings(config_path)

        self.assertEqual(settings.keywords.core, ("AI", "보안 AI"))
        self.assertEqual(settings.keywords.supporting, ("클라우드", "국방기술"))
        self.assertEqual(settings.keywords.exclude, ("채용", "행사"))

    def test_keyword_override_env_path_wins_when_present(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = root / "settings.toml"
            nested_override_path = root / "custom" / "ops-keywords.toml"
            nested_override_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                """
[sources.bizinfo]
enabled = true
fixture_path = "tests/fixtures/bizinfo/support_notices.json"

[sources.g2b]
enabled = false

[runtime]
action = "collect"
source_mode = "fixture"

[keywords]
core = ["AI"]
supporting = ["데이터"]
exclude = ["채용"]
""",
                encoding="utf-8",
            )
            nested_override_path.write_text(
                """
[keywords_override]
add_supporting = ["전자전"]
""",
                encoding="utf-8",
            )

            resolved_path = resolve_keyword_override_path(
                config_path,
                {KEYWORDS_OVERRIDE_PATH_ENV_VAR: str(nested_override_path)},
            )
            settings = load_settings(
                config_path,
                environ={KEYWORDS_OVERRIDE_PATH_ENV_VAR: str(nested_override_path)},
            )

        self.assertEqual(resolved_path, nested_override_path)
        self.assertEqual(settings.keywords.supporting, ("데이터", "전자전"))
