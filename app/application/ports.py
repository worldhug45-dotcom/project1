"""Application ports implemented by outer adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.application.models import ExportWorkbookInput
from app.domain import DeduplicationKey, Notice, NoticeSource
from app.ops import LogEvent


class NoticeSourcePort(Protocol):
    """Port for external notice source adapters."""

    source: NoticeSource

    def fetch(self) -> tuple[object, ...]:
        """Fetch raw source DTOs without applying domain rules."""
        ...


class NoticeNormalizerPort(Protocol):
    """Port for converting source DTOs into normalized domain notices."""

    def normalize(self, raw_notice: object) -> Notice:
        """Convert one source DTO into a Notice."""
        ...


class NoticeRepositoryPort(Protocol):
    """Port for notice persistence."""

    def exists(self, key: DeduplicationKey) -> bool:
        """Return whether a notice with the given key already exists."""
        ...

    def save(self, notice: Notice, key: DeduplicationKey) -> None:
        """Persist one normalized notice."""
        ...

    def list_all(self) -> tuple[Notice, ...]:
        """Return persisted notices in a deterministic order for export."""
        ...


class ExcelExporterPort(Protocol):
    """Port for Excel output generation."""

    def export(self, workbook: ExportWorkbookInput, run_id: str) -> tuple[Path, ...]:
        """Create Excel output and return generated file paths."""
        ...


class LogSinkPort(Protocol):
    """Port for emitting operational log events."""

    def emit(self, event: LogEvent) -> None:
        """Emit one structured log event."""
        ...
