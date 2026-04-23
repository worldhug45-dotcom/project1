import json
import threading
import time
from dataclasses import replace
from urllib.request import Request, urlopen
from unittest import TestCase

from app.application import (
    CollectExecutionResult,
    ExportExecutionResult,
    ObserveExecutionResult,
    OperatorCollectService,
    OperatorExportService,
    OperatorObserveService,
)
from app.ops import OperatorStatusSnapshot
from app.presentation.web.server import (
    DashboardServerContext,
    DashboardServerSettings,
    create_server,
)


class WebExportActionTests(TestCase):
    def test_export_action_runs_once_and_updates_finished_summary(self) -> None:
        snapshot_holder = _SnapshotHolder()

        def runner() -> ExportExecutionResult:
            time.sleep(0.05)
            snapshot_holder.snapshot = snapshot_holder.snapshot_with_export(
                {
                    "status": "success",
                    "recorded_at": "2026-04-21T11:00:00+00:00",
                    "exported_file_count": 1,
                    "exported_file_path": "output/notices_20260421_export-run.xlsx",
                    "export_output_dir": "output",
                },
                latest_exported_file_path="output/notices_20260421_export-run.xlsx",
            )
            return ExportExecutionResult(returncode=0, stdout="ok")

        payload = _run_server_case(snapshot_holder, runner, expected_status="finished")

        self.assertTrue(payload["action_payload"]["started"])
        status_payload = payload["status_payload"]
        self.assertEqual(status_payload["export_control"]["status"], "finished")
        items = {item["label"]: item["value"] for item in status_payload["export_control"]["items"]}
        self.assertEqual(items["Exported files"], "1")
        self.assertEqual(
            items["Exported file path"],
            "output/notices_20260421_export-run.xlsx",
        )
        self.assertEqual(items["Export output dir"], "output")
        path_values = {item["label"]: item["value"] for item in status_payload["paths"]}
        self.assertEqual(
            path_values["Latest exported file"],
            "output/notices_20260421_export-run.xlsx",
        )

    def test_export_action_rejects_duplicate_request_while_running(self) -> None:
        snapshot_holder = _SnapshotHolder()
        release_event = threading.Event()
        call_count = {"value": 0}

        def runner() -> ExportExecutionResult:
            call_count["value"] += 1
            release_event.wait(timeout=2)
            snapshot_holder.snapshot = snapshot_holder.snapshot_with_export(
                {
                    "status": "success",
                    "recorded_at": "2026-04-21T11:05:00+00:00",
                    "exported_file_count": 1,
                    "exported_file_path": "output/notices_20260421_export-run.xlsx",
                    "export_output_dir": "output",
                },
                latest_exported_file_path="output/notices_20260421_export-run.xlsx",
            )
            return ExportExecutionResult(returncode=0)

        settings = DashboardServerSettings(host="127.0.0.1", port=0)
        export_service = OperatorExportService(
            status_loader=snapshot_holder.load,
            runner=runner,
        )
        context = DashboardServerContext(
            settings=settings,
            status_loader=snapshot_holder.load,
            collect_service=OperatorCollectService(
                status_loader=snapshot_holder.load,
                runner=lambda: CollectExecutionResult(returncode=0),
            ),
            export_service=export_service,
            observe_service=OperatorObserveService(
                status_loader=snapshot_holder.load,
                runner=lambda: ObserveExecutionResult(returncode=0),
            ),
        )
        server = create_server(settings, context=context)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            first = _post_json(f"{base_url}/actions/export")
            second = _post_json(f"{base_url}/actions/export")
            status_while_running = _get_json(f"{base_url}/api/status")
            release_event.set()
            _wait_until(
                lambda: (
                    _get_json(f"{base_url}/api/status")["export_control"]["status"] == "finished"
                )
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertTrue(first["started"])
        self.assertFalse(second["started"])
        self.assertEqual(second["export_control"]["status"], "running")
        self.assertEqual(status_while_running["export_control"]["status"], "running")
        self.assertEqual(call_count["value"], 1)

    def test_export_action_exposes_failed_state(self) -> None:
        snapshot_holder = _SnapshotHolder()

        def runner() -> ExportExecutionResult:
            time.sleep(0.05)
            snapshot_holder.snapshot = snapshot_holder.snapshot_with_export(
                {
                    "status": "failed",
                    "recorded_at": "2026-04-21T11:10:00+00:00",
                    "exported_file_count": 0,
                    "exported_file_path": "not available",
                    "export_output_dir": "output",
                },
                latest_exported_file_path="not available",
            )
            return ExportExecutionResult(returncode=1, stderr="export failed")

        payload = _run_server_case(snapshot_holder, runner, expected_status="failed")

        self.assertTrue(payload["action_payload"]["started"])
        status_payload = payload["status_payload"]
        self.assertEqual(status_payload["export_control"]["status"], "failed")
        self.assertEqual(status_payload["export_control"]["error_message"], "export failed")


class _SnapshotHolder:
    def __init__(self) -> None:
        self.snapshot = OperatorStatusSnapshot(
            current_paths={
                "config_path": "config/settings.local.toml",
                "keyword_override_path": "config/keywords.override.toml",
                "sqlite_db_path": "data/notices.sqlite3",
                "export_output_dir": "output",
                "latest_exported_file_path": "not available",
                "observation_history_path": "data/history.json",
                "observation_report_path": "doc/report.md",
                "observation_raw_jsonl_dir": "data/raw",
                "state_path": "data/operations/manual_run_state.json",
            },
            recent_collect=None,
            recent_export=None,
            recent_observe=None,
            launchers={"export_launcher": "scripts/run_export.ps1"},
            updated_at="2026-04-21T10:55:00+00:00",
        )

    def load(self) -> OperatorStatusSnapshot:
        return self.snapshot

    def snapshot_with_export(
        self,
        payload: dict[str, object],
        *,
        latest_exported_file_path: str,
    ) -> OperatorStatusSnapshot:
        current_paths = dict(self.snapshot.current_paths)
        current_paths["latest_exported_file_path"] = latest_exported_file_path
        return replace(
            self.snapshot,
            current_paths=current_paths,
            recent_export=payload,
            updated_at=str(payload["recorded_at"]),
        )


def _run_server_case(
    snapshot_holder: _SnapshotHolder,
    runner,
    *,
    expected_status: str,
) -> dict[str, object]:
    settings = DashboardServerSettings(host="127.0.0.1", port=0)
    export_service = OperatorExportService(
        status_loader=snapshot_holder.load,
        runner=runner,
    )
    context = DashboardServerContext(
        settings=settings,
        status_loader=snapshot_holder.load,
        collect_service=OperatorCollectService(
            status_loader=snapshot_holder.load,
            runner=lambda: CollectExecutionResult(returncode=0),
        ),
        export_service=export_service,
        observe_service=OperatorObserveService(
            status_loader=snapshot_holder.load,
            runner=lambda: ObserveExecutionResult(returncode=0),
        ),
    )
    server = create_server(settings, context=context)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        action_payload = _post_json(f"{base_url}/actions/export")
        _wait_until(
            lambda: (
                _get_json(f"{base_url}/api/status")["export_control"]["status"] == expected_status
            )
        )
        status_payload = _get_json(f"{base_url}/api/status")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return {"action_payload": action_payload, "status_payload": status_payload}


def _wait_until(predicate, *, timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("Condition was not met before timeout.")


def _post_json(url: str) -> dict[str, object]:
    request = Request(url, method="POST", headers={"Accept": "application/json"})
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str) -> dict[str, object]:
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))
