"""In-memory repository for fixture-based collect tests."""

from __future__ import annotations

from app.domain import DeduplicationKey, Notice


class InMemoryNoticeRepository:
    """NoticeRepositoryPort implementation for tests and early orchestration."""

    def __init__(self) -> None:
        self._items: dict[DeduplicationKey, Notice] = {}

    def exists(self, key: DeduplicationKey) -> bool:
        return key in self._items

    def save(self, notice: Notice, key: DeduplicationKey) -> None:
        self._items[key] = notice

    def list_all(self) -> tuple[Notice, ...]:
        """Return persisted notices in insertion order for export preparation."""

        return tuple(self._items.values())

    def all(self) -> tuple[Notice, ...]:
        return self.list_all()

    def count(self) -> int:
        return len(self._items)
