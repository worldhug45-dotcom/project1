"""Export notices use case orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.application.models import (
    ExportSheetInput,
    ExportWorkbookInput,
    RunSummary,
)
from app.application.ports import ExcelExporterPort, NoticeRepositoryPort
from app.domain import Notice, NoticeType
from app.ops import RunStatus


@dataclass(slots=True)
class DefaultExportNoticesUseCase:
    """Export orchestration over repository lookup and Excel exporter port."""

    repository: NoticeRepositoryPort
    exporter: ExcelExporterPort
    support_sheet_name: str = "support_notices"
    bid_sheet_name: str = "bid_notices"

    def execute(self, *, run_id: str) -> RunSummary:
        started_at = datetime.now(UTC)
        notices = self.repository.list_all()
        workbook = build_export_workbook_input(
            notices,
            support_sheet_name=self.support_sheet_name,
            bid_sheet_name=self.bid_sheet_name,
        )
        exported_files = self.exporter.export(workbook, run_id)
        finished_at = datetime.now(UTC)
        return RunSummary(
            run_id=run_id,
            action="export",
            status=RunStatus.SUCCESS,
            exported_files=exported_files,
            started_at=started_at,
            finished_at=finished_at,
        )


def build_export_workbook_input(
    notices: tuple[Notice, ...],
    *,
    support_sheet_name: str = "support_notices",
    bid_sheet_name: str = "bid_notices",
) -> ExportWorkbookInput:
    """Split persisted notices into the first-MVP Excel worksheet inputs."""

    support_notices = tuple(
        notice for notice in notices if notice.notice_type == NoticeType.SUPPORT
    )
    bid_notices = tuple(notice for notice in notices if notice.notice_type == NoticeType.BID)
    return ExportWorkbookInput(
        support_sheet=ExportSheetInput(
            sheet_name=support_sheet_name,
            notices=support_notices,
        ),
        bid_sheet=ExportSheetInput(
            sheet_name=bid_sheet_name,
            notices=bid_notices,
        ),
    )
