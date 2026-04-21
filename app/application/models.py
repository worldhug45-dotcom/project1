"""Application-level result models shared by collect, export, and all actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.domain import Notice, NoticeSource
from app.ops import ErrorInfo, RunStatus


@dataclass(frozen=True, slots=True)
class SourceRunSummary:
    """Per-source execution summary for one run."""

    source: NoticeSource
    collected_count: int = 0
    saved_count: int = 0
    skipped_count: int = 0
    error_count: int = 0

    def __post_init__(self) -> None:
        _ensure_non_negative("collected_count", self.collected_count)
        _ensure_non_negative("saved_count", self.saved_count)
        _ensure_non_negative("skipped_count", self.skipped_count)
        _ensure_non_negative("error_count", self.error_count)


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Shared execution result for collect, export, and all actions."""

    run_id: str
    action: str
    status: RunStatus
    source_results: tuple[SourceRunSummary, ...] = ()
    collected_count: int = 0
    saved_count: int = 0
    skipped_count: int = 0
    exported_files: tuple[Path, ...] = ()
    error_count: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    errors: tuple[ErrorInfo, ...] = field(default_factory=tuple)

    @classmethod
    def from_sources(
        cls,
        *,
        run_id: str,
        action: str,
        status: RunStatus,
        source_results: tuple[SourceRunSummary, ...],
        exported_files: tuple[Path, ...] = (),
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        errors: tuple[ErrorInfo, ...] = (),
    ) -> "RunSummary":
        return cls(
            run_id=run_id,
            action=action,
            status=status,
            source_results=source_results,
            collected_count=sum(item.collected_count for item in source_results),
            saved_count=sum(item.saved_count for item in source_results),
            skipped_count=sum(item.skipped_count for item in source_results),
            exported_files=exported_files,
            error_count=sum(item.error_count for item in source_results),
            started_at=started_at,
            finished_at=finished_at,
            errors=errors,
        )

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("RunSummary.run_id is required.")
        if self.action not in {"collect", "export", "all"}:
            raise ValueError("RunSummary.action must be collect, export, or all.")
        _ensure_non_negative("collected_count", self.collected_count)
        _ensure_non_negative("saved_count", self.saved_count)
        _ensure_non_negative("skipped_count", self.skipped_count)
        _ensure_non_negative("error_count", self.error_count)
        if (
            self.started_at is not None
            and self.finished_at is not None
            and self.finished_at < self.started_at
        ):
            raise ValueError("RunSummary.finished_at cannot be before started_at.")


@dataclass(frozen=True, slots=True)
class ExportSheetInput:
    """Notices grouped for one Excel worksheet."""

    sheet_name: str
    notices: tuple[Notice, ...]

    def __post_init__(self) -> None:
        if not self.sheet_name.strip():
            raise ValueError("ExportSheetInput.sheet_name is required.")


@dataclass(frozen=True, slots=True)
class ExportWorkbookInput:
    """Workbook input assembled by the export use case."""

    support_sheet: ExportSheetInput
    bid_sheet: ExportSheetInput

    @property
    def sheets(self) -> tuple[ExportSheetInput, ExportSheetInput]:
        return (self.support_sheet, self.bid_sheet)


def _ensure_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be 0 or greater.")
