import json
from pathlib import Path
from unittest import TestCase

from app.domain import NoticeSource
from app.ops import (
    ConfigurationAppError,
    ErrorType,
    LogEvent,
    LogEventType,
    RunStatus,
    create_run_id,
)


class OpsModelTests(TestCase):
    def test_run_id_contains_timestamp_and_uuid_suffix(self) -> None:
        run_id = create_run_id()

        self.assertRegex(run_id, r"^\d{8}T\d{12}Z_[0-9a-f]{8}$")

    def test_log_event_serializes_required_fields(self) -> None:
        event = LogEvent(
            run_id="20260416T081530123456Z_a1b2c3d4",
            event_type=LogEventType.SOURCE_FINISHED,
            action="collect",
            status=RunStatus.SUCCESS,
            source=NoticeSource.BIZINFO,
            fetched_count=20,
            saved_count=3,
            excluded_count=17,
            output_file_path=Path("output/notices.xlsx"),
        )

        payload = json.loads(event.to_json())

        self.assertEqual(payload["run_id"], "20260416T081530123456Z_a1b2c3d4")
        self.assertEqual(payload["event_type"], "source_finished")
        self.assertEqual(payload["source"], "bizinfo")
        self.assertEqual(payload["fetched_count"], 20)
        self.assertEqual(payload["saved_count"], 3)
        self.assertEqual(payload["excluded_count"], 17)
        self.assertEqual(payload["output_file_path"], str(Path("output/notices.xlsx")))

    def test_error_event_serializes_error_type(self) -> None:
        error = ConfigurationAppError("missing keywords").to_error_info()
        event = LogEvent(
            run_id="run-1",
            event_type=LogEventType.ERROR,
            action="collect",
            status=RunStatus.FAILED,
            error=error,
        )

        payload = event.to_dict()

        self.assertEqual(payload["error_type"], ErrorType.CONFIGURATION.value)
        self.assertEqual(payload["error_message"], "missing keywords")

    def test_log_event_serializes_metadata_payload(self) -> None:
        event = LogEvent(
            run_id="run-1",
            event_type=LogEventType.COLLECT_DIAGNOSTIC,
            action="collect",
            status=RunStatus.RUNNING,
            source=NoticeSource.BIZINFO,
            metadata={
                "source_notice_id": "BIZ-1",
                "eligible": False,
                "skip_reason": "no_keyword_match",
            },
        )

        payload = event.to_dict()

        self.assertEqual(payload["event_type"], "collect_diagnostic")
        self.assertEqual(payload["metadata"]["source_notice_id"], "BIZ-1")
        self.assertEqual(payload["metadata"]["skip_reason"], "no_keyword_match")
