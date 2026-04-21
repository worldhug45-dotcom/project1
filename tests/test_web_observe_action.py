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


class WebObserveActionTests(TestCase):
    def test_observe_action_runs_once_and_updates_finished_summary(self) -> None:
        snapshot_holder = _SnapshotHolder()

        def runner() -> ObserveExecutionResult:
            time.sleep(0.05)
            snapshot_holder.snapshot = snapshot_holder.snapshot_with_observe(
                {
                    "status": "success",
                    "recorded_at": "2026-04-21T12:00:00+00:00",
                    "run_id": "observe-run-1",
                    "observed_on": "2026-04-21",
                    "fetched_count": 20,
                    "saved_count": 4,
                    "skipped_count": 16,
                    "error_count": 0,
                    "observation_history_path": "data/observations/history.json",
                    "observation_report_path": "doc/observations/report.md",
                    "latest_raw_jsonl_path": "data/observations/raw/2026-04-21_observe-run-1.jsonl",
                }
            )
            return ObserveExecutionResult(returncode=0, stdout="ok")

        payload = _run_server_case(snapshot_holder, runner, expected_status="finished")

        self.assertTrue(payload["action_payload"]["started"])
        status_payload = payload["status_payload"]
        self.assertEqual(status_payload["observe_control"]["status"], "finished")
        items = {
            item["label"]: item["value"]
            for item in status_payload["observe_control"]["items"]
        }
        self.assertEqual(items["Run ID"], "observe-run-1")
        self.assertEqual(items["Observed on"], "2026-04-21")
        self.assertEqual(items["Fetched"], "20")
        self.assertEqual(items["Saved"], "4")
        self.assertEqual(items["Skipped"], "16")
        self.assertEqual(items["Errors"], "0")
        self.assertEqual(
            items["Observation history"],
            "data/observations/history.json",
        )
        self.assertEqual(
            items["Observation report"],
            "doc/observations/report.md",
        )
        self.assertEqual(
            items["Latest raw JSONL"],
            "data/observations/raw/2026-04-21_observe-run-1.jsonl",
        )

    def test_observe_action_rejects_duplicate_request_while_running(self) -> None:
        snapshot_holder = _SnapshotHolder()
        release_event = threading.Event()
        call_count = {"value": 0}

        def runner() -> ObserveExecutionResult:
            call_count["value"] += 1
            release_event.wait(timeout=2)
            snapshot_holder.snapshot = snapshot_holder.snapshot_with_observe(
                {
                    "status": "success",
                    "recorded_at": "2026-04-21T12:05:00+00:00",
                    "run_id": "observe-run-2",
                    "observed_on": "2026-04-21",
                    "fetched_count": 2,
                    "saved_count": 1,
                    "skipped_count": 1,
                    "error_count": 0,
                    "observation_history_path": "data/observations/history.json",
                    "observation_report_path": "doc/observations/report.md",
                    "latest_raw_jsonl_path": "data/observations/raw/2026-04-21_observe-run-2.jsonl",
                }
            )
            return ObserveExecutionResult(returncode=0)

        settings = DashboardServerSettings(host="127.0.0.1", port=0)
        observe_service = OperatorObserveService(
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
            export_service=OperatorExportService(
                status_loader=snapshot_holder.load,
                runner=lambda: ExportExecutionResult(returncode=0),
            ),
            observe_service=observe_service,
        )
        server = create_server(settings, context=context)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            first = _post_json(f"{base_url}/actions/observe")
            second = _post_json(f"{base_url}/actions/observe")
            status_while_running = _get_json(f"{base_url}/api/status")
            release_event.set()
            _wait_until(
                lambda: _get_json(f"{base_url}/api/status")["observe_control"]["status"]
                == "finished"
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertTrue(first["started"])
        self.assertFalse(second["started"])
        self.assertEqual(second["observe_control"]["status"], "running")
        self.assertEqual(status_while_running["observe_control"]["status"], "running")
        self.assertEqual(call_count["value"], 1)

    def test_observe_action_exposes_failed_state(self) -> None:
        snapshot_holder = _SnapshotHolder()

        def runner() -> ObserveExecutionResult:
            time.sleep(0.05)
            snapshot_holder.snapshot = snapshot_holder.snapshot_with_observe(
                {
                    "status": "failed",
                    "recorded_at": "2026-04-21T12:10:00+00:00",
                    "run_id": "observe-run-3",
                    "observed_on": "2026-04-21",
                    "fetched_count": 0,
                    "saved_count": 0,
                    "skipped_count": 0,
                    "error_count": 1,
                    "observation_history_path": "data/observations/history.json",
                    "observation_report_path": "doc/observations/report.md",
                    "latest_raw_jsonl_path": "not available",
                }
            )
            return ObserveExecutionResult(returncode=1, stderr="observe failed")

        payload = _run_server_case(snapshot_holder, runner, expected_status="failed")

        self.assertTrue(payload["action_payload"]["started"])
        status_payload = payload["status_payload"]
        self.assertEqual(status_payload["observe_control"]["status"], "failed")
        self.assertEqual(status_payload["observe_control"]["error_message"], "observe failed")
        items = {
            item["label"]: item["value"]
            for item in status_payload["observe_control"]["items"]
        }
        self.assertEqual(items["Errors"], "1")


class _SnapshotHolder:
    def __init__(self) -> None:
        self.snapshot = OperatorStatusSnapshot(
            current_paths={
                "config_path": "config/settings.local.toml",
                "keyword_override_path": "config/keywords.override.toml",
                "sqlite_db_path": "data/notices.sqlite3",
                "export_output_dir": "output",
                "latest_exported_file_path": "not available",
                "observation_history_path": "data/observations/history.json",
                "observation_report_path": "doc/observations/report.md",
                "observation_raw_jsonl_dir": "data/observations/raw",
                "state_path": "data/operations/manual_run_state.json",
            },
            recent_collect=None,
            recent_export=None,
            recent_observe=None,
            launchers={"observe_launcher": "scripts/run_observe.ps1"},
            updated_at="2026-04-21T11:55:00+00:00",
        )

    def load(self) -> OperatorStatusSnapshot:
        return self.snapshot

    def snapshot_with_observe(self, payload: dict[str, object]) -> OperatorStatusSnapshot:
        current_paths = dict(self.snapshot.current_paths)
        current_paths["observation_history_path"] = str(
            payload.get("observation_history_path", current_paths["observation_history_path"])
        )
        current_paths["observation_report_path"] = str(
            payload.get("observation_report_path", current_paths["observation_report_path"])
        )
        return replace(
            self.snapshot,
            current_paths=current_paths,
            recent_observe=payload,
            updated_at=str(payload["recorded_at"]),
        )


def _run_server_case(
    snapshot_holder: _SnapshotHolder,
    runner,
    *,
    expected_status: str,
) -> dict[str, object]:
    settings = DashboardServerSettings(host="127.0.0.1", port=0)
    observe_service = OperatorObserveService(
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
        export_service=OperatorExportService(
            status_loader=snapshot_holder.load,
            runner=lambda: ExportExecutionResult(returncode=0),
        ),
        observe_service=observe_service,
    )
    server = create_server(settings, context=context)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        action_payload = _post_json(f"{base_url}/actions/observe")
        _wait_until(
            lambda: _get_json(f"{base_url}/api/status")["observe_control"]["status"]
            == expected_status
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
