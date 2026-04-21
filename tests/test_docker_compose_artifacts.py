from pathlib import Path
from unittest import TestCase


class DockerComposeArtifactsTests(TestCase):
    def test_dockerfile_runs_existing_web_server_module(self) -> None:
        content = Path("Dockerfile").read_text(encoding="utf-8")
        self.assertIn('"python", "-m", "app.presentation.web.server"', content)
        self.assertIn("config/settings.docker.toml", content)
        self.assertIn("EXPOSE 8787", content)

    def test_compose_binds_runtime_directories_and_healthcheck(self) -> None:
        content = Path("compose.yaml").read_text(encoding="utf-8")
        self.assertIn("./config:/workspace/config", content)
        self.assertIn("./data:/workspace/data", content)
        self.assertIn("./output:/workspace/output", content)
        self.assertIn("./doc:/workspace/doc", content)
        self.assertIn("http://127.0.0.1:8787/health", content)
        self.assertIn("PROJECT1_BIZINFO_CERT_KEY", content)
        self.assertIn("PROJECT1_G2B_API_KEY", content)
        self.assertIn("PROJECT1_KEYWORDS_OVERRIDE_PATH", content)
        self.assertIn("PROJECT1_STORAGE_DATABASE_PATH", content)
        self.assertIn("PROJECT1_EXPORT_OUTPUT_DIR", content)

    def test_api_override_enables_runtime_source_mode_api(self) -> None:
        content = Path("compose.api.yaml").read_text(encoding="utf-8")
        self.assertIn("PROJECT1_RUNTIME_SOURCE_MODE: api", content)
        self.assertIn("PROJECT1_SOURCES_BIZINFO_ENABLED", content)
        self.assertIn("PROJECT1_SOURCES_G2B_ENABLED", content)
        self.assertIn("PROJECT1_BIZINFO_CERT_KEY", content)
        self.assertIn("PROJECT1_G2B_API_KEY", content)
        self.assertIn("PROJECT1_KEYWORDS_OVERRIDE_PATH", content)
        self.assertIn("PROJECT1_STORAGE_DATABASE_PATH", content)
        self.assertIn("PROJECT1_EXPORT_OUTPUT_DIR", content)

    def test_env_example_and_docker_settings_exist(self) -> None:
        env_content = Path(".env.example").read_text(encoding="utf-8")
        settings_content = Path("config/settings.docker.toml").read_text(encoding="utf-8")
        override_content = Path("config/keywords.docker.override.toml").read_text(
            encoding="utf-8"
        )

        self.assertIn("PROJECT1_BIZINFO_CERT_KEY", env_content)
        self.assertIn("PROJECT1_G2B_API_KEY", env_content)
        self.assertIn("PROJECT1_KEYWORDS_OVERRIDE_PATH", env_content)
        self.assertIn("PROJECT1_SOURCES_BIZINFO_ENABLED", env_content)
        self.assertIn("PROJECT1_SOURCES_G2B_ENABLED", env_content)
        self.assertIn('source_mode = "fixture"', settings_content)
        self.assertIn("[keywords_override]", override_content)

    def test_docker_doc_describes_fixture_and_api_commands(self) -> None:
        content = Path("doc/docker_local_dashboard.md").read_text(encoding="utf-8")
        self.assertIn("docker compose up --build", content)
        self.assertIn("docker compose -f compose.yaml -f compose.api.yaml up --build", content)
        self.assertIn("docker compose down", content)
