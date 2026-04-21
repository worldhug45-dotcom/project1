import json
import threading
from pathlib import Path
from urllib.request import urlopen
from unittest import TestCase

from app.ops.observation import CollectObservationRecord, NoticeObservationExample, save_observation_history
from app.presentation.web.server import DashboardServerSettings, create_server
from tests.temp_utils import temporary_directory


class WebDashboardTests(TestCase):
    def test_dashboard_root_and_status_endpoint_render(self) -> None:
        with temporary_directory() as directory:
            root = Path(directory)
            config_path = _write_fixture_config(root)
            history_path = root / "history.json"
            raw_output_dir = root / "raw"
            log_path = root / "report.md"
            state_path = root / "manual_state.json"
            output_dir = root / "output"
            latest_xlsx = output_dir / "notices_20260421_run.xlsx"

            output_dir.mkdir(parents=True, exist_ok=True)
            latest_xlsx.write_bytes(b"fake-xlsx")
            raw_output_dir.mkdir(parents=True, exist_ok=True)
            (raw_output_dir / "latest.jsonl").write_text("{}\n", encoding="utf-8")
            log_path.write_text("# report\n", encoding="utf-8")
            _write_observation_history(history_path)
            state_path.write_text(
                json.dumps(
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
                                "error_count": 0,
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

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
                html = urlopen(f"{base_url}/").read().decode("utf-8")
                status_payload = json.loads(
                    urlopen(f"{base_url}/api/status").read().decode("utf-8")
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertIn("Project1 Operator Dashboard", html)
        self.assertIn("/api/status", html)
        self.assertIn("/api/keywords", html)
        self.assertIn("/api/keywords/core", html)
        self.assertIn("/api/keywords/supporting", html)
        self.assertIn("/api/keywords/exclude", html)
        self.assertIn("/health", html)
        self.assertIn("/actions/collect", html)
        self.assertIn("/actions/export", html)
        self.assertIn("/actions/observe", html)
        self.assertIn('data-keywords-url="/api/keywords"', html)
        self.assertIn(
            'data-keywords-core-save-url="/api/keywords/core"',
            html,
        )
        self.assertIn(
            'data-keywords-supporting-save-url="/api/keywords/supporting"',
            html,
        )
        self.assertIn(
            'data-keywords-exclude-save-url="/api/keywords/exclude"',
            html,
        )
        self.assertIn('data-health-url="/health"', html)
        self.assertIn('id="health-badge"', html)
        self.assertIn('id="health-app-name"', html)
        self.assertIn('id="health-server-time"', html)
        self.assertIn('id="health-settings-loaded"', html)
        self.assertIn('id="health-state-file-accessible"', html)
        self.assertIn('id="health-observation-history-exists"', html)
        self.assertIn('id="keywords-status-badge"', html)
        self.assertIn('id="keywords-override-path"', html)
        self.assertIn('id="keywords-override-exists"', html)
        self.assertIn('id="keywords-last-loaded-path"', html)
        self.assertIn('id="keywords-total-count"', html)
        self.assertIn('id="keywords-core-list"', html)
        self.assertIn('id="keywords-core-input"', html)
        self.assertIn('id="keywords-core-add-button"', html)
        self.assertIn('id="keywords-core-save-button"', html)
        self.assertIn('id="keywords-core-message"', html)
        self.assertIn('id="keywords-supporting-list"', html)
        self.assertIn('id="keywords-supporting-input"', html)
        self.assertIn('id="keywords-supporting-add-button"', html)
        self.assertIn('id="keywords-supporting-save-button"', html)
        self.assertIn('id="keywords-supporting-message"', html)
        self.assertIn('id="keywords-exclude-input"', html)
        self.assertIn('id="keywords-exclude-add-button"', html)
        self.assertIn('id="keywords-exclude-save-button"', html)
        self.assertIn('id="keywords-exclude-message"', html)
        self.assertIn('id="keywords-exclude-list"', html)
        self.assertEqual(status_payload["status"], "ready")
        self.assertEqual(status_payload["dashboard_title"], "Project1 Operator Dashboard")
        self.assertFalse(status_payload["read_only"])
        path_values = {item["label"]: item["value"] for item in status_payload["paths"]}
        self.assertEqual(path_values["Config path"], str(config_path))
        self.assertEqual(path_values["Latest exported file"], str(latest_xlsx))
        self.assertEqual(status_payload["collect_control"]["status"], "finished")
        self.assertEqual(status_payload["export_control"]["status"], "finished")
        self.assertEqual(status_payload["observe_control"]["status"], "finished")

    def test_dashboard_launcher_targets_web_server_module(self) -> None:
        content = Path("scripts/run_dashboard.ps1").read_text(encoding="utf-8")
        self.assertIn("app.presentation.web.server", content)
        self.assertIn("--port", content)

    def test_dashboard_frontend_health_fetch_contract_exists(self) -> None:
        content = Path("app/presentation/web/static/dashboard.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("const keywordsUrl = document.body.dataset.keywordsUrl;", content)
        self.assertIn(
            "const keywordsCoreSaveUrl = document.body.dataset.keywordsCoreSaveUrl;",
            content,
        )
        self.assertIn(
            "const keywordsSupportingSaveUrl = document.body.dataset.keywordsSupportingSaveUrl;",
            content,
        )
        self.assertIn(
            "const keywordsExcludeSaveUrl = document.body.dataset.keywordsExcludeSaveUrl;",
            content,
        )
        self.assertIn("fetch(keywordsUrl", content)
        self.assertIn("fetch(keywordsCoreSaveUrl", content)
        self.assertIn("fetch(keywordsSupportingSaveUrl", content)
        self.assertIn("fetch(keywordsExcludeSaveUrl", content)
        self.assertIn("function renderKeywords(payload)", content)
        self.assertIn("function addCoreKeyword()", content)
        self.assertIn("function saveCoreKeywords()", content)
        self.assertIn("function addSupportingKeyword()", content)
        self.assertIn("function saveSupportingKeywords()", content)
        self.assertIn("function addExcludeKeyword()", content)
        self.assertIn("function saveExcludeKeywords()", content)
        self.assertIn("function keywordsStatusClass(status)", content)
        self.assertIn("const healthUrl = document.body.dataset.healthUrl;", content)
        self.assertIn("fetch(healthUrl", content)
        self.assertIn("function renderHealth(payload)", content)
        self.assertIn("function healthStatusClass(status)", content)


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
