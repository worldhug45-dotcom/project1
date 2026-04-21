"""Persistence adapters for notice storage."""

from app.persistence.memory import InMemoryNoticeRepository
from app.persistence.sqlite import SQLiteNoticeRepository

__all__ = ["InMemoryNoticeRepository", "SQLiteNoticeRepository"]
