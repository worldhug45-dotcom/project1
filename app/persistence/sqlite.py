"""SQLite repository for normalized notices."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

from app.domain import (
    BusinessDomain,
    DeduplicationKey,
    KeywordGroup,
    MatchedKeyword,
    Notice,
    NoticeSource,
    NoticeStatus,
    NoticeType,
)
from app.ops import StorageWriteError


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    dedup_key_type TEXT NOT NULL,
    dedup_key_value TEXT NOT NULL,
    source_notice_id TEXT,
    notice_type TEXT NOT NULL,
    business_domains_json TEXT NOT NULL,
    primary_domain TEXT NOT NULL,
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    posted_at TEXT,
    end_at TEXT,
    status TEXT NOT NULL,
    url TEXT NOT NULL,
    match_keywords_json TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    raw_source_name TEXT,
    summary TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (source, dedup_key_type, dedup_key_value)
);
"""


@dataclass(slots=True)
class SQLiteNoticeRepository:
    """NoticeRepositoryPort implementation backed by SQLite."""

    database_path: Path
    _connection: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._ensure_parent_directory()
        self._connection = sqlite3.connect(str(self.database_path))
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    def __enter__(self) -> "SQLiteNoticeRepository":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def initialize(self) -> None:
        """Create required tables when they do not exist."""

        self._connection.execute(SCHEMA_SQL)
        self._connection.commit()

    def exists(self, key: DeduplicationKey) -> bool:
        row = self._connection.execute(
            """
            SELECT 1
            FROM notices
            WHERE source = ?
              AND dedup_key_type = ?
              AND dedup_key_value = ?
            LIMIT 1
            """,
            (key.source.value, key.key_type, key.key_value),
        ).fetchone()
        return row is not None

    def save(self, notice: Notice, key: DeduplicationKey) -> None:
        try:
            self._connection.execute(
                """
                INSERT OR IGNORE INTO notices (
                    source,
                    dedup_key_type,
                    dedup_key_value,
                    source_notice_id,
                    notice_type,
                    business_domains_json,
                    primary_domain,
                    title,
                    organization,
                    posted_at,
                    end_at,
                    status,
                    url,
                    match_keywords_json,
                    collected_at,
                    raw_source_name,
                    summary,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notice.source.value,
                    key.key_type,
                    key.key_value,
                    notice.source_notice_id,
                    notice.notice_type.value,
                    _dump_business_domains(notice.business_domains),
                    notice.primary_domain.value,
                    notice.title,
                    notice.organization,
                    _date_to_text(notice.posted_at),
                    _date_to_text(notice.end_at),
                    notice.status.value,
                    notice.url,
                    _dump_matched_keywords(notice.match_keywords),
                    notice.collected_at.isoformat(),
                    notice.raw_source_name,
                    notice.summary,
                    datetime.now(UTC).isoformat(),
                ),
            )
            self._connection.commit()
        except sqlite3.DatabaseError as exc:
            raise StorageWriteError(
                f"SQLite notice save failed: {exc}",
                source=notice.source.value,
            ) from exc

    def list_all(self) -> tuple[Notice, ...]:
        """Return persisted notices in insertion order for export preparation."""

        rows = self._connection.execute(
            """
            SELECT *
            FROM notices
            ORDER BY id ASC
            """
        ).fetchall()
        return tuple(_notice_from_row(row) for row in rows)

    def all(self) -> tuple[Notice, ...]:
        return self.list_all()

    def count(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) AS count FROM notices").fetchone()
        return int(row["count"])

    def close(self) -> None:
        self._connection.close()

    def _ensure_parent_directory(self) -> None:
        if str(self.database_path) == ":memory:":
            return
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


def _dump_business_domains(values: tuple[BusinessDomain, ...]) -> str:
    return json.dumps([value.value for value in values], ensure_ascii=False)


def _dump_matched_keywords(values: tuple[MatchedKeyword, ...]) -> str:
    payload = [
        {
            "keyword": value.keyword,
            "group": value.group.value,
            "domain": value.domain.value if value.domain is not None else None,
        }
        for value in values
    ]
    return json.dumps(payload, ensure_ascii=False)


def _date_to_text(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _notice_from_row(row: sqlite3.Row) -> Notice:
    return Notice(
        source=NoticeSource(row["source"]),
        source_notice_id=row["source_notice_id"],
        notice_type=NoticeType(row["notice_type"]),
        business_domains=_load_business_domains(row["business_domains_json"]),
        primary_domain=BusinessDomain(row["primary_domain"]),
        title=row["title"],
        organization=row["organization"],
        posted_at=_date_from_text(row["posted_at"]),
        end_at=_date_from_text(row["end_at"]),
        status=NoticeStatus(row["status"]),
        url=row["url"],
        match_keywords=_load_matched_keywords(row["match_keywords_json"]),
        collected_at=datetime.fromisoformat(row["collected_at"]),
        raw_source_name=row["raw_source_name"],
        summary=row["summary"],
    )


def _load_business_domains(raw: str) -> tuple[BusinessDomain, ...]:
    values = json.loads(raw)
    return tuple(BusinessDomain(value) for value in values)


def _load_matched_keywords(raw: str) -> tuple[MatchedKeyword, ...]:
    values: list[dict[str, Any]] = json.loads(raw)
    return tuple(
        MatchedKeyword(
            keyword=value["keyword"],
            group=KeywordGroup(value["group"]),
            domain=BusinessDomain(value["domain"]) if value.get("domain") else None,
        )
        for value in values
    )


def _date_from_text(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None
