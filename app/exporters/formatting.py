"""Excel export formatting rules shared by fake and real exporters."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from app.domain import MatchedKeyword, Notice


EXPORT_COLUMN_ORDER = (
    "source",
    "notice_type",
    "primary_domain",
    "title",
    "organization",
    "posted_at",
    "end_at",
    "status",
    "url",
    "match_keywords",
    "collected_at",
)
DEFAULT_FILENAME_PATTERN = "notices_{run_date}_{run_id}.xlsx"


def format_notice_row(notice: Notice) -> dict[str, str]:
    """Format one Notice into the first-MVP Excel row representation."""

    return {
        "source": notice.source.value,
        "notice_type": notice.notice_type.value,
        "primary_domain": notice.primary_domain.value,
        "title": notice.title,
        "organization": notice.organization,
        "posted_at": _format_date(notice.posted_at),
        "end_at": _format_date(notice.end_at),
        "status": notice.status.value,
        "url": notice.url,
        "match_keywords": format_match_keywords(notice.match_keywords),
        "collected_at": _format_datetime_date(notice.collected_at),
    }


def format_sheet_rows(notices: tuple[Notice, ...]) -> tuple[dict[str, str], ...]:
    """Format sheet notices while preserving exporter column order."""

    return tuple(_ordered_row(format_notice_row(notice)) for notice in notices)


def format_match_keywords(values: tuple[MatchedKeyword, ...]) -> str:
    """Display matched keyword text only, de-duplicated in stored order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value.keyword in seen:
            continue
        seen.add(value.keyword)
        result.append(value.keyword)
    return ", ".join(result)


def build_export_filename(
    *,
    pattern: str,
    run_date: date,
    run_id: str,
) -> Path:
    """Build a safe first-MVP Excel filename from configured placeholders."""

    if "{run_date}" not in pattern and "{run_id}" not in pattern:
        raise ValueError("Export filename pattern must include run_date or run_id.")
    if not pattern.endswith(".xlsx"):
        raise ValueError("Export filename pattern must end with .xlsx.")
    filename = pattern.format(
        run_date=run_date.strftime("%Y%m%d"),
        run_id=run_id,
    )
    return Path(filename)


def _ordered_row(row: dict[str, str]) -> dict[str, str]:
    return {column: row[column] for column in EXPORT_COLUMN_ORDER}


def _format_date(value: date | None) -> str:
    return value.isoformat() if value is not None else ""


def _format_datetime_date(value: datetime) -> str:
    return value.date().isoformat()
