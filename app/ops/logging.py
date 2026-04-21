"""Structured runtime log event model."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.domain import NoticeSource
from app.ops.errors import ErrorInfo


class LogEventType(StrEnum):
    RUN_STARTED = "run_started"
    RUN_FINISHED = "run_finished"
    SOURCE_STARTED = "source_started"
    SOURCE_FINISHED = "source_finished"
    COLLECT_DIAGNOSTIC = "collect_diagnostic"
    EXPORT_FINISHED = "export_finished"
    ERROR = "error"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class LogEvent:
    """A single structured operational log event."""

    run_id: str
    event_type: LogEventType
    action: str
    status: RunStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: NoticeSource | None = None
    fetched_count: int | None = None
    saved_count: int | None = None
    excluded_count: int | None = None
    error: ErrorInfo | None = None
    output_file_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "run_id": self.run_id,
            "event_type": self.event_type.value,
            "action": self.action,
            "status": self.status.value,
        }
        if self.source is not None:
            payload["source"] = self.source.value
        if self.fetched_count is not None:
            payload["fetched_count"] = self.fetched_count
        if self.saved_count is not None:
            payload["saved_count"] = self.saved_count
        if self.excluded_count is not None:
            payload["excluded_count"] = self.excluded_count
        if self.error is not None:
            payload["error_type"] = self.error.error_type.value
            payload["error_message"] = self.error.message
            if self.error.source is not None:
                payload["error_source"] = self.error.source
        if self.output_file_path is not None:
            payload["output_file_path"] = str(self.output_file_path)
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)


class ConsoleLogSink:
    """Minimal sink for the CLI skeleton until file logging is implemented."""

    def emit(self, event: LogEvent) -> None:
        print(event.to_json())
