"""Use case contracts for the first MVP."""

from __future__ import annotations

from typing import Protocol

from app.application.models import RunSummary


class CollectNoticesUseCase(Protocol):
    """Collect and persist eligible notices from enabled sources."""

    def execute(self, *, run_id: str) -> RunSummary:
        """Run collection orchestration and return a shared summary."""
        ...


class ExportNoticesUseCase(Protocol):
    """Export notices loaded through NoticeRepositoryPort.list_all to Excel outputs."""

    def execute(self, *, run_id: str) -> RunSummary:
        """Run export orchestration and return a shared summary."""
        ...
