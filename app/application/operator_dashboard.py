"""Operator dashboard orchestration helpers for web control surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from threading import Lock, Thread
from typing import Callable

from app.ops.operator_status import OperatorStatusSnapshot, now_isoformat


@dataclass(frozen=True, slots=True)
class CollectExecutionResult:
    """Result returned by the reused manual collect execution path."""

    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True, slots=True)
class ExportExecutionResult:
    """Result returned by the reused manual export execution path."""

    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True, slots=True)
class ObserveExecutionResult:
    """Result returned by the reused manual observe execution path."""

    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True, slots=True)
class CollectControlState:
    """Minimal collect control state exposed to the dashboard."""

    status: str
    fetched_count: int
    saved_count: int
    skipped_count: int
    error_count: int
    db_path: str
    recorded_at: str
    source_mode: str = "not available"
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExportControlState:
    """Minimal export control state exposed to the dashboard."""

    status: str
    exported_file_count: int
    exported_file_path: str
    export_output_dir: str
    recorded_at: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ObserveControlState:
    """Minimal observe control state exposed to the dashboard."""

    status: str
    run_id: str
    observed_on: str
    fetched_count: int
    saved_count: int
    skipped_count: int
    error_count: int
    observation_history_path: str
    observation_report_path: str
    latest_raw_jsonl_path: str
    recorded_at: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class OperatorCollectService:
    """Minimal in-process controller for web-triggered collect execution."""

    def __init__(
        self,
        *,
        status_loader: Callable[[], OperatorStatusSnapshot],
        runner: Callable[[], CollectExecutionResult],
    ) -> None:
        self._status_loader = status_loader
        self._runner = runner
        self._lock = Lock()
        self._state = self._initial_state()

    def get_state(self) -> CollectControlState:
        snapshot = self._safe_snapshot()
        with self._lock:
            if self._state.status == "running":
                return self._state
            if snapshot is not None:
                snapshot_state = self._state_from_snapshot(snapshot)
                if (
                    snapshot_state.status == "failed"
                    and self._state.error_message
                    and snapshot_state.error_message is None
                ):
                    snapshot_state = replace(
                        snapshot_state,
                        error_message=self._state.error_message,
                    )
                if self._should_replace_with_snapshot(snapshot_state):
                    self._state = snapshot_state
            return self._state

    def start_collect(self) -> tuple[bool, CollectControlState]:
        snapshot = self._safe_snapshot()
        with self._lock:
            if self._state.status == "running":
                return False, self._state

            baseline_state = self._state_from_snapshot(snapshot)
            self._state = replace(
                baseline_state,
                status="running",
                recorded_at=now_isoformat(),
                error_message=None,
            )
            worker = Thread(target=self._run_collect, daemon=True)
            worker.start()
            return True, self._state

    def _run_collect(self) -> None:
        try:
            result = self._runner()
        except Exception as exc:
            result = CollectExecutionResult(returncode=1, stderr=str(exc))
        snapshot = self._safe_snapshot()
        with self._lock:
            if snapshot is not None:
                next_state = self._state_from_snapshot(snapshot)
            else:
                next_state = replace(
                    self._state,
                    status="finished" if result.succeeded else "failed",
                    recorded_at=now_isoformat(),
                )

            if result.succeeded:
                if next_state.status == "idle":
                    next_state = replace(next_state, status="finished")
                self._state = replace(next_state, error_message=None)
                return

            error_message = _build_error_message(result)
            if next_state.status == "idle":
                next_state = replace(
                    next_state,
                    status="failed",
                    error_count=max(next_state.error_count, 1),
                )
            else:
                next_state = replace(next_state, status="failed")
            self._state = replace(next_state, error_message=error_message)

    def _initial_state(self) -> CollectControlState:
        snapshot = self._safe_snapshot()
        return self._state_from_snapshot(snapshot)

    def _safe_snapshot(self) -> OperatorStatusSnapshot | None:
        try:
            return self._status_loader()
        except Exception:
            return None

    def _state_from_snapshot(
        self,
        snapshot: OperatorStatusSnapshot | None,
    ) -> CollectControlState:
        if snapshot is None:
            return CollectControlState(
                status="idle",
                fetched_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=0,
                db_path="not available",
                recorded_at="not available",
            )

        payload = snapshot.recent_collect or {}
        db_path = snapshot.current_paths.get("sqlite_db_path", "not available")
        source_mode = str(payload.get("source_mode", "not available"))
        recorded_at = str(payload.get("recorded_at", snapshot.updated_at or "not available"))
        if not payload:
            return CollectControlState(
                status="idle",
                fetched_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=0,
                db_path=db_path,
                recorded_at=recorded_at,
                source_mode=source_mode,
            )

        raw_status = str(payload.get("status", "unknown"))
        mapped_status = "finished"
        if raw_status in {"failed", "config_error", "summary_missing"}:
            mapped_status = "failed"
        elif raw_status == "running":
            mapped_status = "running"

        return CollectControlState(
            status=mapped_status,
            fetched_count=int(payload.get("fetched_count", 0)),
            saved_count=int(payload.get("saved_count", 0)),
            skipped_count=int(payload.get("skipped_count", 0)),
            error_count=int(payload.get("error_count", 0)),
            db_path=str(payload.get("db_path", db_path)),
            recorded_at=recorded_at,
            source_mode=source_mode,
        )

    def _should_replace_with_snapshot(self, snapshot_state: CollectControlState) -> bool:
        if self._state.status == "idle":
            return True
        if snapshot_state.recorded_at == "not available":
            return False
        if self._state.recorded_at == "not available":
            return True
        return snapshot_state.recorded_at >= self._state.recorded_at


class OperatorExportService:
    """Minimal in-process controller for web-triggered export execution."""

    def __init__(
        self,
        *,
        status_loader: Callable[[], OperatorStatusSnapshot],
        runner: Callable[[], ExportExecutionResult],
    ) -> None:
        self._status_loader = status_loader
        self._runner = runner
        self._lock = Lock()
        self._state = self._initial_state()

    def get_state(self) -> ExportControlState:
        snapshot = self._safe_snapshot()
        with self._lock:
            if self._state.status == "running":
                return self._state
            if snapshot is not None:
                snapshot_state = self._state_from_snapshot(snapshot)
                if (
                    snapshot_state.status == "failed"
                    and self._state.error_message
                    and snapshot_state.error_message is None
                ):
                    snapshot_state = replace(
                        snapshot_state,
                        error_message=self._state.error_message,
                    )
                if self._should_replace_with_snapshot(snapshot_state):
                    self._state = snapshot_state
            return self._state

    def start_export(self) -> tuple[bool, ExportControlState]:
        snapshot = self._safe_snapshot()
        with self._lock:
            if self._state.status == "running":
                return False, self._state

            baseline_state = self._state_from_snapshot(snapshot)
            self._state = replace(
                baseline_state,
                status="running",
                recorded_at=now_isoformat(),
                error_message=None,
            )
            worker = Thread(target=self._run_export, daemon=True)
            worker.start()
            return True, self._state

    def _run_export(self) -> None:
        try:
            result = self._runner()
        except Exception as exc:
            result = ExportExecutionResult(returncode=1, stderr=str(exc))
        snapshot = self._safe_snapshot()
        with self._lock:
            if snapshot is not None:
                next_state = self._state_from_snapshot(snapshot)
            else:
                next_state = replace(
                    self._state,
                    status="finished" if result.succeeded else "failed",
                    recorded_at=now_isoformat(),
                )

            if result.succeeded:
                if next_state.status == "idle":
                    next_state = replace(next_state, status="finished")
                self._state = replace(next_state, error_message=None)
                return

            error_message = _build_error_message(result)
            if next_state.status == "idle":
                next_state = replace(next_state, status="failed")
            else:
                next_state = replace(next_state, status="failed")
            self._state = replace(next_state, error_message=error_message)

    def _initial_state(self) -> ExportControlState:
        snapshot = self._safe_snapshot()
        return self._state_from_snapshot(snapshot)

    def _safe_snapshot(self) -> OperatorStatusSnapshot | None:
        try:
            return self._status_loader()
        except Exception:
            return None

    def _state_from_snapshot(
        self,
        snapshot: OperatorStatusSnapshot | None,
    ) -> ExportControlState:
        if snapshot is None:
            return ExportControlState(
                status="idle",
                exported_file_count=0,
                exported_file_path="not available",
                export_output_dir="not available",
                recorded_at="not available",
            )

        payload = snapshot.recent_export or {}
        export_output_dir = snapshot.current_paths.get("export_output_dir", "not available")
        latest_exported_file_path = snapshot.current_paths.get(
            "latest_exported_file_path",
            "not available",
        )
        recorded_at = str(payload.get("recorded_at", snapshot.updated_at or "not available"))
        if not payload:
            return ExportControlState(
                status="idle",
                exported_file_count=0,
                exported_file_path=latest_exported_file_path,
                export_output_dir=export_output_dir,
                recorded_at=recorded_at,
            )

        raw_status = str(payload.get("status", "unknown"))
        mapped_status = "finished"
        if raw_status in {"failed", "config_error", "summary_missing"}:
            mapped_status = "failed"
        elif raw_status == "running":
            mapped_status = "running"

        return ExportControlState(
            status=mapped_status,
            exported_file_count=int(payload.get("exported_file_count", 0)),
            exported_file_path=_exported_file_path_from_payload(
                payload,
                latest_exported_file_path,
            ),
            export_output_dir=str(payload.get("export_output_dir", export_output_dir)),
            recorded_at=recorded_at,
        )

    def _should_replace_with_snapshot(self, snapshot_state: ExportControlState) -> bool:
        if self._state.status == "idle":
            return True
        if snapshot_state.recorded_at == "not available":
            return False
        if self._state.recorded_at == "not available":
            return True
        return snapshot_state.recorded_at >= self._state.recorded_at


class OperatorObserveService:
    """Minimal in-process controller for web-triggered observe execution."""

    def __init__(
        self,
        *,
        status_loader: Callable[[], OperatorStatusSnapshot],
        runner: Callable[[], ObserveExecutionResult],
    ) -> None:
        self._status_loader = status_loader
        self._runner = runner
        self._lock = Lock()
        self._state = self._initial_state()

    def get_state(self) -> ObserveControlState:
        snapshot = self._safe_snapshot()
        with self._lock:
            if self._state.status == "running":
                return self._state
            if snapshot is not None:
                snapshot_state = self._state_from_snapshot(snapshot)
                if (
                    snapshot_state.status == "failed"
                    and self._state.error_message
                    and snapshot_state.error_message is None
                ):
                    snapshot_state = replace(
                        snapshot_state,
                        error_message=self._state.error_message,
                    )
                if self._should_replace_with_snapshot(snapshot_state):
                    self._state = snapshot_state
            return self._state

    def start_observe(self) -> tuple[bool, ObserveControlState]:
        snapshot = self._safe_snapshot()
        with self._lock:
            if self._state.status == "running":
                return False, self._state

            baseline_state = self._state_from_snapshot(snapshot)
            self._state = replace(
                baseline_state,
                status="running",
                recorded_at=now_isoformat(),
                error_message=None,
            )
            worker = Thread(target=self._run_observe, daemon=True)
            worker.start()
            return True, self._state

    def _run_observe(self) -> None:
        try:
            result = self._runner()
        except Exception as exc:
            result = ObserveExecutionResult(returncode=1, stderr=str(exc))
        snapshot = self._safe_snapshot()
        with self._lock:
            if snapshot is not None:
                next_state = self._state_from_snapshot(snapshot)
            else:
                next_state = replace(
                    self._state,
                    status="finished" if result.succeeded else "failed",
                    recorded_at=now_isoformat(),
                )

            if result.succeeded:
                if next_state.status == "idle":
                    next_state = replace(next_state, status="finished")
                self._state = replace(next_state, error_message=None)
                return

            error_message = _build_error_message(result)
            if next_state.status == "idle":
                next_state = replace(
                    next_state,
                    status="failed",
                    error_count=max(next_state.error_count, 1),
                )
            else:
                next_state = replace(
                    next_state,
                    status="failed",
                    error_count=max(next_state.error_count, 1),
                )
            self._state = replace(next_state, error_message=error_message)

    def _initial_state(self) -> ObserveControlState:
        snapshot = self._safe_snapshot()
        return self._state_from_snapshot(snapshot)

    def _safe_snapshot(self) -> OperatorStatusSnapshot | None:
        try:
            return self._status_loader()
        except Exception:
            return None

    def _state_from_snapshot(
        self,
        snapshot: OperatorStatusSnapshot | None,
    ) -> ObserveControlState:
        if snapshot is None:
            return ObserveControlState(
                status="idle",
                run_id="not available",
                observed_on="not available",
                fetched_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=0,
                observation_history_path="not available",
                observation_report_path="not available",
                latest_raw_jsonl_path="not available",
                recorded_at="not available",
            )

        payload = snapshot.recent_observe or {}
        observation_history_path = snapshot.current_paths.get(
            "observation_history_path",
            "not available",
        )
        observation_report_path = snapshot.current_paths.get(
            "observation_report_path",
            "not available",
        )
        recorded_at = str(payload.get("recorded_at", snapshot.updated_at or "not available"))
        if not payload:
            return ObserveControlState(
                status="idle",
                run_id="not available",
                observed_on="not available",
                fetched_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=0,
                observation_history_path=observation_history_path,
                observation_report_path=observation_report_path,
                latest_raw_jsonl_path="not available",
                recorded_at=recorded_at,
            )

        raw_status = str(payload.get("status", "unknown"))
        mapped_status = "finished"
        if raw_status in {"failed", "config_error", "summary_missing"}:
            mapped_status = "failed"
        elif raw_status == "running":
            mapped_status = "running"

        return ObserveControlState(
            status=mapped_status,
            run_id=str(payload.get("run_id", "not available")),
            observed_on=str(payload.get("observed_on", "not available")),
            fetched_count=int(payload.get("fetched_count", 0)),
            saved_count=int(payload.get("saved_count", 0)),
            skipped_count=int(payload.get("skipped_count", 0)),
            error_count=int(payload.get("error_count", 0)),
            observation_history_path=str(
                payload.get("observation_history_path", observation_history_path)
            ),
            observation_report_path=str(
                payload.get("observation_report_path", observation_report_path)
            ),
            latest_raw_jsonl_path=str(payload.get("latest_raw_jsonl_path", "not available")),
            recorded_at=recorded_at,
        )

    def _should_replace_with_snapshot(self, snapshot_state: ObserveControlState) -> bool:
        if self._state.status == "idle":
            return True
        if snapshot_state.recorded_at == "not available":
            return False
        if self._state.recorded_at == "not available":
            return True
        return snapshot_state.recorded_at >= self._state.recorded_at


def _exported_file_path_from_payload(
    payload: dict[str, object],
    fallback_path: str,
) -> str:
    explicit_path = payload.get("exported_file_path")
    if isinstance(explicit_path, str) and explicit_path:
        return explicit_path

    exported_files = payload.get("exported_files")
    if isinstance(exported_files, list) and exported_files:
        first = exported_files[0]
        if isinstance(first, str) and first:
            return first

    return fallback_path


def _build_error_message(
    result: CollectExecutionResult | ExportExecutionResult | ObserveExecutionResult,
) -> str:
    stderr = result.stderr.strip()
    if stderr:
        return stderr.splitlines()[-1]
    stdout = result.stdout.strip()
    if stdout:
        return stdout.splitlines()[-1]
    return "Action execution failed."
