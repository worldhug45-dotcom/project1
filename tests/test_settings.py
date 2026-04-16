from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.infrastructure.settings import ConfigurationError, load_settings


class SettingsTests(TestCase):
    def test_loads_example_settings_file(self) -> None:
        settings = load_settings(Path("config/settings.example.toml"))

        self.assertEqual(settings.app.name, "project1")
        self.assertEqual(settings.runtime.action, "all")
        self.assertEqual(settings.export.support_sheet_name, "support_notices")

    def test_cli_override_wins_over_file(self) -> None:
        settings = load_settings(
            Path("config/settings.example.toml"),
            cli_overrides={"action": "export", "env": "dev"},
        )

        self.assertEqual(settings.runtime.action, "export")
        self.assertEqual(settings.app.env, "dev")

    def test_enabled_collect_source_requires_endpoint(self) -> None:
        with TemporaryDirectory() as directory:
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
                load_settings(config_path)

    def test_export_action_does_not_require_source_endpoint(self) -> None:
        with TemporaryDirectory() as directory:
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
