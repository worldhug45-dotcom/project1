"""Fake Excel exporter for export use case tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.application.models import ExportWorkbookInput


@dataclass(slots=True)
class FakeExcelExporter:
    """ExcelExporterPort implementation that records workbook input only."""

    output_paths: tuple[Path, ...] = (Path("output/notices.xlsx"),)
    calls: list[tuple[str, ExportWorkbookInput]] = field(default_factory=list)

    def export(self, workbook: ExportWorkbookInput, run_id: str) -> tuple[Path, ...]:
        self.calls.append((run_id, workbook))
        return self.output_paths

    @property
    def last_workbook(self) -> ExportWorkbookInput | None:
        if not self.calls:
            return None
        return self.calls[-1][1]
